from scrapers import whtop, hostadvice
import pandas as pd
import os


def run(log=print, max_pages:int|None=None):
    companies = []
    log("[RUN] Scraping WHTop")
    companies += whtop.fetch_all_pages(max_pages=max_pages or 10, log=log)
    log(f"[RUN] WHTop returned {len(companies)} total")
    log("[RUN] Scraping HostAdvice")
    companies += hostadvice.fetch_all_pages(max_pages=max_pages or 10, log=log)
    log(f"[RUN] Total companies combined: {len(companies)}")
    df = pd.DataFrame(companies)
    df.drop_duplicates(subset="domain", inplace=True)
    df.to_excel("output/host2me_results.xlsx", index=False)
    df.to_json("output/host2me_results.json", orient="records", force_ascii=False)
    log("[RUN] Results saved to output/host2me_results.xlsx/json")


if __name__ == "__main__":
    max_pages = int(os.environ.get("HOST2ME_MAX_PAGES", "10"))
    run(max_pages=max_pages)
