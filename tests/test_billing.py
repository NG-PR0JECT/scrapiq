"""Tests for API keys, signup, quota, and billing (stub mode).

These exercise the FastAPI app end-to-end via TestClient against a fresh
temp SQLite DB — no network, no real payment.
"""

from tests.conftest import seed_usage, set_plan


class TestSignup:
    def test_signup_creates_key(self, client):
        resp = client.post("/v1/signup", json={"email": "a@b.com"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "a@b.com"
        assert body["api_key"].startswith("sk_")
        assert body["plan"] == "free"

    def test_signup_normalizes_email(self, client):
        resp = client.post("/v1/signup", json={"email": "  A@B.COM "})
        assert resp.status_code == 201
        assert resp.json()["email"] == "a@b.com"

    def test_signup_rejects_invalid_email(self, client):
        resp = client.post("/v1/signup", json={"email": "not-an-email"})
        assert resp.status_code == 422

    def test_signup_idempotent(self, client):
        first = client.post("/v1/signup", json={"email": "dup@x.com"}).json()
        second = client.post("/v1/signup", json={"email": "dup@x.com"}).json()
        assert first["api_key"] == second["api_key"]


class TestUsage:
    def test_usage_zero_after_signup(self, client, signed_up):
        _, key = signed_up
        resp = client.get("/v1/usage", params={"api_key": key})
        assert resp.status_code == 200
        body = resp.json()
        assert body["used"] == 0
        assert body["quota"] == 100
        assert body["plan"] == "free"

    def test_usage_invalid_key(self, client):
        resp = client.get("/v1/usage", params={"api_key": "sk_bogus"})
        assert resp.status_code == 401

    def test_usage_missing_key(self, client):
        resp = client.get("/v1/usage")
        assert resp.status_code == 400


class TestQuota:
    def test_extract_without_key_still_works(self, client):
        """Backwards-compat: anonymous requests remain allowed."""
        resp = client.post("/v1/extract", json={"url": "https://example.com", "format": "text"})
        # Extraction hits the network; we only assert it isn't blocked by auth.
        assert resp.status_code != 401
        assert resp.status_code != 429

    def test_extract_with_valid_key_increments_usage(self, client, signed_up):
        _, key = signed_up
        resp = client.post(
            "/v1/extract",
            json={"url": "https://example.com", "format": "text"},
            headers={"X-API-Key": key},
        )
        assert resp.status_code != 401
        usage = client.get("/v1/usage", params={"api_key": key}).json()
        assert usage["used"] == 1

    def test_extract_with_invalid_key_401(self, client):
        resp = client.post(
            "/v1/extract",
            json={"url": "https://example.com", "format": "text"},
            headers={"X-API-Key": "sk_wrong"},
        )
        assert resp.status_code == 401

    def test_free_quota_exceeded_429(self, client, signed_up):
        _, key = signed_up
        seed_usage(key, 100)
        resp = client.post(
            "/v1/extract",
            json={"url": "https://example.com", "format": "text"},
            headers={"X-API-Key": key},
        )
        assert resp.status_code == 429
        body = resp.json()
        assert body["quota"] == 100
        assert body["used"] == 100

    def test_pro_bypasses_quota_early_access(self, client, signed_up):
        _, key = signed_up
        set_plan(key, "pro")
        seed_usage(key, 150)  # > free quota
        resp = client.post(
            "/v1/extract",
            json={"url": "https://example.com", "format": "text"},
            headers={"X-API-Key": key},
        )
        # Pro is unlimited in early-access mode → not 429, not 401.
        assert resp.status_code not in (401, 429)


class TestBilling:
    def test_checkout_returns_stub_url(self, client, signed_up):
        email, _ = signed_up
        resp = client.get("/v1/billing/checkout", params={"plan": "pro", "email": email})
        assert resp.status_code == 200
        body = resp.json()
        assert "/v1/billing/confirm" in body["checkout_url"]
        assert body["provider"] in ("stub", "stub-fallback")

    def test_checkout_rejects_free_plan(self, client):
        resp = client.get("/v1/billing/checkout", params={"plan": "free", "email": "a@b.com"})
        assert resp.status_code == 400

    def test_confirm_upgrades_plan(self, client, signed_up):
        email, key = signed_up
        resp = client.get("/v1/billing/confirm", params={"plan": "pro", "email": email})
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"
        usage = client.get("/v1/usage", params={"api_key": key}).json()
        assert usage["plan"] == "pro"
        assert usage["quota"] is None  # unlimited in early access

    def test_confirm_unknown_email_404(self, client):
        resp = client.get("/v1/billing/confirm", params={"plan": "pro", "email": "ghost@x.com"})
        assert resp.status_code == 404

    def test_webhook_updates_plan(self, client, signed_up):
        email, key = signed_up
        event = {
            "type": "checkout.completed",
            "data": {"metadata": {"email": email, "plan": "scale"}},
        }
        resp = client.post("/v1/billing/webhook", json=event)
        assert resp.status_code == 200
        assert resp.json()["action"] == "plan_updated"
        usage = client.get("/v1/usage", params={"api_key": key}).json()
        assert usage["plan"] == "scale"

    def test_webhook_ignores_irrelevant_event(self, client):
        event = {"type": "subscription.canceled", "data": {}}
        resp = client.post("/v1/billing/webhook", json=event)
        assert resp.status_code == 200
        assert resp.json()["action"] == "ignored"


class TestEventsAndStats:
    def test_events_endpoint(self, client):
        resp = client.post("/v1/events", json={"event_type": "extract", "source": "hn"})
        assert resp.status_code == 202

    def test_stats_reports_mrr(self, client):
        client.post("/v1/signup", json={"email": "pro@x.com"})
        client.post("/v1/signup", json={"email": "free@x.com"})
        # upgrade pro@x.com via webhook
        client.post(
            "/v1/billing/webhook",
            json={"type": "checkout.completed", "data": {"metadata": {"email": "pro@x.com", "plan": "pro"}}},
        )
        resp = client.get("/v1/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["mrr_usd"] == 29
        assert body["users_by_plan"]["pro"] == 1
