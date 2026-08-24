# Show HN: Scrapiq — URL → clean structured data, one API call

Hey HN,

I built Scrapiq, a dead-simple extraction API that turns any URL into clean
text, Markdown, or typed JSON — no headless browser, no selector debugging,
no LLM required.

The pitch: you give it a URL and a JSON schema, it gives you structured data
back. Deterministic parsing runs first (rowspan/colspan grid expansion,
footnote ref/def resolution), so it is fast and cheap — not another
"spray tokens at the page" tool.

Why I built it: every RAG / agent project I touched re-implemented the same
fragile fetch → parse → clean pipeline. Scrapiq is that pipeline as a hosted
API plus official clients (CLI, Node, LangChain loader, MCP server).

Quick example:

    curl -s https://scrapiq.io/v1/extract \
      -H "X-API-Key: $SCRAPIQ_KEY" \
      -H "Content-Type: application/json" \
      -d '{"url": "https://example.com", "format": "markdown"}'

Three tiers with a free plan. Checkout runs in test mode while I wire up real
billing — signup works today.

MIT licensed. Repo: https://github.com/NG-PR0JECT/scrapiq

Honest status: 0 paying customers, 0 MRR. The product exists; distribution
doesn't yet. If you build RAG or agents that need reliable page data, I'd love
feedback on the API surface.

— Nathan
