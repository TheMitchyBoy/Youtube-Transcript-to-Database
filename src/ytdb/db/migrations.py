from __future__ import annotations

import logging

from sqlalchemy import text

from ytdb.db.engine import create_db_engine

logger = logging.getLogger(__name__)

_MIGRATIONS = (
    "ALTER TABLE videos ADD COLUMN IF NOT EXISTS content_type VARCHAR(16) DEFAULT 'video'",
    "ALTER TABLE videos ADD COLUMN IF NOT EXISTS is_live BOOLEAN DEFAULT FALSE",
    "ALTER TABLE sync_jobs ADD COLUMN IF NOT EXISTS include_videos BOOLEAN DEFAULT TRUE",
    "ALTER TABLE sync_jobs ADD COLUMN IF NOT EXISTS include_streams BOOLEAN DEFAULT TRUE",
    "ALTER TABLE sync_jobs ADD COLUMN IF NOT EXISTS include_live BOOLEAN DEFAULT TRUE",
)


def run_migrations(database_url: str) -> None:
    if not database_url.startswith("postgresql"):
        return

    engine = create_db_engine(database_url)
    with engine.begin() as connection:
        for statement in _MIGRATIONS:
            try:
                connection.execute(text(statement))
            except Exception:
                logger.exception("Migration failed: %s", statement)
