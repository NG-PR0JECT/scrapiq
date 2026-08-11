# Scrapiq

> Turn any URL into clean, structured JSON for LLM/RAG pipelines.
> Live at: **https://scrapiq.io**

Scrapiq is a lightweight, open-source HTTP API that fetches a web page and
returns either:

- **Clean text** — boilerplate stripped (nav, ads, footer, scripts)
- **Clean markdown** — same, with links preserved
- **Structured JSON** — fields extracted from the page according to a
  JSON schema you provide (e.g. `{ "price": "number", "title": "string" }`)

Built for RAG ingestion, fine-tuning dataset generation, and any LLM
pipeline that needs clean source data without HTML noise.

## Hosted endpoint

```
POST https://scrapiq.io/v1/extract
```

Public, no auth required for v0.1. See [Usage](#usage) below.

## Quick start (self-hosted)

```bash
git clone https://github.com/NG-PR0JECT/scrapiq.git
cd scrapiq
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

scrapiq              # starts on http://localhost:8001
```

## Usage

### 1. Clean markdown

```bash
curl -X POST https://scrapiq.io/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "format": "markdown"
  }'
```

### 2. Structured extraction

```bash
curl -X POST https://scrapiq.io/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.ycombinator.com",
    "format": "json",
    "schema": {
      "properties": {
        "title":   {"type": "string"},
        "headline":{"type": "string"},
        "rank":    {"type": "integer"}
      }
    }
  }'
```

### 3. Plain text

```bash
curl -X POST https://scrapiq.io/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "format": "text"}'
```

## Python

```python
import httpx

response = httpx.post(
    "https://scrapiq.io/v1/extract",
    json={
        "url": "https://example.com",
        "format": "markdown",
    },
)
markdown = response.json()["content"]
```

## Use cases

- **RAG ingestion** — Clean text/markdown ready for chunking and embedding
- **Fine-tuning data** — Bulk extract structured fields from content sites
- **Web monitoring** — Re-scrape on a schedule and get JSON diffs
- **Comparison scraping** — Pull prices, names, dates from multiple URLs

## How it works

```
URL → httpx fetch → trafilatura clean → optional structure extraction → JSON
```

- **httpx** for HTTP (async, timeout, redirect handling)
- **trafilatura** for boilerplate removal (state-of-the-art open-source)
- **BeautifulSoup** for metadata extraction (title, description, OG tags)
- **Custom regex** for v0.1 structured extraction (no LLM call needed)

## Roadmap

- [x] v0.1 — Core extraction (text, markdown, schema-based JSON)
- [ ] v0.2 — LLM-backed extraction (user provides their OpenAI key)
- [ ] v0.3 — Caching layer (Redis/in-memory)
- [ ] v0.4 — Bulk URLs in one request
- [ ] v0.5 — JavaScript rendering (Playwright/Chromium)
- [ ] v1.0 — Hosted SaaS with usage-based pricing

## Architecture

This is a **self-hosted, open-source** project. You run it on your own
infrastructure. No telemetry, no data leaves your network.

The HTTP API is in `src/main.py`. The core extraction pipeline is in
`src/extract.py`. Schemas are in `src/schemas.py`.

## License

MIT — see LICENSE.
