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

