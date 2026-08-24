"""Scrapiq HTTP API — FastAPI app."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .config import PLANS, settings
from .db import (
    check_and_increment,
    configure,
    create_user,
    get_user_by_api_key,
    get_usage,
    record_event,
    set_user_plan,
)
from .extract import ExtractionError, extract
from .payments import checkout_url as _checkout_url
from .payments import handle_webhook_event, verify_webhook_signature
from .schemas import (
    CheckoutResponse,
    ConfirmResponse,
    EventRequest,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    SignupRequest,
    SignupResponse,
    UsageResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Ensure the DB schema exists on startup (path from env or default).
configure()

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


@app.middleware("http")
async def api_key_quota_middleware(request: Request, call_next):
    """Enforce API-key quota on /v1/extract.

    Backwards compatible: requests WITHOUT an X-API-Key header are still
    allowed (legacy anonymous mode). Requests WITH a key are authenticated
    and quota-checked. Pro/Scale bypass quota in early-access mode.
    """
    if request.url.path.rstrip("/") == "/v1/extract":
        api_key = request.headers.get("X-API-Key")
        if api_key:
            if get_user_by_api_key(api_key) is None:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or unknown API key"},
                )
            result = check_and_increment(api_key)
            if not result["allowed"]:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Daily quota exceeded. Upgrade at https://scrapiq.io/pricing",
                        "plan": result["plan"],
                        "used": result["used"],
                        "quota": result["quota"],
                    },
                    headers={"Retry-After": "86400"},
                )
            request.state.api_key = api_key
            request.state.plan = result["plan"]
    return await call_next(request)


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


# ── Auth / signup ────────────────────────────────────────────────────────


@app.post("/v1/signup", response_model=SignupResponse, tags=["Auth"], status_code=201)
def signup(request: SignupRequest) -> SignupResponse:
    """Create an account and return an API key.

    Idempotent: signing up with an existing email returns the existing key
    (same plan preserved) rather than erroring.
    """
    from .db import get_user_by_email

    user = get_user_by_email(request.email)
    if user is None:
        user = create_user(request.email)
        record_event(user["api_key"], "signup")
    return SignupResponse(
        email=user["email"],
        api_key=user["api_key"],
        plan=user["plan"],
        created_at=user["created_at"],
    )


@app.get("/v1/usage", response_model=UsageResponse, tags=["Auth"])
def usage(api_key: str | None = None, x_api_key: str | None = None) -> UsageResponse:
    """Return today's quota usage for an API key.

    Pass the key via `?api_key=` query param or `X-API-Key` header.
    """
    key = api_key or x_api_key
    if not key:
        raise HTTPException(status_code=400, detail="Missing API key")
    if get_user_by_api_key(key) is None:
        raise HTTPException(status_code=401, detail="Invalid or unknown API key")
    usage_data = get_usage(key)
    return UsageResponse(**usage_data)


# ── Billing (Polar.sh, stub / early-access) ──────────────────────────────


@app.get("/v1/billing/checkout", response_model=CheckoutResponse, tags=["Billing"])
def billing_checkout(plan: str = "pro", email: str = "") -> CheckoutResponse:
    """Return a checkout URL for upgrading to `plan`.

    In stub mode (no Polar token) the URL points at our own confirm endpoint.
    """
    if plan not in PLANS or plan == "free":
        raise HTTPException(status_code=400, detail="Plan must be 'pro' or 'scale'")
    if not email:
        raise HTTPException(status_code=400, detail="Missing email")
    result = _checkout_url(plan, email)
    record_event(None, "checkout_started", source=None, campaign=None)
    return CheckoutResponse(
        plan=plan, email=email, checkout_url=result["url"], provider=result["provider"]
    )


@app.get("/v1/billing/confirm", tags=["Billing"])
def billing_confirm(request: Request, plan: str = "pro", email: str = ""):
    """Stub-mode simulated checkout success — upgrades the user's plan.

    Only meaningful until a real Polar.sh token is configured. In production
    (token set) this endpoint returns 404 and upgrades flow via the webhook.

    When the client accepts HTML (a browser), redirect back to /pricing with a
    success flag instead of returning raw JSON.
    """
    from fastapi.responses import RedirectResponse

    if plan not in PLANS or plan == "free":
        raise HTTPException(status_code=400, detail="Plan must be 'pro' or 'scale'")
    if not email:
        raise HTTPException(status_code=400, detail="Missing email")
    user = set_user_plan(email, plan)
    if user is None:
        raise HTTPException(status_code=404, detail="No account for that email — sign up first")
    record_event(user["api_key"], "checkout_completed")

    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse(url="/pricing?checkout=success&plan=" + plan, status_code=303)

    return ConfirmResponse(plan=plan, email=email, status="active")


@app.post("/v1/billing/webhook", tags=["Billing"])
async def billing_webhook(request: Request) -> dict:
    """Polar.sh webhook receiver. Updates a user's plan on payment events."""
    payload = await request.body()
    signature = request.headers.get("polar-signature") or request.headers.get(
        "x-polar-signature"
    )
    if not verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        event = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    result = handle_webhook_event(event)
    email, plan = result["email"], result["plan"]
    if not email or not plan:
        return {"received": True, "action": "ignored"}

    user = set_user_plan(email, plan)
    if user is None:
        # Account may not exist yet (checkout before signup) — record and move on.
        record_event(None, "webhook_unknown_user", campaign="polar")
        return {"received": True, "action": "no_such_user", "email": email}

    record_event(user["api_key"], "plan_upgraded", campaign="polar")
    return {"received": True, "action": "plan_updated", "email": email, "plan": plan}


# ── Events / conversion tracking ─────────────────────────────────────────


@app.post("/v1/events", tags=["Analytics"], status_code=202)
def events(request: EventRequest, x_api_key: str | None = None) -> dict:
    """Record a server-side event (conversion funnel / source attribution)."""
    api_key = x_api_key
    if api_key and get_user_by_api_key(api_key) is None:
        raise HTTPException(status_code=401, detail="Invalid or unknown API key")
    record_event(api_key, request.event_type, source=request.source, campaign=request.campaign)
    return {"accepted": True, "event_type": request.event_type}


# ── Analytics (daily-report / weekly bilan) ──────────────────────────────


@app.get("/v1/stats", tags=["Analytics"])
def stats() -> dict:
    """Aggregate stats for MRR / funnel reporting (public, non-sensitive)."""
    from .db import dump_stats

    data = dump_stats()
    users_by_plan = data["users_by_plan"]
    mrr = sum(PLANS[p]["price"] * n for p, n in users_by_plan.items() if p in PLANS)
    return {
        "mrr_usd": mrr,
        "users_by_plan": users_by_plan,
        "total_users": sum(users_by_plan.values()),
        "events_by_type": data["events_by_type"],
        "events_by_source": data["events_by_source"],
    }


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
