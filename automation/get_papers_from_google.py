import time
import pickle
import requests
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlencode

import time
import pickle
import requests
import os
import re
import random
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlencode

# === CONFIG ===
API_KEY = "fbb15dc82c0f4f0fd1d943c96104c114"
SITE_KEY = "6LfFDwUTAAAAAIyC8IeC3aGLqVpvrB6ZpkfmAibj"
BASE_URL = "https://scholar.google.com/scholar"
COOKIE_FILE = "scholar_cookies.pkl"

# === FASTCAPTCHA ===
# === 2CAPTCHA (createTask/getTaskResult) ===
def solve_fastcaptcha_dataportal(web_url, site_key, api_key, driver,is_invisible=False, timeout=180, poll_interval=5):
    """
    Replaced to use 2Captcha's JSON API:
      - POST https://api.2captcha.com/createTask
      - POST https://api.2captcha.com/getTaskResult
    Returns the gRecaptchaResponse token.
    """
    create_url = "http://api.2captcha.com/createTask"
    result_url = "http://api.2captcha.com/getTaskResult"


    cookies = driver.get_cookies()
    cookies_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    task_payload = {
        "clientKey": api_key,
        "task": {
            "type": "RecaptchaV2TaskProxyless",
            "websiteURL": web_url,
            "websiteKey": site_key,
            "isInvisible": bool(is_invisible),
            "cookies": cookies_str 
          
        }
    }
    print(task_payload)
    # Create task
    print("🧠 Requesting CAPTCHA solution from 2Captcha (createTask)...")
    create_resp = requests.post(create_url, json=task_payload, headers={"Content-Type": "application/json"})
    print(create_resp)
    if create_resp.status_code != 200:
        raise Exception(f"❌ 2Captcha createTask HTTP error: {create_resp.status_code} - {create_resp.text}")

    create_json = create_resp.json()
    if create_json.get("errorId") != 0:
        raise Exception(f"❌ 2Captcha createTask error: {create_json}")

    task_id = create_json.get("taskId")
    if not task_id:
        raise Exception(f"❌ 2Captcha createTask missing taskId: {create_json}")

    # Poll for result
    started = time.time()
    while True:
        if time.time() - started > timeout:
            raise TimeoutError("⌛ 2Captcha timeout waiting for solution.")

        time.sleep(poll_interval)
        check_payload = {
            "clientKey": api_key,
            "taskId": task_id
        }
        check_resp = requests.post(result_url, json=check_payload, headers={"Content-Type": "application/json"})
        print(check_resp.json())
        if check_resp.status_code != 200:
            raise Exception(f"❌ 2Captcha getTaskResult HTTP error: {check_resp.status_code} - {check_resp.text}")

        check_json = check_resp.json()
        if check_json.get("errorId") != 0:
            raise Exception(f"❌ 2Captcha getTaskResult error: {check_json}")

        status = check_json.get("status")
        if status == "processing":
            continue

        if status == "ready":
            time.sleep(10)
            solution = check_json.get("solution", {})
            token = solution.get("gRecaptchaResponse")
            if not token:
                raise Exception(f"❌ 2Captcha ready but no gRecaptchaResponse: {check_json}")
            print("✅ CAPTCHA solved via 2Captcha.")
            return token

        # Unexpected status
        raise Exception(f"❌ 2Captcha unknown status: {check_json}")



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
    """Inject CAPTCHA token and handle the redirect properly"""
 
    # Build the URL with CAPTCHA response parameter
    current_url = driver.current_url
    url_parts = current_url.split('?')
    base_url = url_parts[0] if '?' in current_url else current_url
    query_params = dict(pair.split('=') for pair in url_parts[1].split('&')) if '?' in current_url else {}
    
    # Add/update the g-recaptcha-response parameter
    query_params['g-recaptcha-response'] = token
    
    # Rebuild the URL with CAPTCHA response
    captcha_url = base_url + '?' + '&'.join([f"{k}={v}" for k, v in query_params.items()])
    
    print(f"🔗 Navigating to CAPTCHA verification URL: {captcha_url}")
    driver.get(captcha_url)
    
    # Wait for redirect and save cookies
    time.sleep(3)
    save_cookies(driver)
    print("🍪 Cookies saved after CAPTCHA verification")
    
    return True


def is_captcha_present(driver):
    print("checking if captcha required ", driver.page_source.lower())
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
    print("inside ppr scraping ")
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
            print("🍪 No cookies found, starting fresh.")

            driver.get(url)
        time.sleep(3)
        print("checking if captcha required ")
        if is_captcha_present(driver):
            print("🛑 CAPTCHA detected. Solving...")
            token = solve_fastcaptcha_dataportal(driver.current_url, SITE_KEY, API_KEY,driver)
            inject_token(driver, token)
            # driver.get(url)
            # time.sleep(5)
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
                    print("✅ Article added:", title)

            except Exception as e:
                print("⚠️ Skipping article due to error:", e)


    driver.quit()
    return results