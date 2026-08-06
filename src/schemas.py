"""Pydantic schemas for request/response."""

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class ExtractRequest(BaseModel):
    """Request to extract structured data from a URL."""

    url: HttpUrl = Field(..., description="URL to fetch and extract from")
    schema_definition: dict[str, Any] | None = Field(
        None,
        alias="schema",
        description="Optional JSON schema describing fields to extract. If omitted, returns raw cleaned text.",
    )
    format: Literal["json", "text", "markdown"] = Field(
        "json",
        description="Output format. 'json' for structured extraction, 'text' for plain text, 'markdown' for clean markdown.",
    )
    include_metadata: bool = Field(
        True,
        description="Include page metadata (title, description, author, date) in the response.",
    )


class PageMetadata(BaseModel):
    """Metadata about the fetched page."""

    title: str | None = None
    description: str | None = None
    author: str | None = None
    published_date: str | None = None
    language: str | None = None
    canonical_url: str | None = None
    word_count: int | None = None


class ExtractResponse(BaseModel):
    """Response with extracted data."""

    url: str
    format: str
    data: dict[str, Any] | None = Field(
        None,
        description="Structured data extracted according to the schema. None if format != 'json'.",
    )
    content: str | None = Field(
        None,
        description="Cleaned text or markdown content. None if format == 'json'.",
    )
    metadata: PageMetadata | None = None
    cached: bool = False
    extraction_time_ms: int


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: str | None = None
    url: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["ok", "degraded", "down"]
    version: str
    cache_size: int
