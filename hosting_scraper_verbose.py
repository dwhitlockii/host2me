import time
import re
import pandas as pd
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
from urllib.parse import urlparse
from tqdm import tqdm

HEADERS = {'User-Agent': UserAgent().random}

FIELDS = [
    "Rank", "Company Name", "Website URL", "Careers Page URL", "Remote Work Policy",
    "Tech Stack Relevance", "Application Status", "LinkedIn", "Twitter"
]

EXCLUDE_KEYWORDS = ["reseller", "affiliate", "GoDaddy", "EIG", "subsidiary", "part of", "owned by"]

def log(message):
    print(f"[LOG] {message}")

def search_hosting_companies():
    urls = []
    terms = ["US-based web hosting companies", "independent hosting providers USA"]
    for term in terms:
        query = f"https://www.bing.com/search?q={term.replace(' ', '+')}"
        log(f"Searching Bing with query: {term}")
        res = requests.get(query, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        found = 0
        for a in soup.select('li.b_algo h2 a'):
            href = a.get('href')
            if href and 'http' in href:
                urls.append(href)
                found += 1
        log(f"Found {found} links for query '{term}'")
        time.sleep(2)
    return list(set(urls))

def is_us_based(soup):
    text = soup.get_text().lower()
    return "united states" in text or "usa" in text

def has_disqualifiers(soup):
    text = soup.get_text().lower()
    return any(k in text for k in EXCLUDE_KEYWORDS)

def get_social_links(soup):
    links = {"LinkedIn": "", "Twitter": ""}
    for a in soup.find_all("a", href=True):
        href = a['href']
        if "linkedin.com/company" in href:
            links["LinkedIn"] = href
        elif "twitter.com" in href:
            links["Twitter"] = href
    return links

def detect_remote_policy(soup):
    text = soup.get_text().lower()
    if "fully remote" in text:
        return "Fully Remote"
    elif "hybrid" in text:
        return "Hybrid"
    elif "on-site" in text:
        return "On-Site"
    return "Unknown"

def detect_tech_stack(soup):
    tech_terms = ["linux", "terraform", "aws", "puppet", "grafana", "prometheus", "ci/cd", "devops"]
    text = soup.get_text().lower()
    hits = sum(1 for t in tech_terms if t in text)
    return "Yes" if hits > 5 else "Partial" if hits > 2 else "No"

def extract_company_info(url, rank=None):
    try:
        log(f"Fetching URL: {url}")
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        if not is_us_based(soup):
            log(f"Skipped (Not US-based): {url}")
            return None
        if has_disqualifiers(soup):
            log(f"Skipped (Disqualifiers matched): {url}")
            return None
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        name = parsed.netloc.replace("www.", "").split('.')[0].capitalize()
        careers_url = ""

        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if "career" in href or "jobs" in href:
                careers_url = href if "http" in href else base_url + href
                break

        social = get_social_links(soup)
        log(f"Extracted: {name} - {base_url}")

        return {
            "Rank": rank if rank else "",
            "Company Name": name,
            "Website URL": base_url,
            "Careers Page URL": careers_url,
            "Remote Work Policy": detect_remote_policy(soup),
            "Tech Stack Relevance": detect_tech_stack(soup),
            "Application Status": "",
            "LinkedIn": social["LinkedIn"],
            "Twitter": social["Twitter"]
        }
    except Exception as e:
        log(f"Error processing {url}: {e}")
        return None

def scrape_hosting_companies():
    results = []
    urls = search_hosting_companies()
    log(f"Total unique URLs collected: {len(urls)}")
    for i, url in enumerate(tqdm(urls[:50])):
        data = extract_company_info(url, rank=i+1)
        if data:
            results.append(data)
        time.sleep(1.5)
    if results:
        df = pd.DataFrame(results, columns=FIELDS)
        df.to_excel("output/us_hosting_companies.xlsx", index=False)
        log("Scraping complete. Data written to output/us_hosting_companies.xlsx")
    else:
        log("No valid data was scraped.")
