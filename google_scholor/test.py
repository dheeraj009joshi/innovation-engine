import random
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time

import urllib
from config import QUERY, START, headers,END,endYear, startYear,user_agent_list,search_url, search_url2, search_url3

def get_urls():
    urls=[]

    resp = urllib.request.urlopen(urllib.request.Request(url=search_url, data=None))
    data = resp.read().decode('utf-8').split('/*""*/')[0]
    for i in data.split("\n"):
        urls.append(i)
    resp = urllib.request.urlopen(urllib.request.Request(url=search_url2, data=None))
    data = resp.read().decode('utf-8').split('/*""*/')[0]
    for i in data.split("\n"):
        urls.append(i)
    resp = urllib.request.urlopen(urllib.request.Request(url=search_url3, data=None))
    data = resp.read().decode('utf-8').split('/*""*/')[0]
    for i in data.split("\n"):
        urls.append(i)
    
    return urls



import ssl
import random
import urllib.request
from bs4 import BeautifulSoup
import re
from urllib.parse import urlencode

def fetch_scholar_results(query, start=START, end=END):
    results = []
    base_url = "https://scholar.google.com/scholar"

    def get_random_proxy():
        return random.choice(get_urls())

    def get_random_headers():
        return {
            'User-Agent': random.choice(user_agent_list),
        }

    context = ssl.create_default_context()

    for i in range(start, end, 10):
        params = {
            'q': query,
            'hl': 'en',
            'start': i,
            'as_sdt': '0,50',
            'as_ylo': startYear,
            'as_yhi': endYear,
            'as_rr': 1
        }

        url = f"{base_url}?{urlencode(params)}"
        proxy = get_random_proxy()
        headers = get_random_headers()

        try:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)

            req = urllib.request.Request(url=url, headers=headers)
            response = urllib.request.urlopen(req, context=context)

            html = response.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

            for result in soup.select('.gs_r.gs_or.gs_scl'):
                title_tag = result.select_one('.gs_rt')
                pdf_link_tag = result.select_one('.gs_or_ggsm a')
                author_tag = result.select_one('.gs_a')
                cited_by = None

                title = title_tag.get_text(strip=True) if title_tag else "No title"
                pdf_link = pdf_link_tag['href'] if pdf_link_tag else None
                author_info = author_tag.get_text(strip=True) if author_tag else "No author info"

                year_match = re.search(r'\b(19|20)\d{2}\b', author_info)
                year = year_match.group(0) if year_match else None

                for a_tag in result.select('.gs_fl a'):
                    if a_tag.text.startswith("Cited by"):
                        cited_by = a_tag.text
                        break

                if pdf_link and pdf_link.lower().endswith('.pdf'):
                    results.append({
                        'title': title,
                        'pdf_link': pdf_link,
                        'author_info': author_info,
                        'year': year,
                        'cited_by': cited_by
                    })

            print(f"✅ Success at start={i}, total results: {len(results)}")
            for paper in results:
                print(f"Title: {paper['title']}, PDF Link: {paper['pdf_link']}, Author Info: {paper['author_info']}, Year: {paper['year']}, Cited By: {paper['cited_by']}")
                
        except Exception as e:
            print(f"⚠️ Proxy Failed at start={i} using {proxy} → {e}")
            continue

    return results




papers = fetch_scholar_results(QUERY, START)
print(f"Total papers fetched: {len(papers)}")
for paper in papers:
    print(f"Title: {paper['title']}, PDF Link: {paper['pdf_link']}, Author Info: {paper['author_info']}, Year: {paper['year']}, Cited By: {paper['cited_by']}")