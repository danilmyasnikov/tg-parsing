"""Context loader for recent messages from Postgres."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, List

import asyncpg


@dataclass(frozen=True)
class MessageRow:
    sender_id: str
    message_id: int
    date: datetime
    text: Optional[str]


def _format_message(row: MessageRow, max_chars: int) -> str:
    safe_text = (row.text or "").replace("\n", " ").strip()
    if len(safe_text) > max_chars:
        safe_text = f"{safe_text[:max_chars]}…"
    ts = row.date.strftime("%Y-%m-%d %H:%M")
    return f"[{ts}] {row.sender_id}: {safe_text}"


def format_messages(rows: Iterable[MessageRow], max_chars: int = 400) -> str:
    return "\n".join(_format_message(r, max_chars=max_chars) for r in rows)


async def load_recent_messages(
    pg_dsn: str,
    sender_id: Optional[str] = None,
    days_back: int = 30,
    limit: int = 1000,
    max_chars: int = 400,
) -> str:
    """Load recent messages and format them for LLM input."""
    # Use an aware UTC timestamp so comparisons with timestamptz columns
    # in Postgres behave as expected.
    since = datetime.now(timezone.utc) - timedelta(days=days_back)

    query = (
        "SELECT sender_id, id, date, text FROM messages "
        "WHERE date >= $1 "
    )
    # params may contain mixed types (datetime plus optional sender_id and int limit)
    from typing import Any

    params: list[Any] = [since]

    if sender_id:
        query += "AND sender_id = $2 "
        params.append(sender_id)
        limit_param = "$3"
    else:
        limit_param = "$2"

    query += f"ORDER BY date DESC LIMIT {limit_param}"
    params.append(limit)

    async with asyncpg.create_pool(pg_dsn) as pool:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            # If the date filter returned no rows (e.g., small `days_back`),
            # fall back to returning the most recent `limit` rows so the
            # analyzer still has data to work with.
            if not rows:
                rows = await conn.fetch(
                    "SELECT sender_id, id, date, text FROM messages ORDER BY date DESC LIMIT $1",
                    limit,
                )

    message_rows: List[MessageRow] = [
        MessageRow(
            sender_id=str(r["sender_id"]),
            message_id=int(r["id"]),
            date=r["date"],
            text=r["text"],
        )
        for r in rows
    ]

    # Reverse to get chronological order in the prompt
    message_rows.reverse()
    return format_messages(message_rows, max_chars=max_chars)
