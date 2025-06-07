import os
import re
import requests

DIRECTORY_URLS = [
    "https://r.jina.ai/https://www.webhostdir.com/",
    "https://r.jina.ai/https://www.hostsearch.com/",
]

DEBUG_TEMPLATE = "output/open_directory_{idx}.html"


def fetch_companies(log=None):
    companies = []
    seen = set()
    for idx, url in enumerate(DIRECTORY_URLS, 1):
        if log:
            log(f"[OpenDir] Fetching {url}")
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            text = resp.text
        except Exception as e:
            if log:
                log(f"[OpenDir] Error fetching {url}: {e}")
            continue
        os.makedirs("output", exist_ok=True)
        with open(DEBUG_TEMPLATE.format(idx=idx), "w", encoding="utf-8") as f:
            f.write(text)
        domains = re.findall(r"([A-Za-z0-9.-]+\.[A-Za-z]{2,})", text)
        for d in domains:
            d = d.lower().lstrip("www.")
            if d in seen:
                continue
            seen.add(d)
            companies.append({
                "name": d.split(".")[0].capitalize(),
                "domain": d,
                "url": f"https://{d}",
                "logo_url": "",
                "favicon_url": f"https://{d}/favicon.ico",
            })
    if log:
        log(f"[OpenDir] Extracted {len(companies)} companies")
    return companies
