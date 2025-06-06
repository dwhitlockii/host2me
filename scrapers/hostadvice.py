import os
import requests
from bs4 import BeautifulSoup
from utils.browser import get_driver, wait_for

BASE_URL = "https://hostadvice.com/hosting-services/"


def save_debug_html(page: int, html: str):
    os.makedirs('output', exist_ok=True)
    path = f"output/hostadvice_debug_page{page}.html"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)


def fetch_page_requests(session: requests.Session, page: int, proxy: str | None = None):
    url = f"{BASE_URL}?page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": BASE_URL,
    }
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    resp = session.get(url, headers=headers, timeout=10)
    return resp


def fetch_page_selenium(page: int, proxy: str | None = None):
    url = f"{BASE_URL}?page={page}"
    driver = get_driver(proxy)
    try:
        driver.get(url)
        wait_for(driver, ".company-card,.company-list-card,.listing__card")
        html = driver.page_source
        save_debug_html(page, html)
        return html
    finally:
        driver.quit()


def parse_companies(html: str):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(".company-card") or soup.select(".company-list-card") or soup.select(".listing__card")
    companies = []
    for card in cards:
        name_el = card.select_one(".company-name")
        url_el = card.select_one(".company-name a")
        if not url_el:
            continue
        url = url_el["href"]
        if url.startswith("/"):
            url = "https://hostadvice.com" + url
        domain = url.split("/")[2]
        companies.append({
            "name": name_el.get_text(strip=True) if name_el else domain.split('.')[0],
            "domain": domain,
            "url": url,
        })
    return companies


def fetch_all_pages(max_pages: int = 10, proxy: str | None = None, log=None):
    session = requests.Session()
    all_companies = {}
    page = 1
    while True:
        if max_pages and page > max_pages:
            break
        resp = fetch_page_requests(session, page, proxy)
        if resp.status_code == 403:
            if log:
                log(f"[HostAdvice] 403 on page {page}. Using Selenium")
            html = fetch_page_selenium(page, proxy)
        elif resp.status_code != 200:
            if log:
                log(f"[HostAdvice] Failed {page} status {resp.status_code}")
            break
        else:
            html = resp.text
            save_debug_html(page, html)
        companies = parse_companies(html)
        if log:
            log(f"[HostAdvice] Parsed {len(companies)} companies on page {page}")
        new = 0
        for c in companies:
            if c['domain'] not in all_companies:
                all_companies[c['domain']] = c
                new += 1
        if log:
            log(f"[HostAdvice] Added {new} new companies")
        if not companies:
            break
        page += 1
    return list(all_companies.values())
