import os
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.whtop.com/directory/country/us"


def save_debug_html(page: int, html: str):
    os.makedirs('output', exist_ok=True)
    path = f"output/whtop_debug_page{page}.html"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)


def fetch_page(session: requests.Session, page: int, proxy: str | None = None):
    url = BASE_URL if page == 1 else f"{BASE_URL}/page/{page}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36",
        "Referer": BASE_URL,
        "Accept-Language": "en-US,en;q=0.9",
    }
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    resp = session.get(url, headers=headers, timeout=10)
    return resp


def parse_companies(html: str):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.table.alt")
    if not table:
        return []
    companies = []
    rows = table.find_all("tr", class_=["s_alt_row1", "s_alt_row2"])
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 7:
            continue
        domain_cell = tds[6].get_text(strip=True)
        match = re.search(r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", domain_cell)
        if not match:
            continue
        domain = match.group(0)
        companies.append({
            "name": domain.split(".")[0].capitalize(),
            "domain": domain,
            "url": f"https://{domain}",
            "plan_name": tds[0].get_text(strip=True),
            "price": tds[3].get_text(strip=True) if len(tds) > 3 else "",
        })
    return companies


def fetch_all_pages(max_pages: int = 10, proxy: str | None = None, log=None):
    session = requests.Session()
    all_companies = {}
    prev_html = None
    page = 1
    while True:
        if max_pages and page > max_pages:
            break
        resp = fetch_page(session, page, proxy)
        if resp.status_code != 200:
            if log:
                log(f"[WHTOP] Failed {page} status {resp.status_code}")
            break
        html = resp.text
        save_debug_html(page, html)
        if prev_html and html == prev_html:
            if log:
                log(f"[WHTOP] Page {page} duplicate of page {page-1}. Stopping.")
            break
        prev_html = html
        companies = parse_companies(html)
        if log:
            log(f"[WHTOP] Parsed {len(companies)} companies on page {page}")
        new = 0
        for c in companies:
            if c['domain'] not in all_companies:
                all_companies[c['domain']] = c
                new += 1
        if log:
            log(f"[WHTOP] Added {new} new companies")
        if not companies:
            break
        page += 1
    return list(all_companies.values())
