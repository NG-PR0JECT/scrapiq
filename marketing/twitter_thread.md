# Twitter thread — Scrapiq (5 tweets)

**1 — Hook**
Every RAG / agent project I touch re-implements the same fragile fetch → parse → clean pipeline. So I turned mine into an API.

**2 — Pain**
Scraping is annoying: headless browsers, selector debugging, HTML soup, and token-burning LLM calls just to get a page into your context. It shouldn't be this hard.

**3 — Solution**
Meet Scrapiq: one API call turns any URL into clean text, Markdown, or typed JSON. Deterministic parsing first — no browser, no selectors, no LLM required. Fast and cheap.

**4 — Proof / spec**
Ships with CLI, Node, LangChain loader, and MCP server. Free tier included. MIT licensed. → github.com/NG-PR0JECT/scrapiq

**5 — CTA**
Honest status: 0 paying customers. The product exists; the distribution doesn't. If you build RAG or agents that need clean page data, try it and tell me what breaks.
