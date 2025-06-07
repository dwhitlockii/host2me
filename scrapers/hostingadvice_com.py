import os
import re
import requests
from bs4 import BeautifulSoup

URL = "https://www.hostingadvice.com/blog/best-web-hosting-services/"
DEBUG_PATH = "output/host_debug_page_hostingadvice.html"


def save_debug_html(html: str):
    os.makedirs("output", exist_ok=True)
    with open(DEBUG_PATH, "w", encoding="utf-8") as f:
        f.write(html)


def fetch_companies(log=None):
    if log:
        log("[HostingAdvice] Fetching ranking page")
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    if resp.status_code not in (200, 404):
        if log:
            log(f"[HostingAdvice] Failed with status {resp.status_code}")
        return []
    html = resp.text
    save_debug_html(html)
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    for h in soup.select("h2.review-item-heading"):
        text = h.get_text(" ", strip=True)
        match = re.search(r"([A-Za-z0-9.-]+\.[A-Za-z]{2,})", text)
        if not match:
            continue
        domain = match.group(1).lower()
        name = domain.split(".")[0].capitalize()
        companies.append({
            "name": name,
            "domain": domain,
            "url": f"https://{domain}",
            "logo_url": "",
            "favicon_url": f"https://{domain}/favicon.ico",
        })
    if log:
        log(f"[HostingAdvice] Extracted {len(companies)} companies")
    return companies
