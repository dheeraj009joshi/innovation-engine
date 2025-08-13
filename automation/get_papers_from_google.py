import time
import pickle
import requests
import os
import re
import random
import urllib.request
from urllib.parse import urlencode, urlparse, parse_qs
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# === CONFIGURATION ===
API_KEY = "fbb15dc82c0f4f0fd1d943c96104c114"  # 2Captcha API key
SITE_KEY = "6LfFDwUTAAAAAIyC8IeC3aGLqVpvrB6ZpkfmAibj"  # Google reCAPTCHA site key
BASE_URL = "https://scholar.google.com/scholar"
COOKIE_FILE = "scholar_cookies.pkl"

# Proxy configuration
PROXY_USERNAME = "tikuntechnologies.gmail.com"
PROXY_PASSWORD = "bwnh68"
PROXY_HOST = "69.30.227.194"
PROXY_PORT = "2000"

# User-Agent rotation list
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0'
]

# Referer options for Google Scholar
REFERERS = [
    'https://www.google.com/',
    'https://scholar.google.com/',
    'https://www.google.com/search?q=google+scholar',
    'https://en.wikipedia.org/',
    'https://www.researchgate.net/'
]


class ProxyManager:
    """Manage proxy rotation and failure tracking"""
    
    def __init__(self):
        self.proxies = []
        self.failed_proxies = set()
        self.current_index = 0
    
    def load_proxies_from_service(self):
        """Load proxies from external service"""
        try:
            resp = urllib.request.urlopen(
                "http://list.didsoft.com/get?email=tikuntechnologies@gmail.com&pass=bwnh68&pid=http1000&showcountry=no&level=1&country=US"
            )
            data = resp.read().decode('utf-8').strip()
            self.proxies = data.split("\n")
            print(f"📡 Loaded {len(self.proxies)} proxies from service")
            return True
        except Exception as e:
            print(f"⚠️ Error loading proxies: {e}")
            return False
    
    def get_next_proxy(self):
        """Get next available proxy"""
        if not self.proxies:
            return None
            
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_index % len(self.proxies)]
            self.current_index += 1
            
            if proxy not in self.failed_proxies:
                return proxy
            
            attempts += 1
        
        return None
    
    def mark_proxy_failed(self, proxy):
        """Mark a proxy as failed"""
        self.failed_proxies.add(proxy)
        print(f"❌ Marked proxy as failed: {proxy}")


def get_random_headers():
    """Generate random headers for requests with better anti-detection"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin' if random.random() > 0.5 else 'cross-site',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': f'"{random.choice(["Windows", "macOS", "Linux"])}"',
        'Cache-Control': 'max-age=0',
        'Referer': random.choice(REFERERS)
    }


def solve_captcha_2captcha(web_url, site_key, api_key, session, is_invisible=False, timeout=180, poll_interval=5):
    """
    Solve CAPTCHA using 2Captcha API with requests session
    """
    create_url = "http://api.2captcha.com/createTask"
    result_url = "http://api.2captcha.com/getTaskResult"

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
    captcha_indicators = ["recaptcha", "are you a robot", "captcha", "g-recaptcha"]
    content_lower = html_content.lower()
    return any(indicator in content_lower for indicator in captcha_indicators)


def save_cookies(session, path=COOKIE_FILE):
    """Save session cookies to file"""
    try:
        with open(path, "wb") as file:
            pickle.dump(dict(session.cookies), file)
            print("🍪 Cookies saved.")
    except Exception as e:
        print(f"⚠️ Error saving cookies: {e}")


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
                
            # Clean title text
            title_link = title_tag.find('a') if title_tag.name != 'a' else title_tag
            title = title_link.get_text().strip() if title_link else title_tag.get_text().strip()
            
            # Extract PDF link
            pdf_link = None
            pdf_tags = article.find_all('a', href=True)
            for pdf_tag in pdf_tags:
                href = pdf_tag.get('href', '')
                text = pdf_tag.get_text().lower()
                if href.lower().endswith('.pdf') or 'pdf' in text:
                    pdf_link = href if href.startswith('http') else f"https://scholar.google.com{href}"
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
                    cited_match = re.search(r'\d+', a.get_text())
                    cited_by = cited_match.group(0) if cited_match else None
                    break
            
            # Only keep if it's a PDF link or if we found PDF text
            if pdf_link:
                results.append({
                    "title": title,
                    "pdf_link": pdf_link,
                    "author_info": author_info,
                    "year": year,
                    "cited_by": cited_by
                })
                print(f"✅ Article added: {title[:60]}...")
                
        except Exception as e:
            print(f"⚠️ Error parsing article: {e}")
            continue
    
    return results


def make_initial_request(session):
    """Make an initial request to Google Scholar homepage to establish session"""
    try:
        print("🏠 Making initial request to Google Scholar homepage...")
        headers = get_random_headers()
        headers['Referer'] = 'https://www.google.com/'
        
        # Visit Google first
        google_resp = session.get('https://www.google.com/', headers=headers, timeout=10)
        time.sleep(random.uniform(1, 3))
        
        # Then visit Scholar homepage
        scholar_resp = session.get('https://scholar.google.com/', headers=headers, timeout=10)
        
        if scholar_resp.status_code == 200:
            print("✅ Successfully established session with Google Scholar")
            save_cookies(session)
            return True
        else:
            print(f"⚠️ Scholar homepage returned: {scholar_resp.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️ Error establishing session: {e}")
        return False


def handle_403_error(session, url, attempt=1, max_attempts=3):
    """Handle 403 errors with progressive backoff and session reset"""
    if attempt > max_attempts:
        return None
        
    print(f"🛑 403 Error - Attempt {attempt}/{max_attempts}")
    
    # Progressive delays
    delay = random.uniform(5 * attempt, 15 * attempt)
    print(f"⏳ Waiting {delay:.1f} seconds...")
    time.sleep(delay)
    
    # Reset session on subsequent attempts
    if attempt > 1:
        session.cookies.clear()
        if not make_initial_request(session):
            return None
    
    # Try with different approach
    try:
        headers = get_random_headers()
        
        # Add some randomization to headers
        if random.random() > 0.7:
            headers.pop('DNT', None)
        if random.random() > 0.8:
            headers.pop('Upgrade-Insecure-Requests', None)
            
        response = session.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Successfully recovered from 403 error")
            return response
        elif response.status_code == 403:
            return handle_403_error(session, url, attempt + 1, max_attempts)
        else:
            print(f"❌ Got status code {response.status_code} on retry")
            return None
            
    except Exception as e:
        print(f"❌ Error on retry attempt {attempt}: {e}")
        if attempt < max_attempts:
            return handle_403_error(session, url, attempt + 1, max_attempts)
        return None


def setup_authenticated_proxy(session):
    """Setup authenticated proxy for session"""
    proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    proxy_dict = {
        'http': proxy_url,
        'https': proxy_url
    }
    session.proxies.update(proxy_dict)
    print(f"🔧 Configured authenticated proxy: {PROXY_HOST}:{PROXY_PORT}")
    return True


def make_request_with_authenticated_proxy(session, url, max_attempts=3):
    """Make request with authenticated proxy"""
    
    for attempt in range(max_attempts):
        print(f"🔄 Attempt {attempt + 1}/{max_attempts} using authenticated proxy")
        
        try:
            headers = get_random_headers()
            response = session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("✅ Success with authenticated proxy")
                return response
            elif response.status_code == 403:
                print(f"🛑 403 error with proxy, attempt {attempt + 1}")
                if attempt < max_attempts - 1:
                    time.sleep(random.uniform(10, 20))
            elif response.status_code == 429:
                print(f"⏳ Rate limited, waiting before retry...")
                time.sleep(random.uniform(15, 30))
            else:
                print(f"⚠️ Unexpected status {response.status_code}")
                
        except requests.exceptions.ProxyError as e:
            print(f"🚫 Proxy connection error: {e}")
            if attempt < max_attempts - 1:
                time.sleep(random.uniform(5, 10))
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout with authenticated proxy")
            if attempt < max_attempts - 1:
                time.sleep(random.uniform(5, 10))
        except Exception as e:
            print(f"❌ Error with authenticated proxy: {e}")
            
        # Random delay between attempts
        if attempt < max_attempts - 1:
            time.sleep(random.uniform(3, 8))
    
    print(f"❌ All {max_attempts} attempts failed with authenticated proxy")
    return None


def make_request_with_proxy_rotation(session, url, proxy_manager, max_attempts=3):
    """Make request with automatic proxy rotation on failure"""
    
    for attempt in range(max_attempts):
        current_proxy = proxy_manager.get_next_proxy()
        
        if not current_proxy:
            print("❌ No working proxies available")
            return None
            
        proxy_dict = {
            'http': f'http://{current_proxy}',
            'https': f'http://{current_proxy}'
        }
        
        print(f"🔄 Attempt {attempt + 1}/{max_attempts} using proxy: {current_proxy}")
        
        try:
            session.proxies = proxy_dict
            headers = get_random_headers()
            
            response = session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Success with proxy: {current_proxy}")
                return response
            elif response.status_code == 403:
                print(f"🛑 403 error with proxy {current_proxy}, trying next...")
                proxy_manager.mark_proxy_failed(current_proxy)
            elif response.status_code == 429:
                print(f"⏳ Rate limited with proxy {current_proxy}, trying next...")
                time.sleep(random.uniform(5, 10))
            else:
                print(f"⚠️ Unexpected status {response.status_code} with proxy {current_proxy}")
                
        except requests.exceptions.ProxyError:
            print(f"🚫 Proxy connection error: {current_proxy}")
            proxy_manager.mark_proxy_failed(current_proxy)
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout with proxy: {current_proxy}")
            proxy_manager.mark_proxy_failed(current_proxy)
        except Exception as e:
            print(f"❌ Error with proxy {current_proxy}: {e}")
            
        # Random delay between attempts
        time.sleep(random.uniform(2, 5))
    
    print(f"❌ All {max_attempts} attempts failed")
    return None


def scrape_scholar_pages(query, start_year, end_year, use_authenticated_proxy=True, max_pages=3):
    """
    Main scraping function using requests
    
    Args:
        query (str): Search query
        start_year (int): Start year filter
        end_year (int): End year filter
        use_authenticated_proxy (bool): Whether to use authenticated proxy first
        max_pages (int): Maximum number of pages to scrape
    
    Returns:
        list: List of dictionaries containing article information
    """
    print("🔍 Starting Google Scholar scraping with requests...")
    
    # Create session for persistent cookies
    session = requests.Session()
    
    # Configure session with retry strategy
    retry_strategy = Retry(
        total=2,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Load existing cookies if available
    load_cookies(session)
    
    # Setup proxy if requested
    proxy_manager = None
    if use_authenticated_proxy:
        setup_authenticated_proxy(session)
    else:
        proxy_manager = ProxyManager()
        if not proxy_manager.load_proxies_from_service():
            print("⚠️ Failed to load proxy list, proceeding without proxies...")
    
    # Establish initial session
    if not make_initial_request(session):
        print("⚠️ Failed to establish initial session, proceeding anyway...")
    
    all_results = []
    
    for page in range(max_pages):
        start = page * 10
        try:
            url = build_scholar_url(query, start, start_year, end_year)
            print(f"\n🌐 Making request to page {page + 1}: {url}")
            
            # Longer random delay between requests
            delay = random.uniform(5, 12)
            print(f"⏳ Waiting {delay:.1f} seconds before request...")
            time.sleep(delay)
            
            # Make request based on proxy configuration
            response = None
            if use_authenticated_proxy:
                response = make_request_with_authenticated_proxy(session, url)
                # Fallback to proxy rotation if authenticated proxy fails
                if not response and proxy_manager:
                    print("🔄 Falling back to proxy rotation...")
                    response = make_request_with_proxy_rotation(session, url, proxy_manager)
            else:
                if proxy_manager:
                    response = make_request_with_proxy_rotation(session, url, proxy_manager)
                else:
                    # Direct request without proxy
                    headers = get_random_headers()
                    response = session.get(url, headers=headers, timeout=30)
            
            # Handle response
            if not response:
                print(f"❌ Failed to get response for page {page + 1}")
                continue
                
            if response.status_code == 403:
                print("🛑 Got 403 error, attempting recovery...")
                response = handle_403_error(session, url)
                if not response:
                    print(f"❌ Failed to recover from 403 error for page {page + 1}")
                    continue
                    
            elif response.status_code == 429:
                print("🛑 Rate limited (429), waiting longer...")
                time.sleep(random.uniform(30, 60))
                continue
                
            elif response.status_code != 200:
                print(f"❌ HTTP Error {response.status_code}: {response.text[:500]}")
                continue
            
            # Check for CAPTCHA
            if is_captcha_present(response.text):
                print("🛑 CAPTCHA detected. Solving...")
                try:
                    token = solve_captcha_2captcha(url, SITE_KEY, API_KEY, session)
                    response = handle_captcha_verification(session, url, token)
                except Exception as captcha_error:
                    print(f"❌ CAPTCHA solving failed: {captcha_error}")
                    continue
            
            # Parse results
            page_results = parse_scholar_results(response.text)
            all_results.extend(page_results)
            
            print(f"📄 Page {page + 1}: Found {len(page_results)} PDF articles")
            
        except requests.RequestException as e:
            print(f"❌ Request error for page {page + 1}: {e}")
            continue
        except Exception as e:
            print(f"❌ General error for page {page + 1}: {e}")
            continue
    
    print(f"\n🎉 Scraping complete! Total PDF articles found: {len(all_results)}")
    return all_results

