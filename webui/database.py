"""Database utilities for web UI."""

from __future__ import annotations

import os
from typing import Optional
from contextlib import asynccontextmanager

try:
    import asyncpg
except ImportError:
    asyncpg = None

# Default PostgreSQL DSN - can be overridden via environment
DEFAULT_PG_DSN = os.getenv(
    "PG_DSN",
    "postgresql://pguser:pgpass@localhost:5432/tgdata"
)

_pool: Optional["asyncpg.Pool"] = None


async def get_pool(dsn: str = DEFAULT_PG_DSN) -> "asyncpg.Pool":
    """Get or create the database connection pool."""
    global _pool
    if asyncpg is None:
        raise RuntimeError("asyncpg is not installed")
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
    return _pool


async def close_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


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
