import os
import re
import requests
from bs4 import BeautifulSoup

URL = "https://www.techradar.com/web-hosting/best-web-hosting-service-websites"
DEBUG_PATH = "output/host_debug_page_techradar.html"


def save_debug_html(html: str):
    os.makedirs("output", exist_ok=True)
    with open(DEBUG_PATH, "w", encoding="utf-8") as f:
        f.write(html)


def fetch_companies(log=None):
    if log:
        log("[TechRadar] Fetching ranking page")
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    if resp.status_code != 200:
        if log:
            log(f"[TechRadar] Failed with status {resp.status_code}")
        return []
    html = resp.text
    save_debug_html(html)
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    for h in soup.select("h3.product__title"):
        name = h.get_text(strip=True)
        name_clean = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
        domain = f"{name_clean}.com"
        companies.append({
            "name": name,
            "domain": domain,
            "url": f"https://{domain}",
            "logo_url": "",
            "favicon_url": f"https://{domain}/favicon.ico",
        })
    if log:
        log(f"[TechRadar] Extracted {len(companies)} companies")
    return companies
