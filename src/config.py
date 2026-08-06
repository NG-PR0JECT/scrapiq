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

    # User agent
    USER_AGENT: str = os.getenv(
        "SCRAPIQ_USER_AGENT",
        "Mozilla/5.0 (compatible; Scrapiq/0.1; +https://github.com/NG-PR0JECT/scrapiq)",
    )


settings = Settings()
