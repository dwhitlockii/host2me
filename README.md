# Host2Me

This project scrapes hosting company data and provides a small Flask
interface to run the scraper. A Dockerfile is included for running either
the web UI or the full data pipeline.

## Quick Start

```bash
# Build the container
docker build -t host2me .

# Run the web UI (default)
docker run -p 5000:5000 host2me

# Run the full scraping pipeline
# writes results under the container's /app/output folder
# (mount a volume to retrieve them)
docker run -e MODE=pipeline host2me
```

Set `SERPAPI_KEY` in the environment if you have a SerpAPI account for
search results.

## Configuration

Several environment variables allow you to tune how the scraper behaves:

- `SERPAPI_KEY` – API key for SerpAPI. When provided, search engine
  results from Bing/Google are used in addition to directory mining.
- `HOST2ME_MAX_PAGES` – limits how many pages of the WHTop directory are
  scraped. Defaults to 10.
- `SHOW_BROWSER` – set to `1` to display the Chrome window when the
  HostAdvice scraper runs (useful for debugging).

The web interface also includes a **Use HostAdvice directory** checkbox.
Enabling it switches the scraper to the HostAdvice source instead of the
default WHTop directory mode.

