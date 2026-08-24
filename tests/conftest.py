"""Shared pytest fixtures — temp DB + TestClient per test."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from src import db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A TestClient backed by a fresh temp SQLite DB, isolated per test."""
    db_file = tmp_path / "scrapiq-test.db"
    db.configure(db_file)

    # Prevent settings from leaking a stale path during this test.
    from src import main  # noqa: F401  (imports app, calls configure() again)

    with TestClient(main.app) as c:
        yield c


@pytest.fixture()
def signed_up(client):
    """Create a user via the API and return (email, api_key)."""
    email = "test@example.com"
    resp = client.post("/v1/signup", json={"email": email})
    assert resp.status_code == 201, resp.text
    return email, resp.json()["api_key"]


def seed_usage(api_key: str, count: int) -> None:
    """Directly set today's usage count for a key (for quota-over tests)."""
    conn = sqlite3.connect(str(db.db_path()))
    conn.execute(
        """
        INSERT INTO usage (api_key, date, count) VALUES (?, date('now'), ?)
        ON CONFLICT(api_key, date) DO UPDATE SET count = excluded.count
        """,
        (api_key, count),
    )
    conn.commit()
    conn.close()


def set_plan(api_key: str, plan: str) -> None:
    """Directly set a user's plan (for early-access bypass tests)."""
    conn = sqlite3.connect(str(db.db_path()))
    conn.execute("UPDATE users SET plan = ? WHERE api_key = ?", (plan, api_key))
    conn.commit()
    conn.close()
