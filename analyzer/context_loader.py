"""Context loader for recent messages from Postgres."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, List, AsyncIterator

import asyncpg


@dataclass(frozen=True)
class MessageRow:
    sender_id: str
    message_id: int
    date: datetime
    text: Optional[str]


@dataclass(frozen=True)
class MessageKey:
    date: datetime
    message_id: int
    sender_id: str


@dataclass(frozen=True)
class MessageBatch:
    rows: List[MessageRow]
    text: str
    first_key: MessageKey
    last_key: MessageKey
    char_count: int
    token_estimate: int


def _format_message(row: MessageRow, max_chars: int) -> str:
    safe_text = (row.text or "").replace("\n", " ").strip()
    if len(safe_text) > max_chars:
        safe_text = f"{safe_text[:max_chars]}…"
    ts = row.date.strftime("%Y-%m-%d %H:%M")
    return f"[{ts}] {row.sender_id} (id={row.message_id}): {safe_text}"


def format_messages(rows: Iterable[MessageRow], max_chars: int = 400) -> str:
    return "\n".join(_format_message(r, max_chars=max_chars) for r in rows)


def estimate_tokens(text: str) -> int:
    # Approximate token count to manage batch sizes without a tokenizer.
    return max(1, len(text) // 4)


async def iter_message_rows(
    pg_dsn: str,
    sender_id: Optional[str] = None,
    days_back: int = 30,
    page_size: int = 2000,
    start_key: Optional[MessageKey] = None,
    max_messages: Optional[int] = None,
) -> AsyncIterator[MessageRow]:
    """Yield messages in chronological order using keyset pagination."""
    since: Optional[datetime]
    if days_back and days_back > 0:
        since = datetime.now(timezone.utc) - timedelta(days=days_back)
    else:
        since = None

    last_key = start_key
    yielded = 0

    use_sender_tiebreaker = sender_id is None

    async with asyncpg.create_pool(pg_dsn) as pool:
        async with pool.acquire() as conn:
            while True:
                params: list[object] = []
                where: list[str] = []

                if since is not None:
                    params.append(since)
                    where.append(f"date >= ${len(params)}")

                if sender_id:
                    params.append(sender_id)
                    where.append(f"sender_id = ${len(params)}")

                if last_key is not None:
                    if use_sender_tiebreaker:
                        params.extend([last_key.date, last_key.message_id, last_key.sender_id])
                        date_idx = len(params) - 2
                        id_idx = len(params) - 1
                        sender_idx = len(params)
                        where.append(
                            "("
                            f"date > ${date_idx} "
                            f"OR (date = ${date_idx} AND id > ${id_idx}) "
                            f"OR (date = ${date_idx} AND id = ${id_idx} AND sender_id::text > ${sender_idx})"
                            ")"
                        )
                    else:
                        params.extend([last_key.date, last_key.message_id])
                        date_idx = len(params) - 1
                        id_idx = len(params)
                        where.append(
                            "("
                            f"date > ${date_idx} "
                            f"OR (date = ${date_idx} AND id > ${id_idx})"
                            ")"
                        )

                where_clause = f" WHERE {' AND '.join(where)}" if where else ""
                params.append(page_size)
                limit_idx = len(params)

                order_by = "ORDER BY date ASC, id ASC"
                if use_sender_tiebreaker:
                    order_by += ", sender_id::text ASC"

                query = (
                    "SELECT sender_id, id, date, text FROM messages "
                    f"{where_clause} "
                    f"{order_by} LIMIT ${limit_idx}"
                )

                rows = await conn.fetch(query, *params)
                if not rows:
                    break

                for row in rows:
                    yield MessageRow(
                        sender_id=str(row["sender_id"]),
                        message_id=int(row["id"]),
                        date=row["date"],
                        text=row["text"],
                    )
                    yielded += 1
                    if max_messages is not None and yielded >= max_messages:
                        return

                last = rows[-1]
                last_key = MessageKey(
                    date=last["date"],
                    message_id=int(last["id"]),
                    sender_id=str(last["sender_id"]),
                )

                if len(rows) < page_size:
                    break


async def iter_message_batches(
    pg_dsn: str,
    sender_id: Optional[str] = None,
    days_back: int = 30,
    page_size: int = 2000,
    max_message_chars: int = 400,
    max_batch_chars: int = 60000,
    max_batch_tokens: int = 15000,
    start_key: Optional[MessageKey] = None,
    max_messages: Optional[int] = None,
) -> AsyncIterator[MessageBatch]:
    """Yield formatted message batches constrained by char/token budgets."""
    buffer: List[MessageRow] = []
    buffer_lines: List[str] = []
    buffer_chars = 0
    buffer_tokens = 0
    first_key: Optional[MessageKey] = None

    async for row in iter_message_rows(
        pg_dsn=pg_dsn,
        sender_id=sender_id,
        days_back=days_back,
        page_size=page_size,
        start_key=start_key,
        max_messages=max_messages,
    ):
        formatted = _format_message(row, max_chars=max_message_chars)
        line_chars = len(formatted) + 1
        line_tokens = estimate_tokens(formatted)

        if buffer and (
            buffer_chars + line_chars > max_batch_chars
            or buffer_tokens + line_tokens > max_batch_tokens
        ):
            batch_text = "\n".join(buffer_lines)
            last_key = MessageKey(
                date=buffer[-1].date,
                message_id=buffer[-1].message_id,
                sender_id=buffer[-1].sender_id,
            )
            if first_key is None:
                first_key = last_key
            yield MessageBatch(
                rows=list(buffer),
                text=batch_text,
                first_key=first_key,
                last_key=last_key,
                char_count=buffer_chars,
                token_estimate=buffer_tokens,
            )
            buffer = []
            buffer_lines = []
            buffer_chars = 0
            buffer_tokens = 0
            first_key = None

        if first_key is None:
            first_key = MessageKey(
                date=row.date,
                message_id=row.message_id,
                sender_id=row.sender_id,
            )

        buffer.append(row)
        buffer_lines.append(formatted)
        buffer_chars += line_chars
        buffer_tokens += line_tokens

    if buffer:
        batch_text = "\n".join(buffer_lines)
        last_key = MessageKey(
            date=buffer[-1].date,
            message_id=buffer[-1].message_id,
            sender_id=buffer[-1].sender_id,
        )
        if first_key is None:
            first_key = last_key
        yield MessageBatch(
            rows=list(buffer),
            text=batch_text,
            first_key=first_key,
            last_key=last_key,
            char_count=buffer_chars,
            token_estimate=buffer_tokens,
        )


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
    since: Optional[datetime]
    if days_back and days_back > 0:
        since = datetime.now(timezone.utc) - timedelta(days=days_back)
    else:
        since = None

    query = "SELECT sender_id, id, date, text FROM messages "

    # params may contain mixed types (datetime plus optional sender_id and int limit)
    from typing import Any

    params: list[Any] = []
    conditions: list[str] = []

    if since is not None:
        params.append(since)
        conditions.append(f"date >= ${len(params)}")

    if sender_id:
        params.append(sender_id)
        conditions.append(f"sender_id = ${len(params)}")

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    limit_param = f"${len(params)}"

    query += f"{where_clause} ORDER BY date DESC LIMIT {limit_param}"

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
