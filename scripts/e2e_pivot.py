#!/usr/bin/env python3
"""End-to-end validation of the Scrapiq commercial pivot funnel.

Validates, against a running Scrapiq API:

  1. signup (free)            → API key issued
  2. pricing checkout (stub)  → checkout URL returned (test-mode Polar.sh)
  3. checkout completion      → plan upgraded to Pro (early-access, no real payment)
  4. usage endpoint           → reports Pro plan with unlimited quota

Quota-exceeded enforcement (free tier 429) is covered by tests/test_billing.py.

Usage:
    SCRAPIQ_BASE_URL=http://127.0.0.1:8001 python scripts/e2e_pivot.py

Defaults to http://127.0.0.1:8001. Fails with a non-zero exit code on any
step mismatch.
"""

from __future__ import annotations

import os
import sys
import uuid
from urllib.parse import urlparse

import httpx

BASE = os.getenv("SCRAPIQ_BASE_URL", "http://127.0.0.1:8001").rstrip("/")

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}  {detail}")


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=30)
    email = f"e2e-{uuid.uuid4().hex[:10]}@example.com"

    print(f"Scrapiq pivot E2E — base URL: {BASE}\n")

    # 1. Signup (free)
    print("[1] signup (free)")
    r = client.post("/v1/signup", json={"email": email})
    check("signup 201", r.status_code == 201, f"got {r.status_code}: {r.text}")
    body = r.json()
    api_key = body.get("api_key", "")
    check("api_key issued", api_key.startswith("sk_"), api_key)
    check("default plan free", body.get("plan") == "free", str(body))

    # 2. Checkout (stub / test-mode Polar.sh)
    print("[2] billing checkout (test mode)")
    r = client.get("/v1/billing/checkout", params={"plan": "pro", "email": email})
    check("checkout 200", r.status_code == 200, f"got {r.status_code}: {r.text}")
    checkout = r.json()
    checkout_url = checkout.get("checkout_url", "")
    check("checkout_url present", bool(checkout_url), str(checkout))
    check("stub provider", checkout.get("provider") in ("stub", "stub-fallback"), str(checkout))

    # 3. Complete the checkout (stub confirm endpoint simulates payment).
    #    The checkout_url points at the public base URL; re-point its path at
    #    BASE so this works against any test/staging host too.
    print("[3] complete checkout (simulated payment)")
    parsed = urlparse(checkout_url)
    confirm_path = parsed.path + ("?" + parsed.query if parsed.query else "")
    r = client.get(confirm_path)
    check("confirm 200", r.status_code == 200, f"got {r.status_code}: {r.text}")
    check("confirm status active", r.json().get("status") == "active", str(r.json()))

    # 4. Usage reflects Pro plan (unlimited in early access)
    print("[4] usage reflects Pro")
    r = client.get("/v1/usage", params={"api_key": api_key})
    check("usage 200", r.status_code == 200, f"got {r.status_code}: {r.text}")
    usage = r.json()
    check("plan == pro", usage.get("plan") == "pro", str(usage))
    check("quota unlimited (None)", usage.get("quota") is None, str(usage))

    # 5. Authenticated extract works with the Pro key
    print("[5] authenticated extract (Pro key)")
    r = client.post(
        "/v1/extract",
        json={"url": "https://example.com", "format": "text"},
        headers={"X-API-Key": api_key},
    )
    check("extract not blocked", r.status_code not in (401, 429), f"got {r.status_code}")

    print(f"\nResult: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
