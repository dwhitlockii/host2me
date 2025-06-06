# Refactor Queue

- [ ] Ensure all documentation (project_state.md, code_index.md) stays in sync with future code changes 
- [ ] Refactor to remove legacy Bing scraping once SerpAPI is confirmed stable and reliable 
- [ ] Further tune filters and directory extraction logic for edge cases and false positives 
- [ ] Review if 5s timeout is optimal for all target sites; adjust if needed for edge cases
- [ ] Further tune is_hosting_company for edge cases; consider using external hosting company lists or APIs for validation
- [ ] Further tune blacklist, nav/product link logic, and scoring for edge cases
- [x] Loosened filters and scoring logic: US-based check more permissive, only egregious disqualifiers skip, lower score threshold, careers page optional, detailed skip logging
- [x] Pruned negative keyword list, lowered nav/product link and domain signal penalties, made directory extraction more permissive for hosting company acceptance
- [x] Radically reduced negative keywords, removed generic penalties, made directory extraction more permissive, only skip for egregious disqualifiers in has_disqualifiers
- [x] Made acceptance stricter—directory extraction now only accepts companies with score >= 10 and strong nav link, is_hosting_company requires at least two positive signals and one in heading/title, expanded egregious disqualifiers, logs all acceptances with positive signals
- [x] Made is_hosting_company stricter—requires CTA and pricing/plans/packages, expanded aggregator/research/statistics disqualifiers, directory extraction applies same checks, all acceptances log positive signals
- [x] Loosened acceptance—accepts if at least 2 positive signals (one in heading/title/nav) AND (CTA OR pricing/plans/packages found); expanded CTA triggers; pricing/plans/packages counted in nav text/href; directory extraction uses same logic
- [ ] Review acceptance rate after rerun of updated scoring_pass.py; further tune weights if too many/few hosts are accepted. [timestamp]

# Multi-Phase Enhancement Queue

## Phase 1: UI/UX Core Upgrades (In Progress)
- [ ] Pause/Resume Scrape Button
- [ ] Cancel Scrape Button
- [ ] Live Filtering/Search in Log
- [ ] Dark/Light Theme Toggle
- [ ] Custom Search Terms Input
- [ ] Export to CSV/JSON
- [ ] Company Details Modal
- [ ] Download Debug Log

## Phase 2: Scraping/Data Quality
- [ ] Duplicate Detection
- [ ] Company Logo Extraction
- [ ] Advanced Filtering Options (user-set filters)
- [ ] Concurrent Requests
- [ ] Retry on Failure
- [ ] Proxy/Rotating User-Agent Support
- [ ] Progressive Saving

## Phase 3: Analytics/Reporting
- [ ] Summary Charts (pie/bar)
- [ ] Historical Run Comparison

## Phase 4: Integrations
- [ ] Google Sheets/Airtable Integration
- [ ] Webhook/Email Notification

## Phase 5: Security/Config
- [ ] Password-Protect the UI
- [ ] Environment Variable Editor

## Phase 6: Developer/Power Features
- [ ] API Endpoint
- [ ] Raw HTML Download

[TODO][{timestamp}] Consider unifying all company exports to always write companies.json after every scrape/export, to avoid frontend fallback logic. (No immediate refactor needed for current bugfix.)

[TODO][{timestamp}] Periodically review borderline_hosts.xlsx and consider automating deeper crawl or human-in-the-loop review for borderline/possible hosts.

[TODO][{timestamp}] WHTop pagination now robust, but HostAdvice still needs similar logic for multi-page scraping and stop conditions.

[TODO][{timestamp}] Consider adding TrustPilot, Capterra, and G2 scrapers for even richer hosting company datasets. HostAdvice now primary directory source; WHTop scraping deprecated due to anti-bot pagination.

[2025-06-06] HostAdvice anti-bot evasion improved with undetected-chromedriver and more human-like Selenium options. No refactor needed unless further blocks occur. 