import os
import re
import requests

URL = "https://r.jina.ai/https://www.capterra.com/web-hosting-software/"
DEBUG_PATH = "output/capterra_debug.html"

def save_debug_html(html: str):
    os.makedirs("output", exist_ok=True)
    with open(DEBUG_PATH, "w", encoding="utf-8") as f:
        f.write(html)

def fetch_companies(log=None):
    if log:
        log("[Capterra] Fetching directory")
    try:
        resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        text = resp.text
    except Exception as e:
        if log:
            log(f"[Capterra] Error: {e}")
        return []
    save_debug_html(text)
    domains = set(re.findall(r"([A-Za-z0-9.-]+\.[A-Za-z]{2,})", text))
    companies = []
    for d in domains:
        d = d.lower().lstrip("www.")
        companies.append({
            "name": d.split(".")[0].capitalize(),
            "domain": d,
            "url": f"https://{d}",
            "logo_url": "",
            "favicon_url": f"https://{d}/favicon.ico",
        })
    if log:
        log(f"[Capterra] Extracted {len(companies)} companies")
    return companies
