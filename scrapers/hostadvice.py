import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://hostadvice.com/hosting-services/"
DEBUG_TEMPLATE = "output/hostadvice_debug_page{page}.html"


def save_debug_html(page: int, html: str):
    os.makedirs('output', exist_ok=True)
    path = DEBUG_TEMPLATE.format(page=page)
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


def scrape_hostadvice_page(page: int, proxy: str | None = None, log=print) -> str:
    """Load a HostAdvice directory page using Selenium and return the HTML."""
    url = f"{BASE_URL}?page={page}"
    selector = (
        ".host-company-card,.company-card,.company-list-card,.listing__card," \
        ".provider-item,.review-card,.company-box,.provider-box,.review-box"
    )
    for attempt in range(1, 4):
        if log:
            log(f"[HostAdvice] Fetching page {page} via Selenium... (attempt {attempt})")
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36"
        )
        options.add_argument("--lang=en-US")
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
        driver = uc.Chrome(options=options)
        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            except Exception:
                pass
            html = driver.page_source
            save_debug_html(page, html)
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(selector)
            if not cards:
                if log:
                    log("[DEBUG] Selector '.company-card' failed — fallback used")
                cards = soup.select(".provider-box,.review-box,.provider-item")
            if cards:
                if log:
                    log(f"[HostAdvice] Page {page}: Found {len(cards)} companies ✅")
                return html
            if log:
                log(f"[HostAdvice] Page {page}: No company cards found — HTML saved")
        except Exception as e:
            if log:
                log(f"[ERROR] Selenium attempt {attempt} failed: {e}")
        finally:
            try:
                driver.quit()
            except Exception:
                pass
        # retry on failure
    return ""


def parse_companies(html: str, log=None):
    soup = BeautifulSoup(html, "html.parser")
    selectors = ".host-company-card,.company-card,.company-list-card,.listing__card,.host-item,.review-box,.provider-box"
    cards = soup.select(selectors)
    if log:
        log(f"[HostAdvice] Loaded {len(cards)} company cards")
    companies = []
    removed = 0
    for card in cards:
        name_el = card.select_one(".company-name")
        url_el = card.select_one(".company-name a")
        if not url_el:
            continue
        name = name_el.get_text(strip=True) if name_el else ""
        if any(k in name.lower() for k in ["affiliate", "reseller"]):
            removed += 1
            continue
        url = url_el["href"]
        if url.startswith("/"):
            url = urljoin(BASE_URL, url.lstrip("/"))
        domain = url.split("/")[2]
        logo_el = card.select_one("img")
        logo_url = logo_el["src"] if logo_el and logo_el.get("src") else ""
        companies.append({
            "name": name or domain.split('.')[0],
            "domain": domain,
            "url": url,
            "logo_url": logo_url,
            "favicon_url": f"https://{domain}/favicon.ico",
        })
    if log and removed:
        log(f"[HostAdvice] Removed {removed} affiliates")
    return companies


def fetch_all_pages(max_pages: int = 10, proxy: str | None = None, log=None):
    session = requests.Session()
    all_companies = {}
    page = 1
    while True:
        if max_pages and page > max_pages:
            break
        if log:
            log(f"[HostAdvice] Fetching page {page}")
        resp = fetch_page_requests(session, page, proxy)
        if resp.status_code == 403:
            if log:
                log(f"[HostAdvice] 403 on page {page}. Using Selenium")
            html = scrape_hostadvice_page(page, proxy, log=log)
        elif resp.status_code != 200:
            if log:
                log(f"[HostAdvice] Failed {page} status {resp.status_code}")
            break
        else:
            html = resp.text
            save_debug_html(page, html)
        companies = parse_companies(html, log=log)
        if log:
            log(f"[HostAdvice] Page {page}: found {len(companies)} hosting providers")
        new = 0
        for c in companies:
            if c['domain'] not in all_companies:
                all_companies[c['domain']] = c
                new += 1
        if log:
            log(f"[HostAdvice] Added {new} new companies")
        if not companies:
            save_debug_html(page, html)
            if log:
                log(f"[HostAdvice][DEBUG] No company cards found on page {page}")
            break
        page += 1
    return list(all_companies.values())
