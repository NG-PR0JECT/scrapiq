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

## Benchmarks

Measured on 23 live pages (two page sets, two consecutive days) against
`trafilatura`, `readability-lxml`, `MarkItDown` and a raw-HTML baseline. Method,
per-page numbers, raw JSON and caveats live in
[**scrapiq-bench**](https://github.com/NG-PR0JECT/scrapiq-bench):

| | median chars | median ms (cold) |
|---|---:|---:|
| raw HTML | 105,845 | 97 |
| trafilatura (the same call Scrapiq makes) | 4,449 | 253 |
| **Scrapiq (HTTP API)** | **6,648** | **411** |
| readability-lxml | 3,814 | 217 |
| MarkItDown | 17,205 | 414 |

Scrapiq runs trafilatura underneath — the extra ~0.16 s of median latency is the
round trip and the server-side fetch. What it buys back:

- On **23/23** pages the API returned at least as much text as the bare library
  called with identical kwargs, and more on 17/23.
- On a forum front page it recovers **+32 links** the extractor dropped (reproduced
  on both days, +2,876 and +3,281 chars respectively).
- On the Apache licence page the bare library call returns **0 characters** with no
  error, while the API returns 9,354 — its BeautifulSoup fallback fires when the
  parser comes back empty.

`readability-lxml` returned under 200 characters on 2/23 pages without raising an
error, and `MarkItDown` carried 4+ boilerplate markers on 4/23 (`8 markers / 58,237
chars` on one news front vs `0 / 4,068` for Scrapiq). One of the pages in the first
set exposed a link-corruption bug in Scrapiq's markdown pass, fixed in `7775cca`.

## Ecosystem

Official client libraries and integrations (all MIT):

- [scrapiq-cli](https://github.com/NG-PR0JECT/scrapiq-cli) — dependency-free CLI (`pip install scrapiq`)
- [scrapiq-node](https://github.com/NG-PR0JECT/scrapiq-node) — dependency-free TypeScript/Node client
- [scrapiq-python](https://github.com/NG-PR0JECT/scrapiq-python) — official Python client (sync + async)
- [scrapiq-langchain-loader](https://github.com/NG-PR0JECT/scrapiq-langchain-loader) — LangChain `DocumentLoader`
- [scrapiq-mcp-server](https://github.com/NG-PR0JECT/scrapiq-mcp-server) — MCP server for Claude/Cursor/agent tools

## License

MIT — see LICENSE.
