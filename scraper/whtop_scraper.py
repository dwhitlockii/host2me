import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import re

BASE_URL = "https://www.whtop.com/directory/country/us"
OUTPUT_CSV = "output/whtop_us_companies.csv"

# Helper to extract company info from a company card
def parse_company_card(card):
    name = card.select_one(".companyTitle")
    name = name.get_text(strip=True) if name else ""
    url = card.select_one(".companyTitle a")
    url = url["href"] if url else ""
    if url and url.startswith("/"):
        url = "https://www.whtop.com" + url
    rating = card.select_one(".rating")
    rating = rating.get_text(strip=True) if rating else ""
    reviews = card.select_one(".reviews")
    reviews = reviews.get_text(strip=True) if reviews else ""
    desc = card.select_one(".companyDescription")
    desc = desc.get_text(strip=True) if desc else ""
    return {
        "name": name,
        "url": url,
        "rating": rating,
        "reviews": reviews,
        "description": desc
    }

def get_whtop_us_companies(max_pages=200, log_func=None):
    os.makedirs("output", exist_ok=True)
    companies = {}
    page = 1
    empty_page_count = 0
    last_total = 0
    session = requests.Session()
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    prev_url = BASE_URL
    while True:
        if max_pages is not None and page > max_pages:
            msg = f"[WHTOP] Stopping: reached hard max_pages limit ({max_pages})."
            print(msg)
            if log_func:
                log_func(msg)
            break
        url = f"{BASE_URL}?page={page}"
        headers = base_headers.copy()
        headers["Referer"] = prev_url if page > 1 else BASE_URL
        msg = f"[WHTOP] Fetching URL: {url}"
        print(msg)
        if log_func:
            log_func(msg)
        res = session.get(url, headers=headers, timeout=10)
        # Save HTML for first 3 pages
        if page <= 3:
            debug_path = f"output/whtop_debug_page{page}.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(res.text)
            print(f"[WHTOP][DEBUG] Saved HTML to {debug_path}")
        if res.status_code != 200:
            msg = f"[WHTOP] Failed to fetch page {page} (status {res.status_code})"
            print(msg)
            if log_func:
                log_func(msg)
            break
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.select_one("table.table.alt")
        msg = f"[WHTOP][DEBUG] Found {len(table.find_all('tr', class_=['s_alt_row1', 's_alt_row2'])) if table else 0} company rows on page {page}."
        print(msg)
        if log_func:
            log_func(msg)
        if not table:
            msg = f"[WHTOP][DEBUG] No <table class='table alt'> found. Stopping."
            print(msg)
            if log_func:
                log_func(msg)
            break
        rows = table.find_all("tr", class_=["s_alt_row1", "s_alt_row2"])
        if not rows:
            msg = f"[WHTOP][DEBUG] No company rows found in table. Stopping."
            print(msg)
            if log_func:
                log_func(msg)
            break
        new_domains = 0
        page_domains = []
        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 7:
                continue
            plan_name = tds[0].get_text(strip=True)
            domain_cell = tds[6].get_text(strip=True)
            match = re.search(r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", domain_cell)
            if not match:
                continue
            domain = match.group(0)
            price = tds[3].get_text(strip=True) if len(tds) > 3 else ""
            if domain and domain not in companies:
                homepage = f"https://{domain}" if not domain.startswith("http") else domain
                companies[domain] = {
                    "name": domain.split(".")[0].capitalize(),
                    "domain": domain,
                    "url": homepage,
                    "plan_name": plan_name,
                    "price": price
                }
                new_domains += 1
                page_domains.append(domain)
        msg = f"[WHTOP][DEBUG] Added {new_domains} new companies on page {page}. Total so far: {len(companies)}."
        print(msg)
        if log_func:
            log_func(msg)
        if page_domains:
            msg = f"[WHTOP][DEBUG] First 3 domains this page: {page_domains[:3]}"
            print(msg)
            if log_func:
                log_func(msg)
        if new_domains == 0:
            empty_page_count += 1
            msg = f"[WHTOP][DEBUG] No new companies found on page {page} (empty_page_count={empty_page_count})."
            print(msg)
            if log_func:
                log_func(msg)
        else:
            empty_page_count = 0
        if empty_page_count >= 2:
            msg = f"[WHTOP] Stopping: {empty_page_count} consecutive pages with no new companies. Directory likely exhausted."
            print(msg)
            if log_func:
                log_func(msg)
            break
        prev_url = url
        page += 1
    return list(companies.values())

def scrape_whtop_us():
    companies = get_whtop_us_companies()
    # Write to CSV
    with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "rating", "reviews", "description"])
        writer.writeheader()
        for row in companies:
            writer.writerow(row)
    print(f"[WHTOP] Scraping complete. {len(companies)} companies written to {OUTPUT_CSV}")

if __name__ == "__main__":
    scrape_whtop_us() 