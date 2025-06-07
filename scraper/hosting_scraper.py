import time
import re
import pandas as pd
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin
import os
from serpapi import GoogleSearch
import concurrent.futures
import threading
import queue
import csv
from requests.exceptions import RequestException
from colorama import Fore, Style, init as colorama_init
import tldextract
import json
from scraper.whtop_scraper import get_whtop_us_companies
from scraper.hostadvice_scraper import get_hostadvice_companies
from scrapers.hostingadvice_com import fetch_companies as fetch_hostingadvice_companies
from scrapers.techradar import fetch_companies as fetch_techradar_companies
import openpyxl

from utils.db import save_company, save_html
colorama_init(autoreset=True)

HEADERS = {'User-Agent': UserAgent().random}
SAVE_HTML = os.environ.get("SAVE_HTML", "1") == "1"

FIELDS = [
    "Rank", "Company Name", "Website URL", "Careers Page URL", "Remote Work Policy",
    "Tech Stack Relevance", "Application Status", "LinkedIn", "Twitter", "HTML Path"
]

# Expanded and more generic search terms
SEARCH_TERMS = [
        "independent web hosting companies USA",
        "top US-based hosting providers",
        "list of US cloud hosting companies",
        "best small business hosting companies US",
        "non-reseller hosting providers USA",
    "private web hosting company United States",
    "web hosting company directory USA",
    "list of web hosting companies",
    "top web hosting companies worldwide",
    "web hosting company list",
    "cloud hosting providers directory",
    "web hosting company reviews",
    "web hosting company comparison"
]

SEARCH_ENGINES = ["bing", "google", "duckduckgo"]

SEED_URLS = [
    "https://webhostingbuddy.com/top-web-hosting-companies/list/"
]

SEARCH_TERMS_FILE = 'output/search_terms.json'
COMPANIES_JSON = 'output/companies.json'

# Hosting company verification keywords
HOSTING_KEYWORDS = [
    "web hosting", "cloud hosting", "vps", "dedicated server", "shared hosting",
    "hosting plans", "domain registration", "cpanel", "plesk", "ssd hosting",
    "wordpress hosting", "reseller hosting", "managed hosting", "hosting provider"
]

# Loosened US-based check: allow if US in title, URL, or page text

DOMAIN_BLACKLIST = [
    'wikipedia.org', 'wikimedia.org', 'facebook.com', 'twitter.com', 'linkedin.com', 'youtube.com',
    'pinterest.com', 'reddit.com', 'instagram.com', 'tumblr.com', 'fandom.com', 'imdb.com',
    'yelp.com', 'tripadvisor.com', 'glassdoor.com', 'indeed.com', 'crunchbase.com', 'github.com',
    'medium.com', 'quora.com', 'forbes.com', 'bloomberg.com', 'nytimes.com', 'cnn.com', 'bbc.com',
    'amazon.com', 'google.com', 'bing.com', 'duckduckgo.com', 'yahoo.com', 'msn.com', 'ask.com',
    'baidu.com', 'alibaba.com', 'ebay.com', 'etsy.com', 'shopify.com', 'paypal.com', 'stripe.com',
    'wordpress.com', 'blogspot.com', 'weebly.com', 'wix.com', 'squarespace.com', 'godaddy.com',
    'namecheap.com', 'bluehost.com', 'hostgator.com', 'siteground.com', 'dreamhost.com', 'a2hosting.com',
    'hostinger.com', 'inmotionhosting.com', 'greengeeks.com', 'justhost.com', 'fatcow.com', 'ipage.com',
    'web.com', 'networksolutions.com', 'register.com', 'dotster.com', 'domain.com', 'enom.com',
    'resellerclub.com', 'hostmonster.com', 'arvixe.com', 'midphase.com', 'powweb.com', 'startlogic.com',
    'fastdomain.com', 'myhosting.com', 'lunarpages.com', 'ixwebhosting.com', 'webhostinghub.com',
    'hostpapa.com', 'hostmetro.com', 'webhostingpad.com', 'accuwebhosting.com', 'interserver.net',
    'tsohost.com', '123-reg.co.uk', 'one.com', 'strato.com', 'ovh.com', '1and1.com', 'ionos.com',
    'hetzner.com', 'contabo.com', 'scalahosting.com', 'cloudways.com', 'kinsta.com', 'wpengine.com',
    'flywheel.com', 'pagely.com', 'pressable.com', 'site5.com', 'liquidweb.com', 'rackspace.com',
    'digitalocean.com', 'linode.com', 'vultr.com', 'upcloud.com', 'aws.amazon.com', 'azure.com',
    'googlecloud.com', 'cloud.google.com', 'oracle.com', 'ibm.com', 'alibabacloud.com', 'cloudsigma.com',
    'kamatera.com', 'dreamhost.com', 'hostwinds.com', 'rosehosting.com', 'knownhost.com', 'hostdime.com',
    'turnkeyinternet.net', 'servermania.com', 'hivelocity.net', 'phoenixnap.com', 'coloamerica.com',
    'colocationamerica.com', 'coloatl.com', 'colocity.com', 'colohouse.com', 'colomart.com',
    'colomax.com', 'colomax.net', 'colomax.org', 'colomax.co.uk', 'colomax.us', 'colomax.ca',
    'colomax.eu', 'colomax.de', 'colomax.fr', 'colomax.it', 'colomax.nl', 'colomax.pl', 'colomax.ru',
    'colomax.se', 'colomax.ch', 'colomax.es', 'colomax.pt', 'colomax.gr', 'colomax.dk', 'colomax.no',
    'colomax.fi', 'colomax.be', 'colomax.at', 'colomax.ie', 'colomax.cz', 'colomax.hu', 'colomax.sk',
    'colomax.si', 'colomax.bg', 'colomax.hr', 'colomax.lt', 'colomax.lv', 'colomax.ee', 'colomax.lu',
    'colomax.li', 'colomax.mc', 'colomax.sm', 'colomax.va', 'colomax.md', 'colomax.by', 'colomax.ua',
    'colomax.ge', 'colomax.am', 'colomax.az', 'colomax.kz', 'colomax.uz', 'colomax.tm', 'colomax.kg',
    'colomax.tj', 'colomax.mn', 'colomax.hk', 'colomax.mo', 'colomax.tw', 'colomax.cn', 'colomax.jp',
    'colomax.kr', 'colomax.sg', 'colomax.my', 'colomax.id', 'colomax.ph', 'colomax.th', 'colomax.vn',
    'colomax.in', 'colomax.pk', 'colomax.bd', 'colomax.lk', 'colomax.np', 'colomax.bt', 'colomax.mv',
    'colomax.af', 'colomax.ir', 'colomax.iq', 'colomax.sy', 'colomax.lb', 'colomax.jo', 'colomax.ps',
    'colomax.kw', 'colomax.sa', 'colomax.om', 'colomax.ae', 'colomax.qa', 'colomax.bh', 'colomax.ye',
    'colomax.il', 'colomax.tr', 'colomax.cy'
]

STRICT = True
if not STRICT:
    MIN_ACCEPT_SCORE = 20
else:
    MIN_ACCEPT_SCORE = 30

REVIEW_QUEUE_PATH = 'output/review_queue.csv'

RAW_UNFILTERED_PATH = 'output/unfiltered_hosts.csv'

# Helper: retry logic for requests
def smart_get(url, headers=None, max_retries=2):
    delay = 1
    for attempt in range(max_retries+1):
        try:
            h = headers or HEADERS.copy()
            h['Accept-Language'] = 'en-US,en;q=0.9'
            res = requests.get(url, headers=h, timeout=5)
            if res.status_code in (403, 503):
                time.sleep(delay)
                delay *= 2
                continue
            return res
        except RequestException:
            time.sleep(delay)
            delay *= 2
    return None

# Helper: write to review queue
def append_review_queue(url, score, reasons, review_flag='', title='', meta_desc=''):
    os.makedirs(os.path.dirname(REVIEW_QUEUE_PATH), exist_ok=True)
    with open(REVIEW_QUEUE_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([url, score, '; '.join(reasons), review_flag, title, meta_desc])

# Helper: is_internal
def is_internal(href, base_url):
    if not href or not href.startswith('/') and not href.startswith(base_url):
        return False
    return True

def is_us_based(soup, url):
    text = soup.get_text().lower()
    title = soup.title.string.lower() if soup.title else ""
    url_lower = url.lower()
    # Loosened: accept if US in title, URL, page text, .us TLD, or US phone/address pattern
    if (
        "united states" in text or "usa" in text or
        "us" in title or "usa" in title or
        ".us" in url_lower or "/us" in url_lower
    ):
        return True
    # US phone number pattern
    if re.search(r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", text):
        return True
    # US address pattern (very loose)
    if re.search(r"\b[a-zA-Z]+,\s*(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b", text):
        return True
    return False

# Only skip for the most egregious disqualifiers
EGREGIOUS_DISQUALIFIERS = ["reseller of", "affiliate program", "review aggregator", "directory", "comparison site", "top 10 hosting", "best hosting", "forum", "reddit", "quora", "wikipedia", "blog", "news"]
def has_disqualifiers(soup):
    text = soup.get_text().lower()
    egregious = [
        'review aggregator', 'directory', 'comparison site', 'hosting review', 'hosting comparison', 'best hosting', 'top 10 hosting', 'hosting tool', 'hosting checker', 'hosting research', 'hosting guide', 'hosting blog', 'hosting news', 'hosting deals', 'hosting coupons', 'forum', 'reddit', 'quora', 'wikipedia', 'blog', 'news'
    ]
    for k in egregious:
        if k in text:
            return True
    return False

def get_social_links(soup):
    links = {"LinkedIn": "", "Twitter": ""}
    for a in soup.find_all("a", href=True):
        href = a['href']
        if "linkedin.com/company" in href:
            links["LinkedIn"] = href
        elif "twitter.com" in href:
            links["Twitter"] = href
    return links

def detect_remote_policy(soup):
    text = soup.get_text().lower()
    if "fully remote" in text:
        return "Fully Remote"
    elif "hybrid" in text:
        return "Hybrid"
    elif "on-site" in text:
        return "On-Site"
    return "Unknown"

def detect_tech_stack(soup):
    tech_terms = ["linux", "terraform", "aws", "puppet", "grafana", "prometheus", "ci/cd", "devops"]
    text = soup.get_text().lower()
    hits = sum(1 for t in tech_terms if t in text)
    return "Yes" if hits > 5 else "Partial" if hits > 2 else "No"

BORDERLINE_PATH = 'output/borderline_hosts.xlsx'

# Helper to write borderline cases to Excel
borderline_rows = []
def write_borderline_cases():
    if not borderline_rows:
        return
    import pandas as pd
    df = pd.DataFrame(borderline_rows)
    df.to_excel(BORDERLINE_PATH, index=False)

def is_hosting_company(soup, url=None, return_score=False, crawl_deeper=False, from_directory=False, source=None):
    text = soup.get_text().lower()
    title = soup.title.string.lower() if soup.title else ""
    meta_desc = ''
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta and meta.get('content'):
        meta_desc = meta['content'].lower()
    headings = ' '.join([h.get_text().lower() for h in soup.find_all(['h1','h2','h3'])])
    nav_links = ' '.join([a.get_text().lower() + ' ' + (a.get('href') or '').lower() for a in soup.find_all('a', href=True)])
    button_texts = ' '.join([b.get_text().lower() for b in soup.find_all(['button'])])
    score = 0
    reasons = []
    debug = []
    disqualified = False
    positive_signals = 0
    heading_title_nav_signal = False
    cta_found = False
    pricing_found = False
    # Positive keywords
    positive_keywords = [
        'shared hosting', 'vps hosting', 'dedicated server', 'dedicated servers', 'cloud hosting', 'reseller hosting',
        'linux hosting', 'windows hosting', 'cpanel hosting', 'web hosting', 'hosting plans', 'domains and hosting',
        'hosting features', 'buy hosting', 'pricing', 'wordpress hosting', 'ssd hosting', 'start your hosting business'
    ]
    for kw in positive_keywords:
        if kw in text:
            score += 20
            reasons.append(f"+20: '{kw}' in text")
            positive_signals += 1
        if kw in title or kw in meta_desc:
            score += 20
            reasons.append(f"+20: '{kw}' in title/meta")
            positive_signals += 1
            heading_title_nav_signal = True
        if kw in headings:
            score += 20
            reasons.append(f"+20: '{kw}' in heading")
            positive_signals += 1
            heading_title_nav_signal = True
        if kw in nav_links:
            score += 20
            reasons.append(f"+20: '{kw}' in nav")
            positive_signals += 1
            heading_title_nav_signal = True
    # Positive nav links
    nav_triggers = ['/hosting', '/web-hosting', '/vps', 'plans', 'dedicated', 'cloud', 'cpanel']
    nav_found = False
    for nav in nav_triggers:
        if nav in nav_links:
            score += 15
            nav_found = True
            reasons.append(f"+15: nav link '{nav}'")
            positive_signals += 1
            heading_title_nav_signal = True
    if not nav_found:
        score -= 2  # softened
        reasons.append("-2: No strong nav/product link found")
    # CTA check (expanded)
    cta_triggers = ['buy', 'order', 'sign up', 'signup', 'get started', 'start now', 'register', 'contact', 'request quote', 'get quote', 'learn more', 'view plans', 'see plans', 'get a demo']
    for cta in cta_triggers:
        if cta in nav_links or cta in button_texts:
            cta_found = True
            reasons.append(f"+CTA: '{cta}' found in nav/button")
            break
    if not cta_found:
        score -= 2  # softened
        reasons.append("-2: No CTA found")
    # Pricing/plans/packages check (in nav text or href or headings)
    pricing_triggers = ['pricing', 'plans', 'packages']
    for p in pricing_triggers:
        if p in nav_links or p in headings:
            pricing_found = True
            reasons.append(f"+Pricing: '{p}' found in nav/headings")
            break
    if not pricing_found:
        score -= 2  # softened
        reasons.append("-2: No pricing/plans/packages found")
    # Tech stack
    tech_stack = ['cpanel', 'plesk', 'litespeed', 'whmcs', 'softaculous']
    for tech in tech_stack:
        if tech in text:
            score += 25
            reasons.append(f"+25: tech '{tech}' found")
            positive_signals += 1
    # Brand terms in title/meta
    brand_terms = ['web hosting provider', 'cpanel hosting', 'wordpress hosting', 'ssd hosting', 'start your hosting business']
    for term in brand_terms:
        if term in title or term in meta_desc:
            score += 20
            reasons.append(f"+20: brand term '{term}' in title/meta")
            positive_signals += 1
            heading_title_nav_signal = True
    # Negative indicators (softened)
    egregious_negatives = ['directory', 'review aggregator', 'comparison site', 'forum', 'reddit', 'quora', 'wikipedia']
    soft_negatives = [
        'review', 'compare', 'blog', 'news', 'wiki', 'affiliate', 'reseller', 'agency', 'consulting',
        'statistics', 'statista', 'market research', 'industry report', 'analysis', 'data portal', 'comparison', 'top 10', 'best hosting', 'deals', 'coupons', 'guide', 'checker', 'tool', 'list of', 'report', 'overview', 'summary', 'rankings', 'ratings', 'scorecard', 'survey', 'privacy policy', 'terms of use', 'disclaimer', 'about us', 'contact us', 'careers', 'jobs', 'team', 'press', 'media', 'events', 'partners', 'resources', 'whitepaper', 'case study', 'ebook', 'webinar', 'faq', 'support', 'help', 'login', 'signup', 'register'
    ]
    for neg in egregious_negatives:
        if neg in text or neg in title or neg in meta_desc or neg in headings:
            score -= 25
            reasons.append(f"-25: egregious negative '{neg}'")
    for neg in soft_negatives:
        if neg in text or neg in title or neg in meta_desc or neg in headings:
            score -= 10
            reasons.append(f"-10: soft negative '{neg}'")
    # Domain signal
    if url:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if not any(x in domain for x in ['host', 'cloud', 'server', 'vps', 'web', 'data', 'colo']):
            score -= 2  # softened
            reasons.append("-2: domain lacks hosting signal")
    # Directory boost
    if from_directory:
        score += 10
        reasons.append("+10: Directory source boost")
    # Multi-page analysis (if homepage fails, try /hosting, /plans, /services)
    best_score = score
    best_reasons = list(reasons)
    if crawl_deeper and url:
        for sub in ['/hosting', '/plans', '/services']:
            try:
                sub_url = url.rstrip('/') + sub
                res = requests.get(sub_url, headers=HEADERS, timeout=5)
                if res.status_code == 200 and 'text/html' in res.headers.get('Content-Type', '').lower():
                    sub_soup = BeautifulSoup(res.text, 'html.parser')
                    sub_score, sub_reasons = 0, []
                    # Recurse but don't crawl deeper again
                    accepted, _, sub_score, _, _ = is_hosting_company(sub_soup, sub_url, return_score=True, crawl_deeper=False, from_directory=from_directory)
                    if sub_score > best_score:
                        best_score = sub_score
                        best_reasons = sub_reasons
                        reasons.append(f"+Multi-page: {sub} score {sub_score}")
            except Exception as e:
                reasons.append(f"[Multi-page error: {e}]")
    # Rescue logic: 20 <= score < MIN_ACCEPT_SCORE and (careers/jobs link or tech keyword present)
    rescue = False
    rescue_reasons = []
    careers_url = ""
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "career" in href or "jobs" in href:
            careers_url = href
            rescue = True
            rescue_reasons.append("Careers/Jobs link found")
            break
    tech_keywords = ['cpanel', 'litespeed', 'whmcs']
    tech_found = any(tk in text for tk in tech_keywords)
    if tech_found:
        rescue = True
        rescue_reasons.append("Tech keyword found")
    # Final decision
    accepted = False
    acceptance_status = "Skipped"
    review_flag = ''
    if best_score >= MIN_ACCEPT_SCORE and not disqualified:
        accepted = True
        acceptance_status = "Accepted"
        debug.append(f"SCORE: {best_score} ✅ ADDED")
    elif 20 <= best_score < MIN_ACCEPT_SCORE:
        if (STRICT and rescue) or (not STRICT and (rescue or tech_found or careers_url)):
            accepted = True
            acceptance_status = "Rescued"
            debug.append(f"SCORE: {best_score} ⚠️ RESCUED ({', '.join(rescue_reasons)})")
        else:
            debug.append(f"SCORE: {best_score} 🧐 CANDIDATE")
            print(f"[🧐 CANDIDATE] {url} — borderline, score: {best_score}")
            print("Reasons:", best_reasons)
            append_review_queue(url, best_score, best_reasons, review_flag='borderline', title=title, meta_desc=meta_desc)
            borderline_rows.append({
                'URL': url,
                'Score': best_score,
                'Reasons': '; '.join(best_reasons),
                'Title': title,
                'Meta Description': meta_desc,
                'Source': source or ("Directory" if from_directory else "Search")
            })
    elif -5 <= best_score < 20 and not disqualified:
        review_flag = 'possible_host'
        debug.append(f"SCORE: {best_score} 🤔 POSSIBLE HOST")
        append_review_queue(url, best_score, best_reasons, review_flag=review_flag, title=title, meta_desc=meta_desc)
        borderline_rows.append({
            'URL': url,
            'Score': best_score,
            'Reasons': '; '.join(best_reasons),
            'Title': title,
            'Meta Description': meta_desc,
            'Source': source or ("Directory" if from_directory else "Search")
        })
    else:
        debug.append(f"SCORE: {best_score} ❌ REJECTED")
        append_review_queue(url, best_score, best_reasons, review_flag='', title=title, meta_desc=meta_desc)
    print(f"[DEBUG] {url or ''}\n" + '\n'.join(debug))
    if return_score:
        return accepted, debug, best_score, True, acceptance_status
    return accepted, None, None, True, acceptance_status

def extract_company_info(url, rank=None, seen_domains=None, from_directory=False, source=None):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
        # Blacklist check
        if any(domain == b or domain.endswith('.' + b) for b in DOMAIN_BLACKLIST):
            print(f"[✘] Skipped (Blacklisted domain): {url}")
            return None, 'Blacklisted domain', None
        if seen_domains is not None and domain in seen_domains:
            print(f"[✘] Skipped (Duplicate domain): {url}")
            return None, 'Duplicate domain', None
        res = requests.get(url, headers=HEADERS, timeout=5)
        content_type = res.headers.get('Content-Type', '').lower()
        html_path = save_html(domain, res.text) if SAVE_HTML else ""
        if 'text/html' not in content_type:
            print(f"[✘] Skipped (Non-HTML content: {content_type}): {url}")
            return None, f'Non-HTML content: {content_type}', None
        soup = BeautifulSoup(res.text, 'html.parser')
        if not is_us_based(soup, url):
            companies = extract_companies_from_directory(soup, url, seen_domains, from_directory=from_directory)
            if companies:
                print(f"[LOG] Directory/list page found at {url}, extracted {len(companies)} companies")
                return companies, None, None
            print(f"[✘] Skipped (Not US-based or not a directory/list): {url}")
            return None, 'Not US-based or not a directory/list', None
        if has_disqualifiers(soup):
            print(f"[✘] Skipped (Disqualifiers matched): {url}")
            return None, 'Disqualifiers matched', None
        accepted, reasons, score, nav_found, acceptance_status = is_hosting_company(soup, url, return_score=True, crawl_deeper=True, from_directory=from_directory, source=source)
        if not accepted:
            print(f"[✘] Skipped (Not a hosting company): {url}")
            return None, 'Not a hosting company', reasons
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        name = parsed.netloc.replace("www.", "").split('.')[0].capitalize()
        careers_url = ""
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if "career" in href or "jobs" in href:
                careers_url = href if "http" in href else base_url + href
                break
        # Careers page is now optional
        if not careers_url:
            print(f"[!] Warning: No careers page found for {url}")
        social = get_social_links(soup)
        company = {
            "Rank": rank if rank else "",
            "Company Name": name,
            "Website URL": base_url,
            "Careers Page URL": careers_url,
            "Remote Work Policy": detect_remote_policy(soup),
            "Tech Stack Relevance": detect_tech_stack(soup),
            "Application Status": "",
            "LinkedIn": social["LinkedIn"],
            "Twitter": social["Twitter"],
            "HTML Path": html_path,
            "Scoring Breakdown": f"Score: {score} | {'; '.join(reasons)}",
            "Acceptance Status": acceptance_status,
            "Source": source or ("Directory" if from_directory else "Search")
        }
        save_company(company)
        return [company], None, reasons
    except Exception as e:
        print(f"[ERR] Failed: {url} — {e}")
        return None, f'Error: {e}', None

def extract_companies_from_directory(soup, base_url, seen_domains=None, from_directory=True):
    companies = []
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and not any(domain in href for domain in ["bing.com", "google.com", "duckduckgo.com"]):
            links.add(href)
    rank = 1
    for link in links:
        try:
            parsed = urlparse(link)
            domain = parsed.netloc.lower().replace('www.', '')
            if any(domain == b or domain.endswith('.' + b) for b in DOMAIN_BLACKLIST):
                print(f"[✘] Skipped (Blacklisted domain): {link}")
                continue
            if seen_domains is not None and domain in seen_domains:
                print(f"[✘] Skipped (Duplicate domain): {link}")
                continue
            res = requests.get(link, headers=HEADERS, timeout=5)
            content_type = res.headers.get('Content-Type', '').lower()
            html_path = save_html(domain, res.text) if SAVE_HTML else ""
            if 'text/html' not in content_type:
                print(f"[✘] Skipped (Non-HTML content: {content_type}): {link}")
                continue
            sub_soup = BeautifulSoup(res.text, 'html.parser')
            if has_disqualifiers(sub_soup):
                print(f"[✘] Skipped (Disqualifiers matched): {link}")
                continue
            accepted, reasons, score, nav_found, acceptance_status = is_hosting_company(sub_soup, link, return_score=True, from_directory=True, source="Directory")
            if not accepted:
                print(f"[✘] Skipped (Not a hosting company): {link}")
                continue
            base = f"{parsed.scheme}://{parsed.netloc}"
            name = parsed.netloc.replace("www.", "").split('.')[0].capitalize()
            careers_url = ""
            for a in sub_soup.find_all("a", href=True):
                href = a["href"].lower()
                if "career" in href or "jobs" in href:
                    careers_url = href if "http" in href else base + href
                    break
            social = get_social_links(sub_soup)
            company = {
                "Rank": rank,
                "Company Name": name,
                "Website URL": base,
                "Careers Page URL": careers_url,
                "Remote Work Policy": detect_remote_policy(sub_soup),
                "Tech Stack Relevance": detect_tech_stack(sub_soup),
                "Application Status": "",
                "LinkedIn": social["LinkedIn"],
                "Twitter": social["Twitter"],
                "HTML Path": html_path,
                "Scoring Breakdown": f"Score: {score} | {'; '.join(reasons)}",
                "Acceptance Status": acceptance_status,
                "Source": "Directory"
            }
            companies.append(company)
            save_company(company)
            if seen_domains is not None:
                seen_domains.add(domain)
            print(f"[✔] Added: {name} ({base})")
            rank += 1
        except Exception as e:
            print(f"[ERR] Failed (directory): {link} — {e}")
            continue
    if companies:
        print(f"[LOG] Extracted {len(companies)} companies from directory page: {base_url}")
    write_borderline_cases()
    return companies if companies else None

def get_search_terms():
    if os.path.exists(SEARCH_TERMS_FILE):
        with open(SEARCH_TERMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return SEARCH_TERMS

def search_hosting_companies(log_func=None):
    urls = list(SEED_URLS)
    terms = get_search_terms()
    serpapi_key = os.environ.get("SERPAPI_KEY")
    search_pool_size = int(os.environ.get("SCRAPER_SEARCH_POOL_SIZE", 5))
    print(f"[PROFILE] Using search pool size: {search_pool_size}")
    if log_func:
        log_func(f"[PROFILE] Using search pool size: {search_pool_size}")
    search_tasks = []
    results_lock = threading.Lock() if 'threading' in globals() else None
    all_urls = []
    all_logs = []
    def search_task(engine, term):
        local_urls = []
        local_logs = []
        msg = f"[LOG] Sending search query to {engine}: '{term}'"
        if log_func:
            log_func(msg)
        local_logs.append(msg)
        print(msg)
        if serpapi_key and engine in ["bing", "google", "duckduckgo"]:
            params = {
                "engine": engine,
                "q": term,
                "api_key": serpapi_key
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            msg2 = f"[LOG] Processing results from {engine} for '{term}'"
            if log_func:
                log_func(msg2)
            local_logs.append(msg2)
            print(msg2)
            organic_results = results.get("organic_results", [])
            for res in organic_results:
                link = res.get("link")
                if link and link.startswith("http"):
                    local_urls.append(link)
            print(f"[LOG] {engine} search for '{term}' found {len(organic_results)} results")
            time.sleep(2)
        else:
            if engine == "bing":
                query = f"https://www.bing.com/search?q={term.replace(' ', '+')}"
                res = requests.get(query, headers=HEADERS, timeout=5)
                msg2 = f"[LOG] Processing results from Bing for '{term}'"
                if log_func:
                    log_func(msg2)
                local_logs.append(msg2)
                print(msg2)
                soup = BeautifulSoup(res.text, 'html.parser')
                found = 0
                for a in soup.select('li.b_algo h2 a'):
                    href = a.get('href')
                    if href and href.startswith("http"):
                        local_urls.append(href)
                        found += 1
                print(f"[LOG] Bing search for '{term}' found {found} results")
                time.sleep(2)
        return local_urls, local_logs
    with concurrent.futures.ThreadPoolExecutor(max_workers=search_pool_size) as executor:
        future_to_task = {}
        for engine in SEARCH_ENGINES:
            for term in terms:
                future = executor.submit(search_task, engine, term)
                future_to_task[future] = (engine, term)
        for future in concurrent.futures.as_completed(future_to_task):
            local_urls, local_logs = future.result()
            all_urls.extend(local_urls)
            all_logs.extend(local_logs)
    for msg in all_logs:
        if log_func:
            log_func(msg)
    print(f"[LOG] Total URLs collected from search: {len(set(urls + all_urls))}")
    return list(set(urls + all_urls))

def stream_hosting_scraper(mode="directory", max_whtop_pages=None):
    print("[LOG] Starting scrape...")
    yield "[LOG] Starting scrape..."
    results = []
    def log_func(msg):
        print(msg)
        yield msg
    t0 = time.time()
    urls = []
    if mode == "hostadvice":
        print("[LOG] Using HostAdvice directory mode.")
        yield "[LOG] Using HostAdvice directory mode."
        _logs = []
        try:
            companies = get_hostadvice_companies(log_func=lambda m: _logs.append(m))
        except Exception as e:
            err = f"[ERROR] HostAdvice scrape failed: {e}"
            print(err)
            yield err
            return
        for msg in _logs:
            yield msg
        for i, company in enumerate(companies, 1):
            log_line = f"[✔] Added: {company['name']} ({company['url']})"
            print(log_line)
            yield log_line
            yield f"[PROGRESS] Processed {i}/{len(companies)}: {company['url']} (status: Added)"
        print(f"[✅] HostAdvice scrape complete — saved {len(companies)} companies to CSV")
        yield f"[✅] HostAdvice scrape complete — saved {len(companies)} companies to CSV"
        return
    if mode == "hostingadvice":
        print("[LOG] Using HostingAdvice rankings mode.")
        yield "[LOG] Using HostingAdvice rankings mode."
        logs = []
        companies = fetch_hostingadvice_companies(log=lambda m: logs.append(m))
        for m in logs:
            yield m
        for i, company in enumerate(companies, 1):
            line = f"[✔] Added: {company['name']} ({company['url']})"
            print(line)
            yield line
            yield f"[PROGRESS] Processed {i}/{len(companies)}: {company['url']}(status: Added)"
        print(f"[✅] HostingAdvice scrape complete — saved {len(companies)} companies")
        yield f"[✅] HostingAdvice scrape complete — saved {len(companies)} companies"
        return
    if mode == "techradar":
        print("[LOG] Using TechRadar rankings mode.")
        yield "[LOG] Using TechRadar rankings mode."
        logs = []
        companies = fetch_techradar_companies(log=lambda m: logs.append(m))
        for m in logs:
            yield m
        for i, company in enumerate(companies, 1):
            line = f"[✔] Added: {company['name']} ({company['url']})"
            print(line)
            yield line
            yield f"[PROGRESS] Processed {i}/{len(companies)}: {company['url']}(status: Added)"
        print(f"[✅] TechRadar scrape complete — saved {len(companies)} companies")
        yield f"[✅] TechRadar scrape complete — saved {len(companies)} companies"
        return
    if mode == "directory":
        # WHTop directory mining
        def yield_log(msg):
            print(msg)
            yield msg
        # Use a generator to yield log lines from get_whtop_us_companies
        whtop_gen = get_whtop_us_companies(max_pages=max_whtop_pages, log_func=lambda m: (yield m))
        whtop_companies = []
        for item in whtop_gen:
            if isinstance(item, dict):
                whtop_companies.append(item)
            else:
                yield item
        urls = [c["url"] for c in whtop_companies if c["url"]]
        print(f"[PROFILE] WHTop mining phase found {len(urls)} candidate homepages")
        yield f"[PROFILE] WHTop mining phase found {len(urls)} candidate homepages"
    else:
        # Legacy: search engine scraping
        def yield_log(msg):
            print(msg)
            yield msg
        urls = search_hosting_companies(log_func=yield_log)
        print(f"[PROFILE] Search phase found {len(urls)} candidate URLs")
        yield f"[PROFILE] Search phase found {len(urls)} candidate URLs"
    search_time = time.time() - t0
    print(f"[PROFILE] Discovery phase took {search_time:.2f} seconds")
    yield f"[PROFILE] Discovery phase took {search_time:.2f} seconds"
    extraction_pool_size = int(os.environ.get("SCRAPER_EXTRACTION_POOL_SIZE", 10))
    print(f"[PROFILE] Using extraction pool size: {extraction_pool_size}")
    yield f"[PROFILE] Using extraction pool size: {extraction_pool_size}"
    rank = 1
    processed = []
    seen_domains = set()
    log_queue = queue.Queue()
    def process_url(url_rank_tuple):
        url, rank = url_rank_tuple
        try:
            t_url = time.time()
            log_queue.put(f"[SITE] Checking: {url}")
            data, skip_reason, reasons = extract_company_info(url, rank=rank, seen_domains=seen_domains)
            t_url_done = time.time()
            elapsed = t_url_done - t_url
            log_queue.put(f"[PROFILE] Processed {url} in {elapsed:.2f} seconds")
            status = "Added" if data else (skip_reason or "Skipped")
            if data:
                for company in data:
                    log_line = f"[✔] Added: {company['Company Name']} ({company['Website URL']})"
                    log_queue.put(log_line)
                    processed.append(company)
            else:
                if skip_reason:
                    log_queue.put(f"[✘] Skipped ({skip_reason}): {url}")
                else:
                    log_queue.put(f"[✘] Skipped: {url}")
            # Always log progress
            log_queue.put(f"[PROGRESS] Processed {rank}/{total}: {url} (status: {status})")
        except Exception as e:
            log_queue.put(f"[ERR] Failed: {url} — {str(e)}")
            log_queue.put(f"[PROGRESS] Processed {rank}/{total}: {url} (status: Error)")
    url_rank_tuples = [(url, i+1) for i, url in enumerate(urls[:100])]
    total = len(url_rank_tuples)
    t2 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=extraction_pool_size) as executor:
        futures = [executor.submit(process_url, t) for t in url_rank_tuples]
        finished = 0
        while finished < total:
            try:
                log = log_queue.get(timeout=0.1)
                print(log)
                yield log
            except queue.Empty:
                # Check if all futures are done
                finished = sum(1 for f in futures if f.done())
    # Drain any remaining logs
    while not log_queue.empty():
        log = log_queue.get()
        print(log)
        yield log
    t3 = time.time()
    extraction_time = t3 - t2
    print(f"[PROFILE] Company info extraction phase took {extraction_time:.2f} seconds")
    yield f"[PROFILE] Company info extraction phase took {extraction_time:.2f} seconds"
    t4 = time.time()
    if processed:
        df = pd.DataFrame(processed, columns=FIELDS + ["Scoring Breakdown", "Acceptance Status"])
        df.to_excel("output/us_hosting_companies.xlsx", index=False)
        with open(COMPANIES_JSON, "w", encoding="utf-8") as f:
            json.dump(processed, f, ensure_ascii=False)
        t5 = time.time()
        file_write_time = t5 - t4
        print(f"[PROFILE] File writing phase took {file_write_time:.2f} seconds")
        yield f"[PROFILE] File writing phase took {file_write_time:.2f} seconds"
        print(f"[✅] Scrape complete — saved {len(processed)} companies to Excel")
        yield f"[✅] Scrape complete — saved {len(processed)} companies to Excel"
        # At end, print color summary
        added_count = len([c for c in processed if c.get('Acceptance Status') == 'Accepted'])
        rescued_count = len([c for c in processed if c.get('Acceptance Status') == 'Rescued'])
        skipped_count = len(url_rank_tuples) - len(processed)
        print(f"{Fore.GREEN}🟢 Added: {added_count}{Style.RESET_ALL} | {Fore.YELLOW}🟡 Borderline: {rescued_count}{Style.RESET_ALL} | {Fore.RED}🔴 Skipped: {skipped_count}{Style.RESET_ALL}")
        yield f"[SUMMARY] 🟢 Added: {added_count} | 🟡 Borderline: {rescued_count} | 🔴 Skipped: {skipped_count}"
    else:
        print("[⚠️] No valid results were scraped.")
        yield "[⚠️] No valid results were scraped."

def foundational_scrape():
    urls = search_hosting_companies()
    print(f"[RAW] Found {len(urls)} candidate URLs. Beginning foundational scrape...")
    rows = []
    for url in urls:
        try:
            res = smart_get(url)
            if not res or 'text/html' not in res.headers.get('Content-Type', '').lower():
                continue
            soup = BeautifulSoup(res.text, 'html.parser')
            # Base domain
            ext = tldextract.extract(url)
            base_domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
            # Title
            title = soup.title.string.strip() if soup.title and soup.title.string else ''
            # Meta description
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            meta_desc = meta_tag['content'].strip() if meta_tag and meta_tag.get('content') else ''
            # Top 10 visible text snippets
            snippets = []
            for tag in soup.find_all(['h1','h2','h3','p','li']):
                txt = tag.get_text(strip=True)
                if txt and len(txt) > 20:
                    snippets.append(txt)
                if len(snippets) >= 10:
                    break
            # All <a> hrefs and anchor texts
            links = []
            for a in soup.find_all('a', href=True):
                anchor = a.get_text(strip=True)
                href = a['href']
                links.append(f"{anchor}|||{href}")
            row = {
                'url': url,
                'base_domain': base_domain,
                'title': title,
                'meta_description': meta_desc,
                'snippets': '|'.join(snippets),
                'links': '|'.join(links)
            }
            rows.append(row)
            print(f"[RAW] Added candidate: {url}")
        except Exception as e:
            print(f"[RAW] Error scraping {url}: {e}")
            continue
    # Write to CSV
    os.makedirs(os.path.dirname(RAW_UNFILTERED_PATH), exist_ok=True)
    with open(RAW_UNFILTERED_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url','base_domain','title','meta_description','snippets','links'])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"[RAW] Foundational scrape complete. {len(rows)} rows written to {RAW_UNFILTERED_PATH}")
