"""Pydantic schemas for request/response."""

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


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


# ── Auth / billing / events ──────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    """Create an account / API key."""

    email: str = Field(..., description="Email address to associate with the API key")

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address")
        return v


class SignupResponse(BaseModel):
    """Response to a signup request."""

    email: str
    api_key: str
    plan: str
    created_at: str


class UsageResponse(BaseModel):
    """Quota usage for the calling API key."""

    api_key: str
    plan: str
    used: int
    quota: int | None
    date: str


class CheckoutResponse(BaseModel):
    """A checkout URL for upgrading to a paid plan."""

    plan: str
    email: str
    checkout_url: str
    provider: str


class ConfirmResponse(BaseModel):
    """Result of a (stub-mode) simulated checkout."""

    plan: str
    email: str
    status: str


class EventRequest(BaseModel):
    """Server-side conversion/usage event."""

    event_type: str = Field(..., description="e.g. signup, extract, checkout")
    source: str | None = Field(None, description="utm_source")
    campaign: str | None = Field(None, description="utm_campaign")
