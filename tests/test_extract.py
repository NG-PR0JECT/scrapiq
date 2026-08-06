"""Unit tests for the extractor — pure functions only, no HTTP."""

import pytest

from src.extract import extract_metadata, extract_structured, extract_text
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
