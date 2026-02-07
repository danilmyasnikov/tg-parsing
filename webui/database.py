"""Database utilities for web UI."""

from __future__ import annotations

import os

try:
    import asyncpg
except ImportError:
    asyncpg = None

# Reuse the canonical pool helpers from collector.storage.postgres_store
from collector.storage.postgres_store import init_pg_pool, close_pg_pool

# Default PostgreSQL DSN - can be overridden via environment
DEFAULT_PG_DSN = os.getenv(
    "PG_DSN",
    "postgresql://pguser:pgpass@localhost:5432/tgdata"
)



async def get_pool(dsn: str = DEFAULT_PG_DSN) -> "asyncpg.Pool":
    """Get or create the database connection pool.

    This delegates to the shared pool initializer in
    `collector.storage.postgres_store.init_pg_pool` so the project has a
    single canonical pool implementation.
    """
    if asyncpg is None:
        raise RuntimeError("asyncpg is not installed")
    return await init_pg_pool(dsn)


async def close_pool() -> None:
    """Close the shared database connection pool via collector.storage."""
    await close_pg_pool()


async def get_unique_senders() -> list[dict]:
    """Get unique senders from the messages table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT sender_id, COUNT(*) as message_count
            FROM messages
            GROUP BY sender_id
            ORDER BY sender_id
            """
        )
        return [{"sender_id": row["sender_id"], "message_count": row["message_count"]} for row in rows]


async def get_messages_by_senders(sender_ids: list[str], limit: int = 100) -> list[dict]:
    """Get messages from specified senders."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT sender_id, id, date, text, has_media
            FROM messages
            WHERE sender_id = ANY($1)
            ORDER BY date DESC
            LIMIT $2
            """,
            sender_ids,
            limit,
        )
        return [
            {
                "sender_id": row["sender_id"],
                "id": row["id"],
                "date": row["date"].isoformat() if row["date"] else None,
                "text": row["text"],
                "has_media": row["has_media"],
            }
            for row in rows
        ]
