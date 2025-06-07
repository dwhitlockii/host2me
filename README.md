# Host2Me

This project scrapes hosting company data and provides a small Flask interface
to run the scraper. Results can optionally be stored in a MongoDB database when
using Docker Compose. A Dockerfile is included for running either the web UI or
the full data pipeline.

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
# Or start everything with Docker Compose
docker compose up --build


Set `SERPAPI_KEY` in the environment if you have a SerpAPI account for
search results.

## Configuration

Several environment variables allow you to tune how the scraper behaves:

- `SERPAPI_KEY` – API key for SerpAPI. When provided, search engine results from Bing/Google are used in addition to directory mining.
- `HOST2ME_MAX_PAGES` – limits how many pages of the WHTop directory are scraped. Defaults to 10.
- `SHOW_BROWSER` – set to `1` to display the Chrome window when the HostAdvice scraper runs (useful for debugging).
- `MONGO_URI` – MongoDB connection string (default `mongodb://mongo:27017`).
- `MONGO_DB` – database name (default `host2me`).
- `SAVE_HTML` – set to `0` to skip saving visited page HTML.

The web interface also includes a **Use HostAdvice directory** checkbox.
Enabling it switches the scraper to the HostAdvice source instead of the
default WHTop directory mode.

## Troubleshooting

### Docker reports `exec ./entrypoint.sh: no such file or directory`

If you build the image on Windows, Git may convert `entrypoint.sh` to
Windows line endings (CRLF). The container expects Unix line endings and
will fail to execute the script with the above error. Convert the file to
LF before building or disable line ending conversion:

```bash
git config --global core.autocrlf false
git checkout -- entrypoint.sh
```

After ensuring the script uses LF endings, rebuild the Docker image and the
container will start correctly.

