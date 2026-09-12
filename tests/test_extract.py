"""Unit tests for the extractor — pure functions only, no HTTP."""

import re

import pytest

from src.extract import (
    _in_span,
    _inject_missing_links,
    _protected_spans,
    extract_metadata,
    extract_structured,
    extract_text,
)
from src.schemas import PageMetadata


class TestExtractText:
    """Test HTML → text/markdown cleaning."""

    def test_strips_script_tags(self):
        html = b"<html><body><p>Hello</p><script>alert('x')</script></body></html>"
        out = extract_text(html, "http://x.com", "text")
        assert "Hello" in out
        assert "alert" not in out

    def test_strips_style_tags(self):
        html = b"<html><body><style>body { color: red; }</style><p>Real</p></body></html>"
        out = extract_text(html, "http://x.com", "text")
        assert "Real" in out
        assert "color" not in out

    def test_markdown_includes_links(self):
        html = b'<html><body><p>See <a href="https://example.com">here</a></p></body></html>'
        out = extract_text(html, "http://x.com", "markdown")
        assert "here" in out
        assert "http" in out or "example.com" in out

    def test_returns_empty_for_empty_html(self):
        out = extract_text(b"<html></html>", "http://x.com", "text")
        assert out == "" or out is None

    def test_handles_unicode(self):
        html = "<html><body><p>Café résumé naïve</p></body></html>".encode("utf-8")
        out = extract_text(html, "http://x.com", "text")
        assert "Café" in out
        assert "naïve" in out


class TestExtractMetadata:
    """Test HTML metadata extraction."""

    def test_basic_title(self):
        html = b"<html><head><title>Hello world</title></head><body></body></html>"
        meta = extract_metadata(html, "http://x.com")
        assert meta.title == "Hello world"

    def test_og_title_fallback(self):
        html = b"""<html><head>
            <meta property="og:title" content="OG Title"/>
        </head><body></body></html>"""
        meta = extract_metadata(html, "http://x.com")
        assert meta.title == "OG Title"

    def test_meta_description(self):
        html = b"""<html><head>
            <meta name="description" content="A description"/>
        </head><body></body></html>"""
        meta = extract_metadata(html, "http://x.com")
        assert meta.description == "A description"

    def test_canonical_url(self):
        html = b"""<html><head>
            <link rel="canonical" href="https://canonical.com/page"/>
        </head><body></body></html>"""
        meta = extract_metadata(html, "http://x.com")
        assert meta.canonical_url == "https://canonical.com/page"

    def test_word_count(self):
        html = b"<html><body><p>one two three four five</p></body></html>"
        meta = extract_metadata(html, "http://x.com")
        assert meta.word_count == 5

    def test_language_from_html_attr(self):
        html = b'<html lang="fr"><body></body></html>'
        meta = extract_metadata(html, "http://x.com")
        assert meta.language == "fr"


class TestExtractStructured:
    """Test schema-driven structured extraction."""

    def test_empty_schema_returns_raw(self):
        result = extract_structured("Some text here", {"properties": {}})
        assert result == {"_raw": "Some text here"}

    def test_string_field_extraction(self):
        text = "Product: MacBook Pro 16-inch. Price: $2499. Stock: 12."
        schema = {"properties": {"product": {"type": "string"}, "price": {"type": "string"}}}
        result = extract_structured(text, schema)
        assert "MacBook" in result["product"]
        assert "$2499" in result["price"]

    def test_number_field_extraction(self):
        text = "Price: 2499.99 euros. Stock: 12 units."
        schema = {"properties": {"price": {"type": "number"}, "stock": {"type": "integer"}}}
        result = extract_structured(text, schema)
        assert result["price"] == 2499.99
        assert result["stock"] == 12

    def test_boolean_field_extraction(self):
        text = "Available: yes. Featured: no."
        schema = {"properties": {"available": {"type": "boolean"}, "featured": {"type": "boolean"}}}
        result = extract_structured(text, schema)
        assert result["available"] is True
        assert result["featured"] is False

    def test_missing_field_returns_none(self):
        text = "Just some text without the field."
        schema = {"properties": {"price": {"type": "number"}}}
        result = extract_structured(text, schema)
        assert result["price"] is None

    def test_handles_comma_decimal(self):
        text = "Price: 2499,99 EUR"
        schema = {"properties": {"price": {"type": "number"}}}
        result = extract_structured(text, schema)
        assert result["price"] == 2499.99


@pytest.mark.parametrize(
    "html,expected_word_count",
    [
        (b"<html><body><p>one two three</p></body></html>", 3),
        (b"<html><body>single</body></html>", 1),
        (b"<html><body></body></html>", 0),
    ],
)
def test_word_count_parametrized(html, expected_word_count):
    meta = extract_metadata(html, "http://x.com")
    assert meta.word_count == expected_word_count


class TestLinkInjectionGuards:
    """Regression tests: the markdown link-injection pass must never corrupt
    links or URLs that trafilatura already produced.

    Real failure (found 2026-09-12 while benchmarking 12 live pages): on
    https://en.wikipedia.org/wiki/Retrieval-augmented_generation the navbox
    anchors carry 1-3 char labels ("R", "e", "AI"), which the old `str.replace`
    pass matched *inside* already-correct links and URLs, mangling 79 link
    constructs on a single page.
    """

    def test_short_labels_do_not_corrupt_existing_link(self):
        text = (
            "# Retrieval-augmented generation\n\n"
            "**Retrieval-augmented generation** (**RAG**) is a technique that enables "
            "[large language models](https://en.wikipedia.org/wiki/Large_language_model) "
            "to retrieve and incorporate new information.\n"
        )
        html = (
            b'<nav><a href="/wiki/Template:AI">AI</a>'
            b'<a href="/wiki/Template:R">R</a>'
            b'<a href="/wiki/Template:Gen">e</a>'
            b'<a href="/wiki/Template:GenAI">t</a></nav>'
        )
        out = _inject_missing_links(text, html)
        assert "[large language models](https://en.wikipedia.org/wiki/Large_language_model)" in out
        assert "_[AI](/wiki/Template:AI)" not in out
        assert not re.search(r"\]\([^)\s]*\[", out), f"corrupted link target: {out[:200]!r}"
        assert out == text  # nothing to inject, nothing changed

    def test_long_missing_label_is_still_injected(self):
        text = "This chapter walks you through getting started with the language."
        html = b'<a href="https://doc.rust-lang.org/book/">getting started</a>'
        out = _inject_missing_links(text, html)
        assert "[getting started](https://doc.rust-lang.org/book/)" in out

    def test_label_inside_bare_url_is_not_injected(self):
        text = "See https://example.com/products/analytics for the numbers."
        html = b'<a href="https://other.example/analy">analytics</a>'
        out = _inject_missing_links(text, html)
        assert out == text

    def test_helpers(self):
        text = "text [label](https://a.com/x) then https://b.com/y end"
        spans = _protected_spans(text)
        assert _in_span(spans, text.index("a.com"))
        assert _in_span(spans, text.index("b.com"))
        assert not _in_span(spans, 0)

