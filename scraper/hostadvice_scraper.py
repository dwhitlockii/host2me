import requests
from bs4 import BeautifulSoup
import csv
import os
import time
# Add selenium imports
try:
    import undetected_chromedriver as uc
    HAVE_UC = True
except ImportError:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    HAVE_UC = False
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://hostadvice.com/hosting-services/"
OUTPUT_CSV = "output/hostadvice_us_companies.csv"

FIELDS = ["name", "url", "rating", "price", "location"]

# Proxy support
PROXY = os.environ.get('SCRAPER_PROXY')
DEBUG_MODE = os.environ.get('DEBUG_HOSTADVICE') == '1'

def parse_company_card(card):
    name = card.select_one(".company-name")
    name = name.get_text(strip=True) if name else ""
    url = card.select_one(".company-name a")
    url = url["href"] if url else ""
    if url and url.startswith("/"):
        url = "https://hostadvice.com" + url
    rating = card.select_one(".rating-value")
    rating = rating.get_text(strip=True) if rating else ""
    price = card.select_one(".price-value")
    price = price.get_text(strip=True) if price else ""
    location = card.select_one(".location")
    location = location.get_text(strip=True) if location else ""
    return {
        "name": name,
        "url": url,
        "rating": rating,
        "price": price,
        "location": location
    }

def fetch_with_selenium(url, retry=True):
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/114.0 Safari/537.36"
    )
    options = uc.ChromeOptions() if HAVE_UC else Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--lang=en-US,en")
    if PROXY:
        options.add_argument(f"--proxy-server={PROXY}")
    try:
        driver = uc.Chrome(options=options) if HAVE_UC else webdriver.Chrome(options=options)
    except Exception as e:
        print(f"[ERROR] Failed to start Chrome: {e}")
        if retry:
            try:
                driver = uc.Chrome(options=options) if HAVE_UC else webdriver.Chrome(options=options)
            except Exception as e2:
                print(f"[ERROR] Retry failed: {e2}")
                return f"<html><body><h1>Selenium failed: {e2}</h1></body></html>"
        else:
            return f"<html><body><h1>Selenium failed: {e}</h1></body></html>"
    try:
        driver.get(url)
        # Wait for company card to appear (try multiple selectors)
        found = False
        for class_name in ["company-card", "company-list-card", "listing__card"]:
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, class_name))
                )
                found = True
                break
            except Exception:
                continue
        # Scroll to bottom to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        # Wait again for more cards
        for class_name in ["company-card", "company-list-card", "listing__card"]:
            try:
                WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CLASS_NAME, class_name))
                )
                break
            except Exception:
                continue
        if DEBUG_MODE:
            driver.save_screenshot("output/hostadvice_debug.png")
        html = driver.page_source
        if DEBUG_MODE:
            with open("output/hostadvice_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
        return html
    except Exception as e:
        print(f"[ERROR] Selenium error: {e}")
        if DEBUG_MODE:
            try:
                driver.save_screenshot("output/hostadvice_error.png")
            except Exception:
                pass
        raise
    finally:
        try:
            driver.quit()
        except Exception:
            pass

def get_hostadvice_companies(max_pages=100, log_func=None):
    os.makedirs("output", exist_ok=True)
    companies = {}
    page = 1
    empty_page_count = 0
    session = requests.Session()
    if PROXY:
        session.proxies = {
            'http': PROXY,
            'https': PROXY
        }
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    prev_url = BASE_URL
    while True:
        if max_pages is not None and page > max_pages:
            msg = f"[HostAdvice] Stopping: reached hard max_pages limit ({max_pages})."
            print(msg)
            if log_func:
                log_func(msg)
            break
        url = f"{BASE_URL}?page={page}"
        headers = base_headers.copy()
        headers["Referer"] = prev_url if page > 1 else BASE_URL
        msg = f"[HostAdvice] Fetching URL: {url}"
        print(msg)
        if log_func:
            log_func(msg)
        res = session.get(url, headers=headers, timeout=10)
        prev_url = url
        if res.status_code == 403:
            msg = f"[HostAdvice] 403 Forbidden. Retrying with Selenium for {url}"
            print(msg)
            if log_func:
                log_func(msg)
            html = fetch_with_selenium(url)
            soup = BeautifulSoup(html, "html.parser")
        elif res.status_code != 200:
            msg = f"[HostAdvice] Failed to fetch page {page} (status {res.status_code})"
            print(msg)
            if log_func:
                log_func(msg)
            break
        else:
            soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select(".company-card")
        if not cards:
            cards = soup.select(".company-list-card")
        if not cards:
            cards = soup.select(".listing__card")
        msg = f"[HostAdvice][DEBUG] Found {len(cards)} company cards on page {page}."
        print(msg)
        if log_func:
            log_func(msg)
        if not cards:
            empty_page_count += 1
            msg = f"[HostAdvice][DEBUG] No company cards found on page {page} (empty_page_count={empty_page_count})."
            print(msg)
            if log_func:
                log_func(msg)
            if empty_page_count >= 2:
                msg = f"[HostAdvice] Stopping: {empty_page_count} consecutive pages with no companies. Directory likely exhausted."
                print(msg)
                if log_func:
                    log_func(msg)
                break
            page += 1
            continue
        new_domains = 0
        for card in cards:
            data = parse_company_card(card)
            domain = data["url"].split("/")[2] if data["url"].startswith("http") else data["url"]
            if domain and domain not in companies:
                companies[domain] = data
                new_domains += 1
                msg = f"[HostAdvice][DEBUG] Added: {data['name']} ({data['url']})"
                print(msg)
                if log_func:
                    log_func(msg)
        msg = f"[HostAdvice][DEBUG] Added {new_domains} new companies on page {page}. Total so far: {len(companies)}."
        print(msg)
        if log_func:
            log_func(msg)
        if new_domains == 0:
            empty_page_count += 1
        else:
            empty_page_count = 0
        if empty_page_count >= 2:
            msg = f"[HostAdvice] Stopping: {empty_page_count} consecutive pages with no new companies. Directory likely exhausted."
            print(msg)
            if log_func:
                log_func(msg)
            break
        page += 1
        time.sleep(1)
    # Write to CSV
    with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in companies.values():
            writer.writerow(row)
    print(f"[HostAdvice] Scraping complete. {len(companies)} companies written to {OUTPUT_CSV}")
    return list(companies.values())

if __name__ == "__main__":
    get_hostadvice_companies() 