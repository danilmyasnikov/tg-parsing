"""
Async Postgres helpers for reading Telegram messages.
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import asyncpg

log = logging.getLogger(__name__)


@dataclass
class Message:
    id: int
    sender_id: Optional[int]
    date: str
    text: str


async def fetch_messages(
    pg_dsn: str,
    *,
    sender_id: Optional[int] = None,
    days_back: int = 0,
    max_messages: int = 0,
    max_message_chars: int = 500,
    page_size: int = 2000,
) -> list[Message]:
    """Fetch messages from the DB, newest first."""
    conn = await asyncpg.connect(pg_dsn)
    try:
        clauses = []
        args: list = []
        idx = 1

        if sender_id:
            clauses.append(f"sender_id = ${idx}")
            args.append(sender_id)
            idx += 1

        if days_back > 0:
            clauses.append(f"date >= NOW() - INTERVAL '{days_back} days'")

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        limit = f"LIMIT {max_messages}" if max_messages > 0 else ""

        query = f"""
            SELECT id, sender_id, date::text, COALESCE(LEFT(text, {max_message_chars}), '') as text
            FROM messages
            {where}
            ORDER BY date DESC
            {limit}
        """
        log.info("Fetching messages: %s  args=%s", query.strip()[:200], args)
        rows = await conn.fetch(query, *args)
        messages = [
            Message(id=r["id"], sender_id=r["sender_id"], date=r["date"], text=r["text"])
            for r in rows
            if r["text"] and r["text"].strip()
        ]
        log.info("Fetched %d non-empty messages", len(messages))
        return messages
    finally:
        await conn.close()
