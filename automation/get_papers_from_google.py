import time
import pickle
import requests
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlencode

# === CONFIG ===
API_KEY = "2ae8c54d-eb02-4138-b0de-f710e26a3448"
SITE_KEY = "6LeT6HkUAAAAAN2NOfsbHyGX5Yx8Nn6PpY0zpz2e"
BASE_URL = "https://scholar.google.com/scholar"
COOKIE_FILE = "scholar_cookies.pkl"

# === FASTCAPTCHA ===
def solve_fastcaptcha_dataportal(web_url, site_key, api_key):
    url = "https://thedataextractors.com/fast-captcha/api/solve/recaptcha"

    payload = f"webUrl={web_url}&websiteKey={site_key}"
    headers = {
        'apiSecretKey': api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    print("🧠 Requesting CAPTCHA solution from FastCaptcha...")
    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        raise Exception(f"❌ FastCaptcha API error: {response.status_code} - {response.text}")

    result = response.json()
    if not result.get("success"):
        raise Exception(f"❌ CAPTCHA solving failed: {result}")

    print("✅ CAPTCHA solved successfully.")
    return result["captchaSolve"]  # This is your


# === UTILS ===
def build_scholar_url(query, start=0, start_year=None, end_year=None):
    params = {
        'q': query,
        'hl': 'en',
        'start': start,
        'as_sdt': '0,50',
        'as_rr': 1
    }
    if start_year:
        params['as_ylo'] = start_year
    if end_year:
        params['as_yhi'] = end_year
    return BASE_URL + '?' + urlencode(params)

def inject_token(driver, token):
    driver.execute_script("""
        const textarea = document.createElement('textarea');
        textarea.id = 'g-recaptcha-response';
        textarea.name = 'g-recaptcha-response';
        textarea.style = 'display: block;';
        textarea.value = arguments[0];
        document.body.appendChild(textarea);
    """, token)
    time.sleep(2)
    driver.execute_script("document.getElementById('g-recaptcha-response').dispatchEvent(new Event('change'));")
    time.sleep(5)
    print("✅ CAPTCHA token injected.")

def is_captcha_present(driver):
    return "recaptcha" in driver.page_source.lower() or "are you a robot" in driver.page_source.lower()

def save_cookies(driver, path=COOKIE_FILE):
    with open(path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
        print("🍪 Cookies saved.")

def load_cookies(driver, url, path=COOKIE_FILE):
    if not os.path.exists(path):
        return
    driver.get(url)
    with open(path, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
    print("🍪 Cookies loaded.")
    driver.get(url)

# === MAIN SCRAPER ===
def scrape_scholar_pages(query, start_year, end_year):
    options = Options()
    options.add_argument("--headless")              # <- enables headless mode
    options.add_argument("--disable-gpu")           # <- required for some systems
    options.add_argument("--window-size=1920,1080") # <- set screen size to avoid layout issues
    options.add_argument("--no-sandbox")            # <- optional, useful in some environments
    options.add_argument("--disable-dev-shm-usage") # <- optional for Docker or limited systems

    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    results = []
    for start in [0, 10,20]:  # Scrape 2 pages
        url = build_scholar_url(query, start, start_year, end_year)
        print(f"\n🌐 Visiting: {url}")

        # Load cookies if available
        if os.path.exists(COOKIE_FILE):
            driver.get("https://scholar.google.com")
            load_cookies(driver, url)
        else:
            driver.get(url)
        time.sleep(3)

        if is_captcha_present(driver):
            print("🛑 CAPTCHA detected. Solving...")
            token = solve_fastcaptcha_dataportal(driver.current_url, SITE_KEY, API_KEY)
            inject_token(driver, token)
            driver.get(url)
            time.sleep(5)
            save_cookies(driver)  # Save cookies after solving

        articles = driver.find_elements(By.CSS_SELECTOR, '.gs_r.gs_or.gs_scl')
        for article in articles:
            try:
                title_tag = article.find_element(By.CSS_SELECTOR, '.gs_rt')
                title = title_tag.text.strip()
                
                # Optional PDF link (on the right side)
                pdf_link = None
                try:
                    pdf_tag = article.find_element(By.CSS_SELECTOR, '.gs_or_ggsm a')
                    pdf_link = pdf_tag.get_attribute("href")
                except:
                    pass

                # Author info
                author_tag = article.find_element(By.CLASS_NAME, 'gs_a')
                author_info = author_tag.text.strip()

                # Extract year using regex
                year_match = re.search(r'\b(19|20)\d{2}\b', author_info)
                year = year_match.group(0) if year_match else None

                # Cited by
                cited_by = None
                cited_links = article.find_elements(By.CSS_SELECTOR, '.gs_fl a')
                for a in cited_links:
                    if a.text.lower().startswith("cited by"):
                        cited_by = a.text.strip()
                        break

                # Only keep if it's a PDF link
                if pdf_link and pdf_link.lower().endswith(".pdf"):
                    results.append({
                        "title": title,
                        "pdf_link": pdf_link,
                        "author_info": author_info,
                        "year": year,
                        "cited_by": cited_by.replace("Cited by", "").strip() if cited_by else None
                    })

            except Exception as e:
                print("⚠️ Skipping article due to error:", e)


    driver.quit()
    return results

# results = scrape_scholar_pages("sleep filetype:pdf", 2010, 2015)
# print(results)
# print(len(results), "results found.")