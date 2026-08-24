"""SQLite persistence layer for users, usage, and events.

A single connection per operation is used so the module is safe to call from
async FastAPI handlers (which run in a thread pool). WAL mode keeps concurrent
writes cheap. Tables are created lazily on first use.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import settings

_DB_PATH: Path | None = None


def configure(db_path: str | Path | None = None) -> Path:
    """Set (and return) the active DB path. Tests call this to use a temp file."""
    global _DB_PATH
    _DB_PATH = Path(db_path) if db_path else Path(settings.DB_PATH)
    return _DB_PATH


def db_path() -> Path:
    """Return the active DB path (configuring the default on first call)."""
    global _DB_PATH
    if _DB_PATH is None:
        configure()
    assert _DB_PATH is not None
    return _DB_PATH


@contextmanager
def _connect():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _init_schema(conn)
        yield conn
    finally:
        conn.close()


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            api_key TEXT NOT NULL UNIQUE,
            plan TEXT NOT NULL DEFAULT 'free',
            created_at TEXT NOT NULL,
            stripe_customer_id TEXT
        );

        CREATE TABLE IF NOT EXISTS usage (
            api_key TEXT NOT NULL,
            date TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (api_key, date)
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            event_type TEXT NOT NULL,
            source TEXT,
            campaign TEXT,
            timestamp TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_api_key ON events(api_key);
        CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
        """
    )
    conn.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def generate_api_key() -> str:
    """Return a fresh API key, e.g. sk_live_<32 random url-safe chars>."""
    return "sk_" + secrets.token_urlsafe(32)


# ── Users ────────────────────────────────────────────────────────────────


def create_user(email: str, plan: str = "free") -> dict:
    """Create a user with a fresh API key. Returns the full row as a dict."""
    email = email.strip().lower()
    api_key = generate_api_key()
    created_at = _now_iso()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO users (email, api_key, plan, created_at) VALUES (?, ?, ?, ?)",
            (email, api_key, plan, created_at),
        )
        conn.commit()
    return get_user_by_email(email)


def get_user_by_email(email: str) -> dict | None:
    email = email.strip().lower()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_api_key(api_key: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE api_key = ?", (api_key,)
        ).fetchone()
    return dict(row) if row else None


def set_user_plan(email: str, plan: str) -> dict | None:
    """Update a user's plan (used by the billing webhook)."""
    email = email.strip().lower()
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE users SET plan = ? WHERE email = ?", (plan, email)
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
    return get_user_by_email(email)


def set_user_customer_id(email: str, customer_id: str) -> None:
    email = email.strip().lower()
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET stripe_customer_id = ? WHERE email = ?",
            (customer_id, email),
        )
        conn.commit()


def count_users_by_plan() -> dict[str, int]:
    """Return {plan: count} for the whole user table (MRR reporting)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT plan, COUNT(*) AS n FROM users GROUP BY plan"
        ).fetchall()
    return {r["plan"]: r["n"] for r in rows}


# ── Usage / quota ────────────────────────────────────────────────────────


def _increment_usage(conn: sqlite3.Connection, api_key: str) -> int:
    """Atomically increment today's usage count for a key. Returns new count."""
    today = _today()
    conn.execute(
        """
        INSERT INTO usage (api_key, date, count) VALUES (?, ?, 1)
        ON CONFLICT(api_key, date) DO UPDATE SET count = count + 1
        """,
        (api_key, today),
    )
    conn.commit()
    row = conn.execute(
        "SELECT count FROM usage WHERE api_key = ? AND date = ?",
        (api_key, today),
    ).fetchone()
    return row["count"] if row else 0


def get_usage(api_key: str) -> dict:
    """Return {used, date, quota} for a key. quota=None means unlimited."""
    today = _today()
    with _connect() as conn:
        row = conn.execute(
            "SELECT count FROM usage WHERE api_key = ? AND date = ?",
            (api_key, today),
        ).fetchone()
    used = row["count"] if row else 0

    user = get_user_by_api_key(api_key)
    plan = user["plan"] if user else "free"
    quota = plan_quota(plan)

    return {"api_key": api_key, "plan": plan, "used": used, "quota": quota, "date": today}


def check_and_increment(api_key: str) -> dict:
    """Enforce quota for an authenticated request, then increment the counter.

    Returns {"allowed": bool, "plan": str, "used": int, "quota": int|None}.
    Free tier is rate-limited; Pro/Scale bypass in early-access mode.
    """
    user = get_user_by_api_key(api_key)
    if user is None:
        return {"allowed": False, "reason": "unknown_key", "plan": None, "used": 0, "quota": None}

    plan = user["plan"]
    quota = plan_quota(plan)

    if quota is not None:
        with _connect() as conn:
            today = _today()
            row = conn.execute(
                "SELECT count FROM usage WHERE api_key = ? AND date = ?",
                (api_key, today),
            ).fetchone()
            used = row["count"] if row else 0
            if used >= quota:
                return {
                    "allowed": False,
                    "reason": "quota_exceeded",
                    "plan": plan,
                    "used": used,
                    "quota": quota,
                }
            # Increment atomically (the ON CONFLICT upsert is idempotent-safe).
            new_count = _increment_usage(conn, api_key)
        return {"allowed": True, "plan": plan, "used": new_count, "quota": quota}

    # Unlimited (early access) — still count for analytics.
    with _connect() as conn:
        new_count = _increment_usage(conn, api_key)
    return {"allowed": True, "plan": plan, "used": new_count, "quota": None}


def plan_quota(plan: str) -> int | None:
    """Local import to avoid a cycle; mirrors config.plan_quota."""
    from .config import plan_quota as _plan_quota

    return _plan_quota(plan)


# ── Events (conversion tracking) ─────────────────────────────────────────


def record_event(
    api_key: str | None,
    event_type: str,
    source: str | None = None,
    campaign: str | None = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO events (api_key, event_type, source, campaign, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (api_key, event_type, source, campaign, _now_iso()),
        )
        conn.commit()


def event_counts(event_type: str | None = None) -> int:
    """Total number of events (optionally filtered by type)."""
    with _connect() as conn:
        if event_type:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM events WHERE event_type = ?", (event_type,)
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) AS n FROM events").fetchone()
    return row["n"] if row else 0


def events_by_source() -> dict[str, int]:
    """Return {source: count} for source attribution."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT source, COUNT(*) AS n FROM events "
            "WHERE source IS NOT NULL GROUP BY source ORDER BY n DESC"
        ).fetchall()
    return {r["source"]: r["n"] for r in rows}


def events_by_type() -> dict[str, int]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT event_type, COUNT(*) AS n FROM events GROUP BY event_type"
        ).fetchall()
    return {r["event_type"]: r["n"] for r in rows}


def dump_stats() -> dict:
    """Snapshot used by the daily-report / weekly bilan."""
    return {
        "users_by_plan": count_users_by_plan(),
        "events_by_type": events_by_type(),
        "events_by_source": events_by_source(),
    }


def to_jsonable(obj: object) -> str:
    return json.dumps(obj, default=str)
