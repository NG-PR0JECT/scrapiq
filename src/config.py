"""Application configuration."""

import os
from pathlib import Path


class Settings:
    """Scrapiq application settings."""

    # Server
    HOST: str = os.getenv("SCRAPIQ_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("SCRAPIQ_PORT", "8001"))

    # Extraction limits
    MAX_URL_LENGTH: int = 2048
    MAX_CONTENT_SIZE: int = 5 * 1024 * 1024  # 5 MB
    REQUEST_TIMEOUT: int = int(os.getenv("SCRAPIQ_REQUEST_TIMEOUT", "30"))

    # Rate limiting (free tier)
    FREE_TIER_DAILY_REQUESTS: int = 100

    # Cache
    CACHE_DIR: Path = Path(os.getenv("SCRAPIQ_CACHE_DIR", "/tmp/scrapiq-cache"))
    CACHE_TTL_SECONDS: int = 3600

    # Database (users, usage, events)
    DB_PATH: Path = Path(os.getenv("SCRAPIQ_DB_PATH", "data/scrapiq.db"))

    # Billing — Polar.sh (stub/early-access mode until a token is configured)
    POLAR_ACCESS_TOKEN: str | None = os.getenv("POLAR_ACCESS_TOKEN")
    POLAR_WEBHOOK_SECRET: str | None = os.getenv("POLAR_WEBHOOK_SECRET")
    POLAR_ORGANIZATION: str = os.getenv("POLAR_ORGANIZATION", "scrapiq")
    # Public base URL used to build checkout return/confirm URLs
    PUBLIC_BASE_URL: str = os.getenv("SCRAPIQ_PUBLIC_BASE_URL", "https://scrapiq.io")

    # User agent
    USER_AGENT: str = os.getenv(
        "SCRAPIQ_USER_AGENT",
        "Mozilla/5.0 (compatible; Scrapiq/0.1; +https://github.com/NG-PR0JECT/scrapiq)",
    )


# Pricing tiers. `daily_requests=None` means unlimited (early-access bypass
# until Stripe/Polar payment enforcement is switched on).
PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "daily_requests": 100,
        "rps": 2,
        "features": [
            "text + markdown output",
            "Basic JSON extraction",
            "Community support",
        ],
    },
    "pro": {
        "name": "Pro",
        "price": 29,
        "daily_requests": 10_000,
        "rps": 10,
        "features": [
            "text + markdown + JSON",
            "Custom schema extraction",
            "Webhooks",
            "Email support",
        ],
    },
    "scale": {
        "name": "Scale",
        "price": 99,
        "daily_requests": 100_000,
        "rps": 50,
        "features": [
            "Everything in Pro",
            "Multi-user / team",
            "Analytics",
            "Priority support",
        ],
    },
}


def plan_quota(plan: str) -> int | None:
    """Return the daily request quota for a plan, or None for unlimited.

    In early-access mode, Pro and Scale return None (no enforcement) until
    payment is wired up. Free always enforces its quota.
    """
    plan_cfg = PLANS.get(plan, PLANS["free"])
    # Early access: only "free" is rate-limited for now.
    if plan != "free":
        return None
    return plan_cfg["daily_requests"]


settings = Settings()
