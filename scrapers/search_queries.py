import os
import re
import requests
from urllib.parse import quote_plus

TERMS = [
    "independent US web hosting company",
    "site:about.me \"web hosting\"",
    "intitle:\"web hosting company\" contact",
]

DEBUG_TEMPLATE = "output/search_query_{idx}.html"


def fetch_companies(log=None):
    companies = []
    seen = set()
    for idx, term in enumerate(TERMS, 1):
        q = quote_plus(term)
        url = f"https://r.jina.ai/https://www.bing.com/search?q={q}"
        if log:
            log(f"[Search] Querying {term}")
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            text = resp.text
        except Exception as e:
            if log:
                log(f"[Search] Error on query '{term}': {e}")
            continue
        os.makedirs("output", exist_ok=True)
        with open(DEBUG_TEMPLATE.format(idx=idx), "w", encoding="utf-8") as f:
            f.write(text)
        domains = re.findall(r"https?://([^/]+)", text)
        for d in domains:
            d = d.lower().split('@')[-1]
            d = d.lstrip('www.')
            if '.' not in d or d in seen:
                continue
            seen.add(d)
            companies.append({
                "name": d.split('.')[0].capitalize(),
                "domain": d,
                "url": f"https://{d}",
                "logo_url": "",
                "favicon_url": f"https://{d}/favicon.ico",
            })
    if log:
        log(f"[Search] Extracted {len(companies)} companies")
    return companies
