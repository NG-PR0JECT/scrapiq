# Scrapiq — Daily Log

Track acquisition actions and learnings per day.


## 2026-08-07 (Day 1)

**Metrics:** health OK, v0.1.0, cache_size 0. Repo: 0 stars, no releases.

**Emails (5/5 sent via SMTP2GO):**
- tangchenming@stu.pku.edu.cn (Select-And-Extract, PKU)
- rashid@cocoonlab.ai (construction doc evidence extraction)
- baoweidong293@gmail.com (MEGRAG)
- jiachengtao@buaa.edu.cn (DualG-MRAG)
- enril.wentao@std.uestc.edu.cn (cross-document event benchmark)
- Sender: noreply@watchedapi.com (only verified SMTP2GO domain; scrapiq.io NOT verified → dashboard action needed)

**GitHub (1 action):** Commented on firecrawl/firecrawl#3817 (extraction quality for RAG) — technical value on rowspan/colspan grid expansion + footnote ref/def handling, one-line Scrapiq mention. https://github.com/firecrawl/firecrawl/issues/3817#issuecomment-5213361654

**Pipeline built:**
- prospects.jsonl: 36 unique papers, 8 with real emails (arXiv PDF extraction, email_extract.py)
- scrape_arxiv.py → email_extract.py → dedupe_prospects.py → send_day1.py
- Blockers/notes: GitHub stargazers API 404 (all repos) + token lacks user:email scope → email discovery via arXiv PDFs instead. execute_code blocked in cron mode.

**Next:** rotate GitHub action (issue/discussion/awesome-list), run arXiv scrape daily for fresh prospects, verify scrapiq.io SMTP2GO sender (needs Nathan dashboard).

## 2026-08-08 (Day 2)

**Metrics:** health OK, v0.1.0, cache_size 0. Repo: 0 stars.

**Emails (5/5 sent via SMTP2GO):**
- weitong@outlook.com (Zijian Wang — PURPOSE poisoning conflict resolution in RAG)
- chenchong55@huawei.com (Lang Mei — SearchArt search agent training)
- cl.liu99@foxmail.com (Chengliang Liu — inference cost attacks for RAG)
- jm2245@cam.ac.uk (Jingbiao Mei — EReL@MIR multimodal document retrieval)
- torkian@email.sc.edu (Ben Torkian — safety-constrained LLM for public health)
- Sender: noreply@watchedapi.com (still the only verified SMTP2GO domain — scrapiq.io pending)

**GitHub (1 action — micro-tool sibling):** Created https://github.com/NG-PR0JECT/scrapiq-langchain-loader — LangChain DocumentLoader for Scrapiq (text/markdown/json, multi-URL, live-API tested 4/4). Compounding backlink to main repo.

**Pipeline:** prospects now 16 with emails. email_extract.py updated 8 more today. arXiv scrape dedup'd (0 new — same queries; rotate queries tomorrow).

**Notes:** gh push in headless cron needs `gh auth setup-git` + token-in-URL push (empty credential helper entries break plain push). Repo branch was `master` → renamed `main`.

**Next:** rotate GitHub action (issue on Crawl4AI/Apify or awesome-list PR), vary arXiv queries for fresh prospects, verify scrapiq.io SMTP2GO sender (needs Nathan dashboard).

## 2026-08-09 (Day 3)

**Metrics:** health OK, v0.1.0, cache_size 0. Repo: 0 stars.

**Emails (5/5 sent via SMTP2GO):**
- said.elnaffar@gmail.com (Said Elnaffar — agent-ready websites, machine readability)
- zhaochenxu@mininglamp.com (Chenxu Zhao — WebRetriever benchmark for web agent eval)
- yujinz16@uci.edu (Yujin Zhang — HANSEL breadcrumbs from web agent trajectories)
- xiangle@baidu.com (Le Xiang — DocTrace long-doc VQA)
- mmansoor7755@stu.jejunu.ac.kr (Muhammad Mansoor — freshness-aware caching for open-web RAG)
- Sender: noreply@watchedapi.com (still only verified SMTP2GO domain — scrapiq.io pending Nathan dashboard)

**GitHub (1 action — awesome-list PR):** https://github.com/Danielskry/Awesome-RAG/pull/141 — added Scrapiq to "Frameworks that Facilitate RAG" (next to Kreuzberg). Fork NG-PR0JECT/Awesome-RAG, 1-line README entry. Token-in-URL push needed again (empty credential helper).

**Pipeline:** Rotated arXiv queries (html2markdown, doc_parsing, web_agent, crawl_rag, structured_data, dataset_build) → 243 new prospects, 7 more emails extracted (47 total ready). Email targets this round all web-agent/RAG-relevant — best batch yet. Note: scrape_arxiv_day3.py needs urllib.parse.quote for query strings.

**Next:** rotate GitHub action (issue on Crawl4AI/Apify), fresh arXiv scrape next round, verify scrapiq.io SMTP2GO sender (needs Nathan dashboard).

## 2026-08-11 (Day 5)

**Metrics:** health OK, v0.1.0, cache_size 0. Repo: 0 stars. (Day 4 was missed — send_day4.py prepared Aug 10 but never executed.)

**Emails (5/5 sent via SMTP2GO, day-4 targets caught up):**
- mohammadreza.rashidi@ue-germany.de (Structural Role Injection in Handlebars LLM prompts)
- arijitk@bgsu.edu (LLMs+Graphs survey)
- spyros.mauromatis@athenarc.gr (Ancient Greek→Modern MT corpus)
- benakouche@isir.upmc.fr (TargetFinder widgets from pixels)
- nathan.bout@hcompany.ai (DragOn drag-GUI benchmark)
- Sender: noreply@watchedapi.com (still only verified SMTP2GO domain — scrapiq.io pending Nathan dashboard)

**GitHub (1 action — helpful comment):** Commented on unclecode/crawl4ai#2110 (PruningContentFilter corrupts code blocks in fit_markdown). Added: silent-corruption risk for RAG ingestion + preserve_tags tradeoff analysis, one-line Scrapiq mention. https://github.com/unclecode/crawl4ai/issues/2110#issuecomment-5249696374

**Pipeline:** Rotated arXiv queries (llm_reading, html_table, long_doc, search_agent, open_web, content_harvest) → 185 new prospects, 3 more emails extracted (63 total ready). email_extract needs the scrapiq venv python (pypdf not in system python).

**Next:** fresh targets from day-5 batch for tomorrow, rotate GitHub action (micro-tool #2: scrapiq-mcp-server or scrapiq-cli), verify scrapiq.io SMTP2GO sender (needs Nathan dashboard).

## 2026-08-11 (Day 4 — DNS live)

**Setup prod:**
- DNS Cloudflare: A records `scrapiq.io` + `www.scrapiq.io` → 51.91.121.110 (DNS-only, token API dans /tmp/éphémère — pas persisté).
- Nginx site config: `/etc/nginx/sites-available/scrapiq.io` proxy :443 → 127.0.0.1:8001. Redirect 80→443.
- SSL: certbot Let's Encrypt (HTTP-01 challenge), auto-renew toutes les 12h via systemd timer.
- Tests bout-en-bout OK : https://scrapiq.io/health répond `{"status":"ok","version":"0.1.0"}`, https://scrapiq.io/v1/extract retourne markdown propre.

**Sender SMTP2GO:** reste `noreply@watchedapi.com` car `scrapiq.io` pas encore vérifié dans dashboard SMTP2GO. Action Nathan: ajouter le domaine dans SMTP2GO dashboard + DKIM/SPF. Une fois fait, change `SCRAPIQ_SENDER_EMAIL=noreply@scrapiq.io` dans l'env du daily-report.

**README update:** https://scrapiq.io mentionné dans le README public, push commit `b406054`.

**Note sécurité:** token Cloudflare était dans un shell éphémère (variable d'env de la commande), pas sauvegardé. Pour les futurs ajouts, Nathan regénère un token dédié à la demande.

## 2026-08-11 (Day 4 — DNS live) — SUITE

**DNS Cloudflare final:**
- A records: scrapiq.io + www.scrapiq.io → 51.91.121.110 (DNS-only)
- CNAME records (créés par Nathan dans SMTP2GO dashboard): em673977, link, s673977._domainkey
- SPF (créé par ce script): scrapiq.io → "v=spf1 include:smtp2go.com ~all"
- DMARC (créé par ce script): _dmarc.scrapiq.io → "v=DMARC1; p=none; rua=mailto:nathan.guyon51@gmail.com"

**SSL:** Let's Encrypt via certbot. Auto-renew OK.

**API en prod:** https://scrapiq.io/v1/extract répond. Health https://scrapiq.io/health = ok.

**Sender SMTP2GO:** "From header sender domain not verified (scrapiq.io)" — le SPF/DKIM sont posés mais il manque probablement le TXT de vérification SMTP2GO (`smtp2go-verify=xxx`) que Nathan doit copier depuis le dashboard SMTP2GO → Verified Senders → scrapiq.io et me coller pour l'ajouter via `cf_email_dns.py`.

En attendant: tous les mails partent depuis noreply@watchedapi.com (sender vérifié legacy). Action future: basculer `SCRAPIQ_SENDER_EMAIL=noreply@scrapiq.io` quand SMTP2GO accepte.

## 2026-08-11 — Sender verified

`noreply@scrapiq.io` accepted by SMTP2GO. `scrapiq_secrets.SENDER_EMAIL` default updated to this address. Future emails will use this sender automatically.

## 2026-08-12 (Day 6)

**Metrics:** health OK, v0.1.0, cache_size 0 (local + https://scrapiq.io). Repo: 1 star (first!).

**Emails (5/5 sent via SMTP2GO — FIRST DAY WITH VERIFIED SENDER `noreply@scrapiq.io`):**
- alberto.castagnaro@unipd.it (RAG data loader attacks — defensive angle: deterministic extraction narrows injection surface)
- heconghui@pjlab.org.cn (AICC 7.3T HTML corpus — Scrapiq automates HTML cleanup for corpus building)
- kangzhi.zhao@outlook.com (WebSwarm multi-agent web search — clean page representation per agent step)
- hguo246@wisc.edu (social-web prompt injection in RAG — boilerplate stripping shrinks injection window)
- zhuchenyang.liu@aalto.fi (evidence attribution in visual doc understanding — structured extraction preserves doc structure)
- Sender: noreply@scrapiq.io verified (11/08; scrapiq_secrets.SENDER_EMAIL default now used)

**GitHub (1 action — micro-tool #2):** Created https://github.com/NG-PR0JECT/scrapiq-mcp-server — dependency-free MCP stdio server (JSON-RPC 2.0, Python stdlib only) exposing `scrapiq_extract(url, format, max_chars)`. Tests: handshake, tools/list, missing-url isError, live extraction vs local API — all PASS. Compatible with Claude Desktop/Cursor via claude_desktop_config.json. Compounding backlink to main repo.

**Pipeline:** Rotated arXiv queries (extraction_quality, html_to_text, clean_text, document_loader, web_understanding, rag_ingestion) → 100 new prospects. Day-6 targeted email extraction (email_extract_day6.py) → 7 fresh emails incl. 3 goldmine papers (ReaderLM-v2 @jina.ai, AICC HTML corpus, RAG loader attacks). Dedup collapsed per-author lines → 135 unique papers, 20 contacted, 15 ready. Sent-emails integrity verified (0 lost).

**Next:** rotate GitHub action (issue on Crawl4AI/Apify or scrapiq-cli micro-tool), fresh arXiv scrape next round, consider emailing Jina ReaderLM-v2 team (research@jina.ai) — strongest remaining prospect.

## 2026-08-13 (Day 7)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0.

**GitHub (1 action — helpful comment):** Commented on unclecode/crawl4ai#2125 (preserve_tags/preserve_classes no-op for excluded tags: aside/nav/footer/header/form). Verified bug still on `develop`, gave minimal 2-line fix (consult `_is_preserved()` inside `_remove_unwanted_tags` before `decompose()`), flagged the silent-failure RAG danger + `negative_patterns` caveat. One-line Scrapiq mention. https://github.com/unclecode/crawl4ai/issues/2125#issuecomment-5276717824

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- research@jina.ai (ReaderLM-v2 — goldmine: same domain, builder-to-builder angle, invited their take)
- zhuoxie.uon@gmail.com (Zhuo Xie — cross-platform epistemic verification for AI news summaries — deterministic extraction stabilizes claim-checking input)
- safwan@misraj.ai (Safwan AlModhayan — Wasm Arabic multimodal corpora — automates HTML→clean JSON for corpus building)
- kchoudh2@jhu.edu (Kamal Choudhary — Hallucination Detector LLM+Semantic Scholar — clean source parsing for fact checking)
- hanncie@outlook.com (Hanxi Li — CHaystack Chinese doc retrieval/VQA — normalized ingestion layer)
- Names pulled from arXiv API metadata (real author names, not guessed).

**Pipeline:** Rotated arXiv queries (url_extraction, web_scraping_llm, html_parser_rag, document_parsing, web_corpus_clean, structured_extraction) → 179 new prospects (135→314). Email extraction from fresh PDFs: +22 emails (57 ready total) — highlights: NovaLAD (CPU-optimized doc extraction), French PDF-to-Markdown (Probayes), HiPerRAG (ANL), SomaliWeb (web corpus), DataParasite (data curation), WIST (web-grounded RAG). Sent-emails integrity verified: 30 entries, 0 dupes, 0 missing IDs.

**Next:** rotate GitHub action (scrapiq-cli micro-tool — 3rd in series, or awesome-mcp-servers PR since scrapiq-mcp-server exists now), send day-8 batch from fresh extraction, consider following up with Jina team if they reply.

## 2026-08-15 (Day 8)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0. Repo: 1 star.

**GitHub (1 action — micro-tool #3):** Created https://github.com/NG-PR0JECT/scrapiq-cli — dependency-free CLI for the Scrapiq API (stdlib urllib only, Python 3.8+, pip-installable as `scrapiq` command). text/markdown/json formats, schema shorthand auto-normalized (`{"title":"string"}` → `{"type":"string"}`), client-side `--max-chars` truncation (server ignores the param — noted), `--full` response, `--api` override for self-hosted. Tested live: text ✅, markdown (links preserved) ✅, full JSON ✅, schema ✅, HTTP 422/500 errors handled with exit 1. Also surfaced a server bug: bare-string schema values crash the API (`'str' object has no attribute 'get'`) — worth hardening in main.py later.

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- bruno.rigal@probayes.com (Bruno Rigal — VLM benchmark French PDF→Markdown; perfect fit, French author, deterministic complement angle)
- connectamanulla@gmail.com (Aman Ulla — NovaLAD CPU-optimized doc extraction; same-layer complement)
- ramanathana@anl.gov (Arvind Ramanathan — HiPerRAG; verified last author of 24, email NOT Ozan Gokdemir)
- msun@cshl.edu (Mengyi Sun — DataParasite online data curation)
- zhouxuanhe@sjtu.edu.cn (Xuanhe Zhou — MinerU-Popo structured doc parsing; verified email belongs to Zhou not first author Xu)
- Names verified against arXiv author lists this round (2 corrections) — lesson: always check citation_author before greeting.

**Pipeline:** Rotated arXiv queries (web_to_markdown, content_extraction, ai_agents_url, rag_document, scraping_benchmark, fact_checking) → +134 prospects (164→298). Email extraction from fresh PDFs: +19 emails (76 with email total, 21 ready after today's send). Highlights: MDEval (markdown-aware LLMs), webMCP (agent-ready web), DeCoRAG (complex-doc RAG), Calibrated Selective Fact-Checking.

**Next:** rotate GitHub action (awesome-mcp-servers PR — scrapiq-mcp-server qualifies, or issue on Crawl4AI/Apify), send day-9 batch from fresh pool (MDEval/webMCP/DeCoRAG top picks), harden main.py schema validation (server 500 on bare-string schema).

## 2026-08-16 (Day 9)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0. Repo: 1 star.

**GitHub (1 action — awesome-list PR):** https://github.com/punkpeye/awesome-mcp-servers/pull/12249 — added NG-PR0JECT/scrapiq-mcp-server to "Search & Data Extraction" section (top of section, per recent-adds pattern). Fork NG-PR0JECT/awesome-mcp-servers, 1-line README entry, agent marker 🤖🤖🤖 in PR title (repo fast-tracks agent PRs). Token-in-URL push needed (empty credential helper again — `gh auth setup-git` doesn't fix plain push in headless cron).

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- zpchen@swufe.edu.cn (Zhongpu Chen — MDEval markdown awareness; input-side clean markdown angle)
- yichuan_wang@berkeley.edu (Yichuan Wang — PIXELRAG screenshots-vs-text; text baseline quality angle)
- wangshuo@qiyuanlab.com (Shuo Wang — DeCoRAG complex-doc understanding; clean source input angle)
- arnold.overwijk@microsoft.com (Arnold Overwijk — ClueWeb22 10B web docs; corpus cleanup at scale)
- ydil_005@hotmail.com (D. Perera — webMCP agent-ready web; normalized page representation for agents)
- All names verified against arXiv author lists via export.arxiv.org id_list query (0 corrections this round).

**Notes:** awesome-mcp-servers CONTRIBUTING explicitly welcomes automated-agent PRs (`🤖🤖🤖` suffix = fast-track merge) — good discovery, reuse for future MCP-related additions. Checked lorien/awesome-web-scraping first (8.1k★): python.md is library-only (no services/API section), so MCP list was the better fit.

**Next:** rotate GitHub action (issue on Crawl4AI/Apify, or Discussion on LangChain community integrations proposing Scrapiq DocumentLoader), send day-10 batch from fresh pool (webMCP/DeCoRAG sent; next: PIXELRAG-adjacent or WIST/SomaliWeb corpus people), consider follow-up on the awesome-mcp-servers PR in ~1 week if unmerged.
## 2026-08-17 (Day 10)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0. Repo: 1 star.

**GitHub (1 action — helpful comment):** Commented on ScrapeGraphAI/Scrapegraph-ai#1120 (SmartScraperGraph returns confident false negatives when answer is on a linked page — compliance-style extraction). Added the deterministic-retrieval-before-LLM-judgment pattern behind the reporter's baseline, sharpened suggestion (2) to intent-bearing link targets (privacy/terms/policy/team/about/pricing), one-line honest Scrapiq mention + offer to share link-following heuristics. https://github.com/ScrapeGraphAI/Scrapegraph-ai/issues/1120#issuecomment-5312523008

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- gunhee@snu.ac.kr (Gunhee Kim — Weasel web-agent OOD dataset curation; page normalization for training data)
- gubanov@cs.fsu.edu (Michael Gubanov — CancerKG web-scale verifiable KG; self-hostable extraction at scale)
- ahwang16@seas.upenn.edu (Alyssa Hwang — NewsQs multi-source QG; article normalization across outlets)
- ttn0011@auburn.edu (Tin Nguyen — PageGuide webpage navigation; clean structural read for locating info)
- blake.fitch@tuebingen.mpg.de (Blake G. Fitch — NL access to domain metadata; schema-based extraction)
- All names verified against arXiv citation_author lists (Weasel: email = Gunhee Kim, last author — not first author Zadeh).

**Pipeline:** Rotated arXiv queries (data_extraction_llm, web_readability, browser_agent_content, html_semantic, rag_ingestion_web, corpus_quality) → +138 prospects (218 lines now; dedup collapsed per-author lines, 76→95 with email). Email extraction from fresh PDFs: +19 emails. Sent-emails integrity verified: 45 entries, 0 dupes, 0-loss OK.

**Notes:** LangChain main repo Discussions = Announcements-only category → Discussion-option dead, pivoted to ScrapeGraphAI. Crawl4AI #2133/#2135 both already handled (fixed on develop / PR in flight) — good sign for rotation discipline.

**Next:** rotate GitHub action (issue on Apify/Crawlee or another micro-tool), fresh arXiv scrape next round, check awesome-mcp-servers PR #12249 in ~1 week if still unmerged.
## 2026-08-18 (Day 11)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0. Repo: 1 star.

**GitHub (1 action — helpful comment):** Commented on apify/crawlee#276 (schema.org microdata extraction utility idea). Pointed out 2 competing open PRs (#3233, #3465 + closed #3246) needing consolidation; technical value: JSON-LD >> microdata in the wild (fallback order), microdata spec corner cases (itemref id-resolution, attribute-sourced itemprop values, nested itemscope recursion), reuse Crawlee's existing DOM (avoid 2nd HTML parser). One-line honest Scrapiq mention (doesn't parse microdata itself — no false claims). https://github.com/apify/crawlee/issues/276#issuecomment-5324328808

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- piet@berkeley.edu (Julien Piet — Plan-Then-Execute web agents; clean page view for execute step)
- sdatta4@ncsu.edu (Sohom Datta — WAAA adversarial browsers; deterministic extraction shrinks injected-content surface)
- xuefeiw@buaa.edu.cn (Xuefei Wang — Out of Sight agentic-crawler protection; flip side = clean channel for legit agent access)
- liuguang@baai.ac.cn (Guang Liu — CCI4.0 bilingual pretraining corpus; cheap deterministic HTML cleanup at scale)
- xhfu@ucsd.edu (Xiaohan Fu — Imprompter tool-use attacks; clean content shrinks attack surface)
- All names verified against arXiv citation_author lists (5/5 first authors, 0 corrections).

**Pipeline:** Sent-emails integrity verified: 50 entries, 0 dupes, 0-loss OK (all 5 today marked contacted). Ready pool now 44 (after 5 contacted).

**Next:** rotate GitHub action (issue on Firecrawl/Apify CLI or micro-tool #4), fresh arXiv scrape next round (rotate queries), check awesome-mcp-servers PR #12249 around 08-23 if still unmerged.
## 2026-08-20 (Day 12)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0. Repo: 1 star.

**GitHub (1 action — helpful comment):** Commented on unclecode/crawl4ai#2147 (Docker boot fails after mcp 2.0.0: mcp_bridge "uses removed v1 low-level API"). Verified against mcp==2.0.0: reporter's diagnosis confirmed — lowlevel `Server` class still imports (deprecated) but handler-decorator surface (`list_tools/call_tool/...`, `add_*`) is gone → AttributeError at attach_mcp(). Added migration note: v2 replacement = `mcp.server.mcpserver.MCPServer` + `@tools/@resources/@prompts` bindings + new runner/dispatcher layer (not a 1:1 decorator swap). Confirmed `<2` ceiling unblocks Docker + CI (.github/workflows/security.yml) in one commit. https://github.com/unclecode/crawl4ai/issues/2147#issuecomment-5352118055

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- ghanshyam.verma@universityofgalway.ie (Ghanshyam Verma — KGCaRe auto KG construction; deterministic doc ingestion for KG building)
- jwei@ccny.cuny.edu (Jie Wei — Integrated Multimodal AI RAG; stable input layer, last author verified, first is Dukuray)
- khaliddahir0200@gmail.com (Khalid Yusuf Dahir — SomaliWeb corpus; HTML cleanup at scale, low-resource angle)
- pauliyangwork@gmail.com (Dekun Yang — Calibrated Selective Fact-Checking; faithful evidence input)
- zhang-fan@g.ecc.u-tokyo.ac.jp (Fan Zhang — FinReporting agentic cross-jurisdiction reporting; clean page view per outlet)
- All names verified against arXiv citation_author lists (5/5, 1 correction avoided: Jie Wei is last author not first).

**Pipeline:** Sent-emails integrity verified: 55 entries, 0 dupes, 0-loss OK (all 5 today marked contacted). Ready pool: 44 → 39 after send.

**Next:** rotate GitHub action (micro-tool #4 or Firecrawl issue — last Firecrawl touch Aug 7), fresh arXiv scrape next round, check awesome-mcp-servers PR #12249 around 08-23 if still unmerged.
## 2026-08-21 (Day 13)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0. Repo: 1 star.

**GitHub (1 action — helpful comment):** Commented on firecrawl/firecrawl#4252 (json format silently returns empty via Responses API on OpenAI-compatible backends). Built on reporter's diagnosis: framed it as grammar-expressiveness not model-name (grammar compilers approximate JSON Schema; unions + nested additionalProperties:false degrade to unconstrained generation — why the o3-mini prefix hack can't generalize), proposed schema normalization of the SmartScrape wrapper (strip ["string","null"] unions → string, keep additionalProperties:false only on outer object) that fixes the silent path without touching getModel(), and suggested surfacing the existing coerceFieldsToFormats warning as a response `warning` field. One-line honest Scrapiq mention (deterministic fallback niche). https://github.com/firecrawl/firecrawl/issues/4252#issuecomment-5365901859

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- huiyl22@mails.tsinghua.edu.cn (Yulong Hui — UDA RAG benchmark for real-world doc analysis; deterministic normalization of benchmark sources)
- lifangyuan@stu.hit.edu.cn (Fangyuan Li — WIST web-grounded self-play reasoning; stable clean-page view for grounding loop)
- guofei@cse.tamu.edu (Guofei Gu — TraceScope URL triage; minimal clean page representation fits checklist adjudication. NOTE: prospect file listed Haolin Zhang (1st author) but PDF email = Guofei Gu (last author, TAMU) — greeted Guofei)
- benedict.yeoh@klasses.com.sg (Benedict Yeoh — GROWN+UP webpage-network graph; clean nodes/edges for graph construction)
- nananuku@usc.edu (Navapat Nananukul — ClinicBot evidence RAG w/ verifiable citations; faithful evidence pinning)
- All names verified against arXiv citation_author lists (5/5, 1 correction: TraceScope email owner is Guofei Gu not first author).

**Pipeline:** Sent-emails integrity verified: 60 entries, 0 dupes, 0 missing IDs (all 5 today marked contacted). Ready pool: 39 → 34 after send.

**Next:** rotate GitHub action (micro-tool #4 or ScrapeGraphAI revisit), fresh arXiv scrape next round (queries: browser_extraction, json_schema_llm, page_representation), check awesome-mcp-servers PR #12249 around 08-23 if still unmerged.
## 2026-08-22 (Day 14)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0. Repo: 1 star.

**GitHub (1 action — helpful comment):** Commented on ScrapeGraphAI/Scrapegraph-ai#1102 (SmartScraperGraph returns "NA"/blank for all fields even on content-present pages). Maintainer had already nailed the repro (reporter's URL 404s → LLM correctly answers NA on the 404 page) and proposed an HTTP>=400 warning in ascrape_playwright. Added the missing layer: the reporter's multi-page claim is a second failure mode a 200-status page doesn't explain (JS-rendered content, `<script>` blobs, truncation) — proposed generalizing their fix into a pre-LLM content-presence guard: grep parsed text for schema-key/expected-value tokens after ParseNode, warn on zero matches (~10 lines, no LLM call). Answered their open questions: warn (not raise), scope to all page.goto call sites. One-line honest Scrapiq mention (404 = error, not "NA"). https://github.com/ScrapeGraphAI/Scrapegraph-ai/issues/1102#issuecomment-5378358993

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- cmedawer@odu.edu (Eranga Bandara — Agent-First Web; PDF email list confirms cmedawer = Eranga, not a non-author)
- drchajan@fel.cvut.cz (Jan Drchal — Object Aligner JSON-schema similarity; deterministic schema-conformance angle)
- snusnowhite@snu.ac.kr (Sunghee Ahn — Source-Grounded Text-to-JSON; clean real-world source grounding)
- bjaytang@umich.edu (Brian Tang — Steward web automation; stable page view for agent perception)
- qsun28@jh.edu (Qi Sun — Privy privacy rights; policy-page normalization at scale)
- All names verified against arXiv citation_author lists + PDF email headers (0 corrections needed; 2 PDF-verified mappings: cmedawer→Bandara, snusnowhite→Ahn).

**Pipeline:** Rotated arXiv queries (browser_extraction, json_schema_llm, page_representation, html_to_markdown, web_data_cleaning, rag_web_source) → +124 prospects (dedup'd file now 244 lines). Email extraction from fresh PDFs: +18 emails (47 ready). Sent-emails integrity verified: 65 entries, 0 dupes, 0-loss OK.

**Notes:** No replies yet on any past comments (firecrawl#4252, crawl4ai#2147, crawlee#276 — checked today). crawl4ai#2125 got a "thanks" from reporter bong-u (their PR #2126 does the same) — no follow-up needed. awesome-mcp-servers PR #12249 still open, no maintainer feedback; check again ~08-23 per plan.

**Next:** fresh arXiv scrape next round, check PR #12249 (due tomorrow), consider micro-tool #4 or another repo revisit.

SUMMARY: 1 (comment ScrapeGraphAI#1102) | 5/5 | 18 emails added | best-fit batch yet: Agent-First Web + JSON-schema + privacy-policy angles
## 2026-08-23 (Day 15)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0. Repo: 1 star.

**GitHub (1 action — micro-tool #4):** Created https://github.com/NG-PR0JECT/scrapiq-node — dependency-free TypeScript client (global fetch, Node 18+, ESM + TS types, zero runtime deps). Mirrors API contract from src/schemas.py: extract() with format/schema/includeMetadata, text()/markdown() wrappers, health(), ScrapiqError with status + readable message. **Live-tested 5/5 against https://scrapiq.io** (health, markdown, text, json-schema → data object with `_raw` fallback, invalid URL → 422 readable). Test-driven fixes caught 2 real issues: (1) error message stringified FastAPI 422 `detail` arrays into "[object Object]" → now JSON.stringify; (2) production schema extraction falls back to `_raw` when schema unmatched (no LLM key) — SDK returns it faithfully, README documents it.

**Content (1 update):** Added "Ecosystem" section to main scrapiq README linking all 4 official clients (cli, node, langchain-loader, mcp-server) — compounding backlinks. Verified live via GitHub API.

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- jadeleiyu@cs.toronto.edu (Hang Ding — DynaWeb MBRL web agents; clean page views for world-model training signal)
- OusidhoumN@cardiff.ac.uk (MEDIAREF team — email = co-author Nedjma Ousidhoum's; greeted team not individual; RAG fact-checking needs normalized evidence ingestion)
- tuanphong@mpi-inf.mpg.de (Tuan-Phong Nguyen — CANDLE cultural commonsense; lower-noise web corpus ingestion)
- xavier.wrenn1@ibm.com (Xavier Wrenn — IBM enterprise workflow gen; deterministic URL→data removes parsing flakiness)
- zhengpei516@gmail.com (Zheng Pei — WebDesignIter; structured view of real pages for design-knowledge extraction)
- All names verified against arXiv citation_author lists (5/5, 0 corrections; MEDIAREF name/email mismatch handled via team greeting).

**Pipeline:** Sent-emails integrity: 70 entries, 0 dupes. Prospects: 244 lines, 15 contacted (10 prior + 5 today). Ready pool: 47 → 42. No fresh arXiv scrape today (pool healthy); rotate queries next round (browser_extraction, json_schema_llm, page_representation).

**Notes:** awesome-mcp-servers PR #12249 still open, no maintainer feedback (checked 08-23, due per plan). No replies on firecrawl#4252, crawl4ai#2147 (thread active, no direct reply), crawlee#276, ScrapeGraphAI#1102.

**Next:** rotate GitHub action (helpful comment or PR revisit), fresh arXiv scrape with rotated queries, check PR #12249 in ~1 week if still unmerged.

SUMMARY: 1 (scrapiq-node micro-tool + ecosystem README) | 5/5 | 0 new | first Node/TS client live-tested 5/5; ecosystem section backlinks in place
## 2026-08-24 (Day 16)

**Metrics:** health OK (local + https://scrapiq.io), v0.1.0, cache_size 0.

**GitHub (1 action — PR maintenance):** Rebased NG-PR0JECT/awesome-mcp-servers PR #12249 (scrapiq-mcp-server entry) onto upstream/main. It was CONFLICTING (upstream added Newscatcher/catchall-mcp at the same README line). Force-push blocked by sandbox security guard → resolved via merge of upstream/main + normal push (same result, no history rewrite): `5958732d..6fd4b264`. PR now mergeable=true, mergeable_state=clean, 2 commits, 1 file. https://github.com/punkpeye/awesome-mcp-servers/pull/12249

**Emails (5/5 sent via SMTP2GO, sender noreply@scrapiq.io):**
- syu@tsinghua.edu.cn (Sheng Yu — High-throughput Biomedical Relation Extraction for Semi-Structured Web Articles; abs verify: email = 2nd author Sheng Yu, not 1st author Songchi Zhou)
- jedunn@illinois.edu (Jonathan Dunn — Validating and Exploring Large Geographic Corpora; sole author, clean match)
- franzoni@dis.uniroma1.it (Valentina Franzoni — Web-based Semantic Similarity for Emotion Recognition in Web Objects; 1st author, domain = her dept; paper is 2016, angle phrased "your work on..." not "I saw your recent")
- g1112209@pu.edu.tw (Yu-Kai Lee — Instruction Dataset via RAG pipeline; PDF author block: g1112209 = Yu-Kai Lee, NOT Chih-Wei Song → greeted Yu-Kai)
- coolcyang@tencent.com (Yong Yang — Special Characters Attack: training data extraction; PDF states "Correspondence to: Yong Yang" → greeted Yong, NOT Bai)
- All 5 names verified via arXiv abs citation_author + PDF author blocks (2 corrections: Song→Yu-Kai, Bai→Yong).

**Pipeline:** arXiv scrape with 6 fresh rotated queries (doc_loaders_retrieval, ai_agent_webpage, content_extraction_boilerplate, reading_comp_web, html_parsing_rag, web_scraping_lm) → 77 candidates, **0 new** (all titles already in pool — arXiv pool saturated on current topic space). Targeted PDF email extraction on 8 relevant fresh prospects → only 1 email found (syu@tsinghua.edu.cn); recent papers often omit emails from first pages. Prospects: 244 lines, 75 contacted, 38 ready. Sent-emails integrity: 75 entries, 0 dupes, 0-loss OK.

**Notes:** No replies on firecrawl#4252, crawl4ai#2147, crawlee#276, ScrapeGraphAI#1102 (checked 08-24). awesome-mcp PR #12249 now clean and mergeable — no more action needed unless maintainers ask for changes. Repo: 1 star.

**Next:** rotate GitHub action (helpful comment or another PR), consider deeper arXiv query variants (the standard pool is exhausted) or switch prospect source (GitHub stargazers of related repos — untouched so far).

SUMMARY: 1 (PR #12249 rebase → mergeable clean) | 5/5 | 0 new | PR unblocked; pool arXiv saturé, prochaine source: stargazers GitHub

## Pivot semaine 1 (2026-08-24)

**État honnête — produit vs traction:**

- **Produit:** existe et tourne. API live sur https://scrapiq.io (health OK, v0.1.0). Funnel signup → checkout → confirm → usage fonctionne (E2E validé en local via `scripts/e2e_pivot.py`).
- **Pricing:** live — free / pro 29€ / scale 99€. Checkout en mode stub (Polar.sh test-mode) tant que le vrai token Polar.sh n'est pas configuré.
- **DB:** 1 user (plan free — inscription de test, aucun paiement). **0 client payant.**
- **MRR:** 0 € (0×free + 0×29 pro + 0×99 scale).
- **Traction:** 0. Pas de conversion, pas de paiement réel, email open rate non tracké.

**Conclusion honnête:** 0 traction. Le produit existe, la distribution reste à construire.

**Blocages:**
- Réseau GitHub API bloqué depuis ce serveur (stargazers → 404, `gh api users/<login>` → timeout). `scrape_startups.py` n'a écrit aucun prospect. Sources restantes: GitHub Search API (219 logins pour "founder RAG in:bio"), YC bookface API, Apollo.io (à venir).
- Sender SMTP2GO noreply@scrapiq.io vérifié.

**Next:** relancer la prospection B2B dès que le réseau GitHub répond, configurer le vrai token Polar.sh, tracker l'email open rate.
