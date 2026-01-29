from __future__ import annotations
from telethon.tl.custom.message import Message
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING
try:
    import asyncpg
except Exception:
    asyncpg = None

if TYPE_CHECKING:
    from asyncpg.pool import Pool as AsyncpgPool
else:
    class AsyncpgPool:  # runtime fallback for editors that evaluate symbols
        pass

# Module-level asyncpg pool (optional)
_pg_pool: AsyncpgPool | None = None
_pg_lock: asyncio.Lock = asyncio.Lock()


async def init_pg_pool(dsn: str, min_size: int = 1, max_size: int = 10) -> AsyncpgPool:
    """Initialize and return a module-level asyncpg pool.

    Raises a RuntimeError if `asyncpg` is not installed.
    """
    global _pg_pool, _pg_lock
    if asyncpg is None:
        raise RuntimeError('asyncpg is not installed; add it to requirements')
    if _pg_pool is None:
        async with _pg_lock:
            if _pg_pool is None:
                _pg_pool = await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)
    return _pg_pool


async def close_pg_pool() -> None:
    """Close the module-level asyncpg pool if initialized."""
    global _pg_pool
    if _pg_pool is not None:
        await _pg_pool.close()
        _pg_pool = None


async def postgres_store(m: Message, pool: AsyncpgPool | None = None, dsn: str | None = None) -> None:
    """Store a message record into PostgreSQL using `asyncpg`.

    Usage patterns:
    - Call `await init_pg_pool(dsn)` once at startup, then pass nothing here.
    - Or pass an explicit `pool=` object created by `asyncpg.create_pool`.
    - Or pass `dsn=` to lazily initialize the module pool.
    """
    if asyncpg is None:
        raise RuntimeError('asyncpg is not installed; cannot use postgres_store')

    p = pool or _pg_pool
    if p is None:
        if dsn:
            p = await init_pg_pool(dsn)
        else:
            raise RuntimeError('Postgres pool not initialized; call init_pg_pool(dsn) or pass pool=')

    mid = getattr(m, 'id', None)
    date = getattr(m, 'date', None)
    sender = getattr(m, 'sender_id', None)
    text = (getattr(m, 'text', '') or '').replace('\n', ' ')
    has_media = bool(getattr(m, 'media', None))

    # prefer native datetime when possible; asyncpg will accept str or datetime
    date_val = None
    if date is not None:
        try:
            date_val = date
        except Exception:
            date_val = str(date)

    async with p.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id BIGINT PRIMARY KEY,
                date TIMESTAMP WITH TIME ZONE,
                sender_id BIGINT,
                text TEXT,
                has_media BOOLEAN
            )
            """
        )
        await conn.execute(
            """
            INSERT INTO messages (id, date, sender_id, text, has_media)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
            SET date = EXCLUDED.date,
                sender_id = EXCLUDED.sender_id,
                text = EXCLUDED.text,
                has_media = EXCLUDED.has_media
            """,
            mid,
            date_val,
            sender,
            text,
            has_media,
        )


async def print_store(m: Message) -> None:
    """Async console storage used by small runners/tests.

    Consolidates message printing here and uses `getattr` to avoid
    attribute errors when fields are missing.
    """
    print('--- Latest message ---')
    mid = getattr(m, 'id', None)
    date = getattr(m, 'date', None)
    sender = getattr(m, 'sender_id', None)
    text = (getattr(m, 'text', '') or '').replace('\n', ' ')
    has_media = bool(getattr(m, 'media', None))

    print('id:', mid)
    print('date:', date)
    print('sender_id:', sender)
    print('text:', text)
    if has_media:
        print('Has media: yes (not downloaded)')

