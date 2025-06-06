# Code Index

## Files and Structure

- app.py: Flask app, routes for index, scrape-stream (SSE), and download. Uses stream_hosting_scraper from scraper/hosting_scraper.py.
- scraper/hosting_scraper.py: Main scraping logic. Functions: search_hosting_companies (now uses Bing, Google, DuckDuckGo via SerpAPI, with expanded search terms and directory extraction), extract_company_info, extract_companies_from_directory, stream_hosting_scraper, etc. Filters/logic loosened (US-based check, only egregious disqualifiers, lower score threshold, careers page optional, detailed skip logging)
- requirements.txt: Python dependencies for the app and scraper.
- Dockerfile: Containerizes the app for deployment. Installs dependencies, exposes port 5000, runs app.py. Now installs Google Chrome and ChromeDriver for Selenium-based scraping. HostAdvice scraping now works in Docker.
- templates/index.html: Web UI. Button to start scrape, live log via SSE, download link.
- output/: Directory for generated Excel and debug HTML files.
- run_directory_scrape.py: runs modular scrapers and writes combined host2me_results.xlsx/json.
- hosting_scraper_verbose.py: Alternate or verbose version of the scraper (not used by Flask app directly).
- DOMAIN_BLACKLIST: skips known non-hosting/social/review/aggregator domains
- is_hosting_company: now accepts if at least 2 positive signals (one in heading/title/nav) AND (CTA OR pricing/plans/packages found); expanded CTA triggers; pricing/plans/packages counted in nav text/href; directory extraction uses same logic
- has_disqualifiers: egregious disqualifiers expanded
- Deduplication: companies deduped by canonical domain (netloc, lowercased, no www.)
- Scoring breakdown: saved for each site in output and Excel/JSON
- scrapers/whtop.py: modular WHTop scraper. fetch_all_pages() handles pagination via /page/<n>, saves debug HTML.
- scrapers/hostadvice.py: modular HostAdvice scraper using requests or Selenium fallback, debug HTML dumps.
- utils/browser.py: helper to create Selenium drivers with optional proxy and wait utilities.

## Key Functions/Relationships

- app.py imports stream_hosting_scraper from scraper/hosting_scraper.py
- stream_hosting_scraper() yields log lines for SSE, now including a [PROGRESS] log for every candidate processed (for frontend progress bar reliability)
- search_hosting_companies() performs Bing search and filtering
- extract_company_info() parses and extracts company data
- index.html uses EventSource to stream logs from /scrape-stream
- Dockerfile builds and runs the Flask app
- All requests.get calls in scraper/hosting_scraper.py and hosting_scraper_verbose.py now use timeout=5s
- All major scraper actions now print detailed logs to the console for real-time visibility in server logs
- is_hosting_company now requires at least 2 keyword matches and at least one in a heading or title for a site to be considered a hosting company

# scoring_pass.py
- Constants: ACCEPT_THRESHOLD, RESCUE_THRESHOLD
- Functions: score_row(row), count_strong_signals(row, snippets, links)
- Logic: Boosted weights for tech/contextual/behavioral signals, rescue logic for borderline sites, aggregate signals, improved review/acceptance logic.

- is_hosting_company and extract_company_info: now support a 'directory mode' (from_directory=True) for trusted sources like WHTop, accepting with minimal signal and marking as DirectoryAccepted 

- /output/companies.json endpoint (in app.py) now falls back to output/final_results.xlsx if companies.json is missing, converting Excel to JSON on the fly. 

- is_hosting_company, extract_company_info, extract_companies_from_directory: scoring softening, directory boost, maybe bucket (borderline_hosts.xlsx), multi-page analysis, Source field in output 

- get_whtop_us_companies in whtop_scraper.py now stops after 2 empty pages or max_pages=200, logging the reason. No more infinite/pointless scraping.

- UI (index.html) now has a HostAdvice checkbox. app.py and stream_hosting_scraper support 'hostadvice' mode, enabling HostAdvice scraping from the web UI. 