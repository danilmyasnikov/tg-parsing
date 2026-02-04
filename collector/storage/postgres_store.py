from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
from contextlib import asynccontextmanager

try:
    import asyncpg
except ImportError:
    asyncpg = None

if TYPE_CHECKING:
    from asyncpg.pool import Pool as AsyncpgPool
    # Telethon Message type for static typing (import only during type checking)
    from telethon.tl.custom.message import Message as TgMessage
    from ..normalize import NormalizedMessage
else:
    class AsyncpgPool:  # runtime fallback for editors that evaluate symbols
        pass

# Module-level asyncpg pool (optional)
_pg_pool: AsyncpgPool | None = None
# Lock used to serialize lazy initialization of the module-level pool.
# Shared `asyncio.Lock` ensures only one coroutine performs creation when
# multiple coroutines attempt initialization concurrently.
_pg_lock: asyncio.Lock = asyncio.Lock()


async def init_pg_pool(dsn: str, min_size: int = 1, max_size: int = 10) -> AsyncpgPool:
    """Initialize and return a module-level asyncpg pool.

    Raises a RuntimeError if `asyncpg` is not installed.
    """
    global _pg_pool, _pg_lock
    if asyncpg is None:
        raise RuntimeError('asyncpg is not installed; add it to requirements')
    # Fast-path: avoid acquiring the lock if the pool is already initialized.
    if _pg_pool is None:
        # Acquire the shared lock so only one coroutine will perform creation.
        # Using `async with` makes acquisition/release automatic even on error.
        async with _pg_lock:
            # Inside the lock do a second check (double-checked locking).
            # Two or more coroutines can pass the outer `if` concurrently; the
            # inner check guarantees only the coroutine that holds the lock
            # will create and assign `_pg_pool`.
            if _pg_pool is None:
                _pg_pool = await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)
    return _pg_pool


async def close_pg_pool() -> None:
    """Close the module-level asyncpg pool if initialized."""
    global _pg_pool
    if _pg_pool is not None:
        await _pg_pool.close()
        _pg_pool = None


@asynccontextmanager
async def pg_pool_context(pg_dsn: str, min_size: int = 1, max_size: int = 10):
    """Async context manager that initializes the module-level PG pool.

    The context will call `init_pg_pool(pg_dsn, ...)` on entry and
    `close_pg_pool()` on exit.
    """
    if asyncpg is None:
        raise RuntimeError('asyncpg is not installed; add it to requirements')

    # initialize module-level pool (may reuse existing pool)
    await init_pg_pool(pg_dsn, min_size=min_size, max_size=max_size)
    try:
        yield _pg_pool
    finally:
        await close_pg_pool()


async def postgres_store(m: 'NormalizedMessage', pool: AsyncpgPool | None = None, dsn: str | None = None) -> None:
    """Store a message record into PostgreSQL using `asyncpg`.

    This function mirrors the previous `postgres_store` from the top-level storage.
    """
    if asyncpg is None:
        raise RuntimeError('asyncpg is not installed; cannot use postgres_store')

    p = pool or _pg_pool
    if p is None:
        if dsn:
            p = await init_pg_pool(dsn)
        else:
            raise RuntimeError('Postgres pool not initialized; call init_pg_pool(dsn) or pass pool=')

    # This function expects a NormalizedMessage produced by
    # `collector.normalize.normalize_message()`; callers must ensure
    # messages are normalized before calling this function.
    nm = m

    async with p.acquire() as conn:
        # Use a composite primary key (sender_id, id) so message ids are
        # unique per sender/chat and cannot collide across different senders.
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                sender_id TEXT,
                id BIGINT,
                date TIMESTAMP WITH TIME ZONE,
                text TEXT,
                has_media BOOLEAN,
                PRIMARY KEY (sender_id, id)
            )
            """
        )
        await conn.execute(
            """
            INSERT INTO messages (sender_id, id, date, text, has_media)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (sender_id, id) DO UPDATE
            SET date = EXCLUDED.date,
                text = EXCLUDED.text,
                has_media = EXCLUDED.has_media
            """,
            nm.sender,
            nm.id,
            nm.date,
            nm.text,
            nm.has_media,
        )
