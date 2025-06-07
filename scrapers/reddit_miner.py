import os
import re
import json
import requests

URL = "https://www.reddit.com/r/webhosting/top/.json?limit=100&raw_json=1"
DEBUG_PATH = "output/reddit_webhosting.json"

headers = {"User-Agent": "Mozilla/5.0"}

def fetch_companies(log=None):
    if log:
        log("[Reddit] Fetching /r/webhosting threads")
    try:
        resp = requests.get(URL, headers=headers, timeout=10)
        data = resp.json()
    except Exception as e:
        if log:
            log(f"[Reddit] Error: {e}")
        return []
    os.makedirs("output", exist_ok=True)
    with open(DEBUG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)
    text = json.dumps(data)
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
        log(f"[Reddit] Extracted {len(companies)} domains")
    return companies
