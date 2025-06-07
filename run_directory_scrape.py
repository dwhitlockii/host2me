from scrapers import (
    whtop,
    hostadvice,
    hostingadvice_com,
    techradar,
    capterra,
    g2,
    reddit_miner,
    open_directories,
    search_queries,
)
import pandas as pd
import os


def run(log=print, max_pages:int|None=None):
    companies = []
    log("[RUN] Scraping WHTop")
    companies += whtop.fetch_all_pages(max_pages=max_pages or 10, log=log)
    log(f"[RUN] WHTop returned {len(companies)} total")
    log("[RUN] Scraping HostAdvice")
    companies += hostadvice.fetch_all_pages(max_pages=max_pages or 10, log=log)
    log("[RUN] Scraping HostingAdvice")
    companies += hostingadvice_com.fetch_companies(log=log)
    log("[RUN] Scraping TechRadar")
    companies += techradar.fetch_companies(log=log)
    log("[RUN] Scraping Capterra")
    companies += capterra.fetch_companies(log=log)
    log("[RUN] Scraping G2")
    companies += g2.fetch_companies(log=log)
    log("[RUN] Mining Reddit threads")
    companies += reddit_miner.fetch_companies(log=log)
    log("[RUN] Scraping Open Directories")
    companies += open_directories.fetch_companies(log=log)
    log("[RUN] Running targeted search queries")
    companies += search_queries.fetch_companies(log=log)
    log(f"[RUN] Total companies combined: {len(companies)}")
    df = pd.DataFrame(companies)
    df.drop_duplicates(subset="domain", inplace=True)
    df.to_excel("output/host2me_results.xlsx", index=False)
    df.to_json("output/host2me_results.json", orient="records", force_ascii=False)
    log("[RUN] Results saved to output/host2me_results.xlsx/json")


if __name__ == "__main__":
    max_pages = int(os.environ.get("HOST2ME_MAX_PAGES", "10"))
    run(max_pages=max_pages)
