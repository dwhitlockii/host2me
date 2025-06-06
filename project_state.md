# Project State

## Purpose
This is a Python + Flask-powered web application that scrapes the internet for U.S.-based primary web hosting companies, filters out irrelevant ones, and builds a structured dataset with links, hiring info, and technical relevance — ideal for job targeting or market research.

## What It Does

### 1. Web Search for Hosting Companies
- Uses Bing Search to find websites of U.S.-based web hosting providers by querying multiple industry-related terms like:
    - "independent web hosting companies USA"
    - "non-reseller hosting providers"
    - "top US-based hosting companies"
- You can expand these terms to refine your dataset.

### 2. Filters Out the Noise
- U.S.-based only: Scraper checks for "United States" or "USA" in the page text
- Not a reseller: Eliminates domains mentioning "reseller", "affiliate", "owned by", etc.
- Primary hosting provider: Avoids companies that only offer hosting as a secondary service

### 3. Extracts Useful Data From Each Valid Site
- Rank: Order in which it was found (estimated ranking)
- Company Name: Based on the domain
- Website URL: Base homepage
- Careers Page URL: If a "Jobs" or "Careers" link is found
- Remote Work Policy: Based on keywords like "fully remote", "hybrid", etc.
- Tech Stack Relevance: If the site mentions tools like AWS, Linux, Terraform, DevOps
- Application Status: Left blank for you to update manually
- LinkedIn & Twitter: Detected from social links on the homepage

### 4. Live Web Interface
- Launch a scrape with 1 click
- See real-time logs as URLs are visited, skipped, or added
- Download the final results as an .xlsx file
- Watch progress in a live browser log (via Server-Sent Events)

### 5. Outputs the Results
- output/us_hosting_companies.xlsx: The structured dataset
- output/bing_debug.html: A copy of Bing's HTML (for debugging scraping issues)

## Technology Stack
- Frontend: HTML + JavaScript (SSE for live logging)
- Backend: Python 3.11 + Flask
- Scraping: requests, BeautifulSoup, fake-useragent
- Data Processing: pandas, openpyxl
- Deployment: Fully Dockerized with Dockerfile

## Intended Use Cases
- Job Hunting: Find US-based hosting companies hiring DevOps/SRE/Cloud professionals
- Market Research: Build a real-time map of small-to-medium US web hosts
- Lead Generation: Sales research for companies serving web hosting platforms
- Resume Matching: Filter companies using a tech stack you're skilled in

## Optional Expansions
- Use SerpAPI instead of scraping Bing (faster + more reliable)
- Add a database backend to track application status
- Export to CSV or JSON
- Add pagination or filtering in the web UI
- Deploy to cloud (e.g., Fly.io, Railway, Heroku, Docker Hub + VPS)

## In Progress
- Phase 1: UI/UX Core Upgrades (Pause/Resume, Cancel, Log Filtering/Search, Theme Toggle, Custom Search Terms, Download CSV/JSON, Company Details Modal, Log Download)
- Next: Scraping/Data Quality, Analytics/Reporting, Integrations, Security/Config, Developer/Power features
- Rerun pipeline and verify that unfiltered_hosts.csv is populated with many candidates.
- Progress bar not working (backend): Completed — Backend now yields a [PROGRESS] log line for every candidate processed, ensuring the frontend progress bar always updates, even if all are skipped or rejected.
- Directory mode for WHTop/directory-mined companies: Completed — WHTop/directory-mined companies are now accepted with a much looser threshold (if 'hosting' is present or score >= 5), marked as DirectoryAccepted, greatly increasing acceptance from trusted directories.
- Dockerfile: Add Chrome/ChromeDriver for Selenium (enables HostAdvice scraping in Docker)
- Added undetected-chromedriver for HostAdvice anti-bot evasion, fetch_with_selenium now uses it and sets more human-like options.

## Completed
- Multi-engine search (Bing, Google, DuckDuckGo via SerpAPI)
- Expanded search terms for broader coverage
- Loosened US-only and disqualifier filters
- Directory/list page extraction logic
- [x] Set timeout=5s for all requests.get calls to skip slow-loading sites (Complete)
- [x] Add detailed print logging to console for all major scraper actions (Complete)
- [x] Blacklist for non-hosting domains (Complete)
- [x] Nav/product link requirement in is_hosting_company (Complete)
- [x] Deduplication by canonical domain (Complete)
- [x] Scoring breakdown in output (Complete)
- [x] Log lines for progress bar accuracy (Complete)
- [x] Loosened US-based check, only egregious disqualifiers, lower score threshold, careers page optional, detailed skip logging (Complete)
- [x] Pruned negative keyword list, lowered nav/product link and domain signal penalties, made directory extraction more permissive for hosting company acceptance (Complete)
- [x] Radically reduced negative keywords, removed generic penalties, made directory extraction more permissive, only skip for egregious disqualifiers in has_disqualifiers (Complete)
- [x] Made acceptance stricter—directory extraction now only accepts companies with score >= 10 and strong nav link, is_hosting_company requires at least two positive signals and one in heading/title, expanded egregious disqualifiers, logs all acceptances with positive signals (Complete)
- [x] Made is_hosting_company stricter—requires CTA and pricing/plans/packages, expanded aggregator/research/statistics disqualifiers, directory extraction applies same checks, all acceptances log positive signals (Complete)
- [x] Loosened acceptance—accepts if at least 2 positive signals (one in heading/title/nav) AND (CTA OR pricing/plans/packages found); expanded CTA triggers; pricing/plans/packages counted in nav text/href; directory extraction uses same logic (Complete)
- Updated scoring_pass.py: Lowered threshold, boosted weights, added rescue logic, improved review/acceptance logic.
- Loosened foundational scrape in scraper/hosting_scraper.py: removed all filtering/disqualifier logic, now saves all plausible candidates to output/unfiltered_hosts.csv for scoring phase.
- [Completed] Fixed: /output/companies.json now falls back to final_results.xlsx if companies.json is missing (see app.py)
- [Completed] Scoring softening, directory boost, maybe bucket (borderline_hosts.xlsx), multi-page analysis, Source field in output. Borderline/possible hosts now exported for human review.
- [Completed] WHTop pagination now robust—stops after 2 empty pages or max_pages=200, logs reason for stopping. No more infinite scraping at end of directory.
- [Completed] HostAdvice scraper implemented (scraper/hostadvice_scraper.py) with robust pagination and company extraction. Now used for large-scale directory mining instead of WHTop.
- [Completed] UI HostAdvice checkbox and backend integration. User can now select HostAdvice as the source and run the scrape from the web interface.
- [Completed] Fixed Flask session context bug in /scrape-stream. Session is now accessed before generator, resolving 'Working outside of request context' error and restoring UI streaming.
- Dockerfile: Add Chrome/ChromeDriver for Selenium (enables HostAdvice scraping in Docker)
- Modularized scrapers into scrapers/whtop.py and scrapers/hostadvice.py with debug HTML output and optional proxy support. Added run_directory_scrape.py.

## Follow-up Needed
- Further tuning of filters and extraction logic for edge cases 

## To Do
- Add next step: rerun pipeline and review acceptance rate. 