"""Billing integration — Polar.sh checkout + webhook.

Design: a clean provider abstraction so the API never depends on Polar.sh
directly. Until a real `POLAR_ACCESS_TOKEN` is configured we run in
**stub / early-access mode**:

- `GET /v1/billing/checkout?plan=pro&email=...` returns a local "confirm" URL.
- Visiting that URL (or calling `GET /v1/billing/confirm`) simulates a
  successful checkout and upgrades the user's plan — no real payment.
- When `POLAR_ACCESS_TOKEN` is set, checkout links are created against the
  real Polar.sh API and `POST /v1/billing/webhook` validates the signature.

This keeps the whole funnel testable end-to-end with zero payment credentials.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import urllib.parse

import httpx

from .config import PLANS, settings

logger = logging.getLogger(__name__)

# product_id per plan — map to Polar.sh product IDs once configured
PRODUCT_IDS = {
    "pro": "scrapiq-pro-monthly",
    "scale": "scrapiq-scale-monthly",
}


def _stub_mode() -> bool:
    """True when no Polar access token is configured (early access)."""
    return not settings.POLAR_ACCESS_TOKEN


def checkout_url(plan: str, email: str, success_url: str | None = None) -> dict:
    """Return {"url": ..., "provider": "polar"|"stub"} for the given plan.

    In stub mode the returned URL points at our own /v1/billing/confirm
    endpoint which simulates a completed checkout.
    """
    plan = plan if plan in PLANS else "pro"
    email = email.strip().lower()

    if _stub_mode():
        base = settings.PUBLIC_BASE_URL.rstrip("/")
        params = urllib.parse.urlencode({"plan": plan, "email": email})
        return {"url": f"{base}/v1/billing/confirm?{params}", "provider": "stub"}

    # Real Polar.sh checkout session
    # https://docs.polar.sh/api-reference/endpoints/checkout-links/create
    product_id = PRODUCT_IDS.get(plan)
    payload = {
        "product_id": product_id,
        "customer_email": email,
        "success_url": success_url or f"{settings.PUBLIC_BASE_URL.rstrip('/')}/pricing?checkout=success",
        "metadata": {"plan": plan, "email": email},
    }
    headers = {
        "Authorization": f"Bearer {settings.POLAR_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        resp = httpx.post(
            "https://api.polar.sh/v1/checkouts/",
            json=payload,
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        url = data.get("url") or data.get("checkout_url")
        if not url:
            logger.error("Polar checkout response missing URL: %s", data)
            raise ValueError("Polar.sh returned no checkout URL")
        return {"url": url, "provider": "polar"}
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.exception("Polar.sh checkout creation failed")
        # Fall back to stub so the funnel never hard-fails in early access.
        base = settings.PUBLIC_BASE_URL.rstrip("/")
        params = urllib.parse.urlencode({"plan": plan, "email": email})
        return {"url": f"{base}/v1/billing/confirm?{params}", "provider": "stub-fallback"}


def verify_webhook_signature(payload: bytes, signature_header: str | None) -> bool:
    """Validate a Polar.sh webhook using the configured secret.

    Polar signs with the `webhook-id` / `webhook-signature` scheme; the
    simplest supported check here is an HMAC-SHA256 of the raw body with the
    shared secret. Returns True in stub mode (no secret configured).
    """
    if _stub_mode() or not settings.POLAR_WEBHOOK_SECRET:
        return True
    if not signature_header:
        return False
    digest = hmac.new(
        settings.POLAR_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature_header)


def handle_webhook_event(event: dict) -> dict:
    """Map a Polar.sh webhook event to a plan change.

    Returns {"email": ..., "plan": ...} when the event carries a plan upgrade,
    or {"email": None, "plan": None} when it should be ignored.
    """
    event_type = event.get("type") or event.get("event_type") or ""

    # Polar.sh checkout events carry metadata we set at creation time.
    metadata = event.get("data", {}).get("metadata", {}) if isinstance(event.get("data"), dict) else {}
    email = metadata.get("email")
    plan = metadata.get("plan")

    # subscription.* events reference a customer email directly
    if not email:
        data = event.get("data", {}) if isinstance(event.get("data"), dict) else {}
        customer = data.get("customer", {}) if isinstance(data, dict) else {}
        if isinstance(customer, dict):
            email = customer.get("email")
        if not email and isinstance(data, dict):
            email = data.get("customer_email") or data.get("email")
    if not plan:
        plan = (event.get("data", {}).get("product", {}).get("metadata", {}).get("plan")
                if isinstance(event.get("data"), dict) else None)

    relevant = any(
        key in event_type
        for key in ("checkout.completed", "order.created", "subscription.created",
                    "subscription.active", "subscription.updated")
    )
    if not relevant:
        return {"email": None, "plan": None}

    plan = plan if plan in PLANS else None
    return {"email": email, "plan": plan}
