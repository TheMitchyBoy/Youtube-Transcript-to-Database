from __future__ import annotations

import os
from urllib.parse import parse_qs, urlparse

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_SSL_REQUIRED_HOSTS = (
    "render.com",
    "neon.tech",
    "supabase.co",
    "rlwy.net",
    "amazonaws.com",
)


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://") :]
    return database_url


def get_sslmode(database_url: str) -> str | None:
    explicit = os.getenv("DB_SSLMODE")
    if explicit:
        return explicit

    parsed = urlparse(database_url)
    query = parse_qs(parsed.query)
    if "sslmode" in query:
        return query["sslmode"][0]

    hostname = parsed.hostname or ""

    # Railway private networking does not use TLS between services.
    if hostname.endswith(".railway.internal"):
        return None

    if any(marker in hostname for marker in _SSL_REQUIRED_HOSTS):
        return "require"

    return None


def get_connect_args(database_url: str) -> dict[str, str]:
    sslmode = get_sslmode(database_url)
    if sslmode:
        return {"sslmode": sslmode}
    return {}


def create_db_engine(database_url: str) -> Engine:
    normalized = normalize_database_url(database_url)
    return create_engine(
        normalized,
        pool_pre_ping=True,
        connect_args=get_connect_args(normalized),
    )
