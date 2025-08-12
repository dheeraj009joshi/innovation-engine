import time
import pickle
import requests
import os
import re
import random
from urllib.parse import urlencode, urlparse, parse_qs
from bs4 import BeautifulSoup

# === CONFIG ===
API_KEY = "fbb15dc82c0f4f0fd1d943c96104c114"
SITE_KEY = "6LfFDwUTAAAAAIyC8IeC3aGLqVpvrB6ZpkfmAibj"
BASE_URL = "https://scholar.google.com/scholar"
COOKIE_FILE = "scholar_cookies.pkl"

# User-Agent rotation list
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
]

def get_random_headers():
    """Get random headers for requests"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

# === 2CAPTCHA SOLUTION ===
def solve_fastcaptcha_dataportal(web_url, site_key, api_key, session, is_invisible=False, timeout=180, poll_interval=5):
    """
    Solve CAPTCHA using 2Captcha API with requests session
    """
    create_url = "https://api.2captcha.com/createTask"
    result_url = "https://api.2captcha.com/getTaskResult"

    # Get cookies from session
    cookies_str = "; ".join([f"{name}={value}" for name, value in session.cookies.items()])
    
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
    print(f"🧠 CAPTCHA task payload: {task_payload}")

    # Create task
    print("🧠 Requesting CAPTCHA solution from 2Captcha (createTask)...")
    create_resp = requests.post(create_url, json=task_payload, headers={"Content-Type": "application/json"})
    
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
        print(f"🔍 Checking task status: {check_resp.json()}")
        
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

# === UTILITY FUNCTIONS ===
def build_scholar_url(query, start=0, start_year=None, end_year=None):
    """Build Google Scholar URL with parameters"""
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

def is_captcha_present(html_content):
    """Check if CAPTCHA is present in the HTML content"""
    return "recaptcha" in html_content.lower() or "are you a robot" in html_content.lower()

def save_cookies(session, path=COOKIE_FILE):
    """Save session cookies to file"""
    with open(path, "wb") as file:
        pickle.dump(dict(session.cookies), file)
        print("🍪 Cookies saved.")

def load_cookies(session, path=COOKIE_FILE):
    """Load cookies from file into session"""
    if not os.path.exists(path):
        return
    
    try:
        with open(path, "rb") as file:
            cookies = pickle.load(file)
            for name, value in cookies.items():
                session.cookies.set(name, value, domain='.google.com')
        print("🍪 Cookies loaded.")
    except Exception as e:
        print(f"⚠️ Error loading cookies: {e}")

def handle_captcha_verification(session, current_url, token):
    """Handle CAPTCHA verification by making request with token"""
    # Parse current URL and add CAPTCHA response parameter
    parsed_url = urlparse(current_url)
    query_params = parse_qs(parsed_url.query)
    
    # Flatten query params (parse_qs returns lists)
    flat_params = {k: v[0] if isinstance(v, list) and v else v for k, v in query_params.items()}
    flat_params['g-recaptcha-response'] = token
    
    # Rebuild URL with CAPTCHA response
    captcha_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?" + urlencode(flat_params)
    
    print(f"🔗 Making CAPTCHA verification request to: {captcha_url}")
    
    # Make request with CAPTCHA token
    headers = get_random_headers()
    response = session.get(captcha_url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        save_cookies(session)
        print("🍪 Cookies saved after CAPTCHA verification")
        return response
    else:
        raise Exception(f"❌ CAPTCHA verification failed: {response.status_code}")

def parse_scholar_results(html_content):
    """Parse Google Scholar results from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # Find all article containers
    articles = soup.find_all('div', class_=['gs_r', 'gs_or', 'gs_scl']) or soup.find_all('div', {'data-lid': True})
    
    for article in articles:
        try:
            # Extract title
            title_tag = article.find('h3', class_='gs_rt') or article.find('a')
            if not title_tag:
                continue
            title = title_tag.get_text().strip()
            
            # Extract PDF link
            pdf_link = None
            pdf_tags = article.find_all('a', href=True)
            for pdf_tag in pdf_tags:
                href = pdf_tag.get('href', '')
                if href.lower().endswith('.pdf') or 'pdf' in pdf_tag.get_text().lower():
                    pdf_link = href
                    break
            
            # Extract author info
            author_tag = article.find('div', class_='gs_a')
            author_info = author_tag.get_text().strip() if author_tag else ""
            
            # Extract year using regex
            year_match = re.search(r'\b(19|20)\d{2}\b', author_info)
            year = year_match.group(0) if year_match else None
            
            # Extract cited by information
            cited_by = None
            cited_links = article.find_all('a', href=True)
            for a in cited_links:
                text = a.get_text().lower()
                if "cited by" in text:
                    cited_by = re.sub(r'[^\d]', '', a.get_text())
                    break
            
            # Only keep if it's a PDF link
            if pdf_link and pdf_link.lower().endswith(".pdf"):
                results.append({
                    "title": title,
                    "pdf_link": pdf_link,
                    "author_info": author_info,
                    "year": year,
                    "cited_by": cited_by
                })
                print("✅ Article added:", title)
                
        except Exception as e:
            print(f"⚠️ Error parsing article: {e}")
            continue
    
    return results

def get_random_proxy():
    """Get random proxy (kept from original code)"""
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://list.didsoft.com/get?email=tikuntechnologies@gmail.com&pass=bwnh68&pid=http1000&showcountry=no&level=1&country=US")
        data = resp.read().decode('utf-8').strip()
        urls = data.split("\n")
        return random.choice(urls) 
    except Exception as e:
        print(f"⚠️ Error getting proxy: {e}")
        return None

# === MAIN SCRAPER ===
def scrape_scholar_pages(query, start_year, end_year):
    """Main scraping function using requests"""
    print("🔍 Starting Google Scholar scraping with requests...")
    
    # Create session for persistent cookies
    session = requests.Session()
    
    # Configure session with retry strategy
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Load existing cookies if available
    load_cookies(session)
    
    all_results = []
    
    for start in [0, 10, 20]:  # Scrape 3 pages
        try:
            url = build_scholar_url(query, start, start_year, end_year)
            print(f"\n🌐 Making request to: {url}")
            
            # Random delay between requests
            time.sleep(random.uniform(2, 5))
            
            # Make request with random headers
            headers = get_random_headers()
            response = session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ HTTP Error {response.status_code}: {response.text[:500]}")
                continue
            
            # Check for CAPTCHA
            if is_captcha_present(response.text):
                print("🛑 CAPTCHA detected. Solving...")
                try:
                    token = solve_fastcaptcha_dataportal(url, SITE_KEY, API_KEY, session)
                    response = handle_captcha_verification(session, url, token)
                except Exception as captcha_error:
                    print(f"❌ CAPTCHA solving failed: {captcha_error}")
                    continue
            
            # Parse results
            page_results = parse_scholar_results(response.text)
            all_results.extend(page_results)
            
            print(f"📄 Page {start//10 + 1}: Found {len(page_results)} PDF articles")
            
        except requests.RequestException as e:
            print(f"❌ Request error for start={start}: {e}")
            continue
        except Exception as e:
            print(f"❌ General error for start={start}: {e}")
            continue
    
    print(f"\n🎉 Scraping complete! Total PDF articles found: {len(all_results)}")
    return all_results

