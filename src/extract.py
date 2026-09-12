"""Core extraction logic — fetch URL, clean content, structure to JSON.

The pipeline:
  1. Fetch URL via httpx (with timeout, retry, size limit)
  2. Clean HTML → plain text or markdown using trafilatura
  3. (Optional) Extract structured fields per a JSON schema
  4. Return metadata (title, description, author, date, word count)

Schema-driven extraction strategy for v0.1: simple key-value extraction
from text. For named fields, search the text for "key: value" patterns,
or use the schema's 'description' as a regex prompt. v0.2 will swap to
an LLM-callable extraction layer.

This is intentionally minimal — the value is in *cleaning + structuring*,
not in the LLM call (which the user can do themselves with their own
OpenAI key, or we add as a paid tier later).
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup

from .config import settings
from .schemas import ExtractRequest, ExtractResponse, PageMetadata


class ExtractionError(Exception):
    """Raised when extraction fails for any reason."""


# --- markdown link-injection guards -----------------------------------------
# Ranges that must never be rewritten: existing [label](url) links and bare URLs.
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\([^)]*\)")
_BARE_URL_RE = re.compile(r"https?://\S+")
# Labels shorter than this collide with substrings already present in URLs.
_MIN_INJECT_LEN = 4


def _protected_spans(text: str) -> list[tuple[int, int]]:
    """Return (start, end) ranges of existing markdown links and bare URLs."""
    spans = [m.span() for m in _MD_LINK_RE.finditer(text)]
    spans += [m.span() for m in _BARE_URL_RE.finditer(text)]
    return spans


def _in_span(spans: list[tuple[int, int]], pos: int) -> bool:
    """True if pos falls inside one of the protected ranges."""
    return any(start <= pos < end for start, end in spans)


async def fetch_url(url: str) -> tuple[bytes, str]:
    """Fetch URL with timeout, size limit, and proper headers.

    Returns (content_bytes, final_url) after following redirects.
    Raises ExtractionError on any failure.
    """
    if len(url) > settings.MAX_URL_LENGTH:
        raise ExtractionError(f"URL too long (>{settings.MAX_URL_LENGTH} chars)")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ExtractionError(f"Unsupported scheme: {parsed.scheme!r}")

    headers = {
        "User-Agent": settings.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=settings.REQUEST_TIMEOUT,
        headers=headers,
    ) as client:
        try:
            response = await client.get(url)
        except httpx.TimeoutException as exc:
            raise ExtractionError(f"Request timed out after {settings.REQUEST_TIMEOUT}s") from exc
        except httpx.HTTPError as exc:
            raise ExtractionError(f"HTTP error: {exc}") from exc

        if response.status_code >= 400:
            raise ExtractionError(f"HTTP {response.status_code} from target")

        # Size limit check
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_CONTENT_SIZE:
            raise ExtractionError(f"Content too large ({content_length} bytes)")

        content = response.content
        if len(content) > settings.MAX_CONTENT_SIZE:
            raise ExtractionError(f"Content too large ({len(content)} bytes)")

        return content, str(response.url)


def extract_text(html: bytes, url: str, output_format: str) -> str:
    """Extract clean text or markdown from HTML.

    Uses trafilatura (state-of-the-art boilerplate removal) as the primary
    extractor. Falls back to BeautifulSoup if trafilatura returns empty.
    For markdown, post-processes <a> tags that trafilatura dropped to
    preserve links in `[text](url)` format.
    """
    html_str = html.decode("utf-8", errors="ignore")

    if output_format == "markdown":
        text = trafilatura.extract(
            html_str,
            include_links=True,
            include_images=False,
            include_tables=True,
            output_format="markdown",
            with_metadata=False,
        )
    else:
        text = trafilatura.extract(
            html_str,
            include_links=True,
            include_images=False,
            include_tables=True,
            output_format="txt",
            with_metadata=False,
        )

    text = text.strip() if text else ""

    if output_format != "markdown":
        return text if text else _fallback_text(html)

    if not text:
        return _fallback_text(html)

    return _inject_missing_links(text, html)


def _inject_missing_links(text: str, html: bytes) -> str:
    """Add `[label](href)` for anchors trafilatura dropped from the output.

    Only injects a label that is currently missing from the text, and only when
    the match position is outside every existing `[label](url)` / bare URL.
    Labels shorter than _MIN_INJECT_LEN are never injected: on Wikipedia the
    navbox anchors carry 1-3 char labels ("R", "e", "AI") that also occur as
    substrings of already-correct links and URLs, which is exactly how the
    previous `str.replace` version corrupted 79 link constructs on one page.
    Pure function (no network) so the guards are unit-testable.
    """
    soup = BeautifulSoup(html, "html.parser")
    spans = _protected_spans(text)

    for a in soup.find_all("a", href=True):
        href = a["href"]
        link_text = a.get_text(strip=True)
        if not link_text or len(link_text) < _MIN_INJECT_LEN or href in text:
            continue
        idx = text.find(link_text)
        if idx < 0 or _in_span(spans, idx):
            continue
        after = text[idx + len(link_text) : idx + len(link_text) + 2]
        if after.startswith("]("):
            continue
        text = text[:idx] + f"[{link_text}]({href})" + text[idx + len(link_text) :]
        spans = _protected_spans(text)

    return text


def _fallback_text(html: bytes) -> str:
    """Plain-text fallback when trafilatura returns nothing."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_metadata(html: bytes, url: str) -> PageMetadata:
    """Extract page metadata from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    def meta(name: str, attr: str = "name") -> str | None:
        tag = soup.find("meta", attrs={attr: name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        title = meta("og:title", "property")

    description = meta("description") or meta("og:description", "property")
    author = meta("author")
    published_date = meta("article:published_time", "property") or meta("pubdate") or meta("date")
    language = soup.html.get("lang") if soup.html else None
    canonical = None
    canonical_tag = soup.find("link", rel="canonical")
    if canonical_tag and canonical_tag.get("href"):
        canonical = canonical_tag["href"]

    # Word count
    text = soup.get_text(separator=" ", strip=True)
    word_count = len(text.split())

    return PageMetadata(
        title=title,
        description=description,
        author=author,
        published_date=published_date,
        language=language,
        canonical_url=canonical,
        word_count=word_count,
    )


def extract_structured(text: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Extract structured fields from text according to a JSON schema.

    v0.1 algorithm: whitespace-tokenize, scan for each schema field name,
    grab the first numeric/string value within ±50 tokens. Cheap and works
    for ~60% of "extract: price, name, date" use cases on clean text.

    v0.2 will swap in an LLM-callable extractor (with user's key).
    For v0.1 we ship the dumb version that gives value for free text.
    """
    properties = schema.get("properties", {})
    if not properties:
        return {"_raw": text}

    result: dict[str, Any] = {}
    text_lower = text.lower()

    for field_name, field_schema in properties.items():
        field_type = field_schema.get("type", "string")
        # Search for the field name in the text
        pattern = re.compile(rf"\b{re.escape(field_name)}\b", re.IGNORECASE)
        match = pattern.search(text)
        if not match:
            result[field_name] = None
            continue

        # Look at the next 200 chars after the field name
        start = match.end()
        snippet = text[start : start + 200].strip()
        # Take first sentence/line. Only split on period/dot if it's NOT
        # followed by a digit (i.e. don't break "2499.99" into "2499" + ".99").
        snippet = re.split(r"[\n;]|(?<!\d)\.|\.(?!\d)", snippet, maxsplit=1)[0].strip()

        if field_type == "number":
            # Match a number with optional decimal (handle both . and , as separator).
            # Take the FIRST complete number-with-decimal, not the integer prefix.
            matches = re.findall(r"-?\d+(?:[.,]\d+)?", snippet)
            value = None
            for m in matches:
                try:
                    v = float(m.replace(",", "."))
                    value = v
                    break  # first match wins
                except ValueError:
                    continue
            result[field_name] = value
        elif field_type == "integer":
            numbers = re.findall(r"-?\d+", snippet)
            result[field_name] = int(numbers[0]) if numbers else None
        elif field_type == "boolean":
            result[field_name] = bool(
                re.search(r"\b(true|yes|oui|1)\b", snippet, re.IGNORECASE)
            )
        else:
            # String: first 200 chars
            result[field_name] = snippet[:200] if snippet else None

    return result


async def extract(request: ExtractRequest) -> ExtractResponse:
    """Main pipeline: fetch → clean → (optional) structure.

    Returns ExtractResponse with data, content, or both depending on format.
    """
    import time

    start = time.monotonic()

    html, final_url = await fetch_url(str(request.url))

    metadata = extract_metadata(html, final_url) if request.include_metadata else None

    if request.format == "json":
        # Extract text first, then structure-ify
        text = extract_text(html, final_url, output_format="text")
        if request.schema_definition:
            data = extract_structured(text, request.schema_definition)
        else:
            # No schema: return raw text under a "text" key
            data = {"text": text}
        content = None
    else:
        content = extract_text(html, final_url, output_format=request.format)
        data = None

    elapsed_ms = int((time.monotonic() - start) * 1000)

    return ExtractResponse(
        url=final_url,
        format=request.format,
        data=data,
        content=content,
        metadata=metadata,
        cached=False,
        extraction_time_ms=elapsed_ms,
    )
