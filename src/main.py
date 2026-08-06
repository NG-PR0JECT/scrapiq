"""Scrapiq HTTP API — FastAPI app."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import settings
from .extract import ExtractionError, extract
from .schemas import ExtractRequest, ExtractResponse, HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Scrapiq",
    description=(
        "Turn any URL into clean, structured JSON for LLM/RAG pipelines. "
        "Submit a URL, optionally with a JSON schema, and get back clean text, "
        "markdown, or structured fields ready for fine-tuning or RAG ingestion."
    ),
    version=__version__,
    contact={"name": "Scrapiq", "url": "https://github.com/NG-PR0JECT/scrapiq"},
    license_info={"name": "MIT"},
)

# CORS — open for the public API (no auth in v0.1)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Info"])
def root() -> dict:
    """Root endpoint with a quick-start example."""
    return {
        "service": "scrapiq",
        "version": __version__,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "quickstart": {
            "curl": (
                "curl -X POST http://localhost:8001/v1/extract "
                "-H 'Content-Type: application/json' "
                "-d '{\"url\": \"https://example.com\", \"format\": \"markdown\"}'"
            ),
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    """Health check — used by uptime monitors."""
    return HealthResponse(
        status="ok",
        version=__version__,
        cache_size=0,  # v0.1 has no cache yet
    )


@app.post(
    "/v1/extract",
    response_model=ExtractResponse,
    tags=["Extraction"],
    summary="Extract structured data from a URL",
)
async def extract_endpoint(request: ExtractRequest) -> ExtractResponse:
    """Fetch a URL and return clean text, markdown, or structured fields.

    - **format=text**: clean plain text (boilerplate removed)
    - **format=markdown**: clean markdown with links
    - **format=json** (with schema): structured fields per the schema
    - **format=json** (no schema): wrapped raw text under `data.text`
    """
    try:
        return await extract(request)
    except ExtractionError as exc:
        logger.warning("Extraction failed for %s: %s", request.url, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error extracting %s", request.url)
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc


def run() -> None:
    """Entry point for the `scrapiq` script."""
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
    )


if __name__ == "__main__":
    run()
