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

# Encapsulate pool lifecycle in a manager class. Keep the old
# module-level compatibility functions for existing callers.


class PostgresPoolManager:
    """Manage a single asyncpg pool with lazy init and a lock."""

    def __init__(self) -> None:
        self._pool: AsyncpgPool | None = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def init(self, dsn: str, min_size: int = 1, max_size: int = 10) -> AsyncpgPool:
        if asyncpg is None:
            raise RuntimeError('asyncpg is not installed; add it to requirements')
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    self._pool = await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def conn(self, dsn: str | None = None, min_size: int = 1, max_size: int = 10):
        """Async context manager that yields a connection from the managed pool.

        If the pool is not initialized and `dsn` is provided it will be
        initialized lazily.
        """
        if self._pool is None:
            if dsn is None:
                raise RuntimeError('Postgres pool not initialized; call init_pg_pool(dsn) or pass dsn=')
            await self.init(dsn, min_size=min_size, max_size=max_size)
        async with self._pool.acquire() as conn:
            yield conn


# Canonical manager instance used by module-level helpers
_PG_MANAGER = PostgresPoolManager()


async def init_pg_pool(dsn: str, min_size: int = 1, max_size: int = 10) -> AsyncpgPool:
    """Compatibility wrapper: initialize and return the shared pool."""
    return await _PG_MANAGER.init(dsn, min_size=min_size, max_size=max_size)


async def close_pg_pool() -> None:
    """Compatibility wrapper: close the shared pool."""
    await _PG_MANAGER.close()


@asynccontextmanager
async def pg_pool_context(pg_dsn: str, min_size: int = 1, max_size: int = 10):
    """Context manager that initializes the shared pool and closes it on exit."""
    await init_pg_pool(pg_dsn, min_size=min_size, max_size=max_size)
    try:
        yield _PG_MANAGER._pool
    finally:
        await close_pg_pool()


async def get_conn(dsn: str | None = None):
    """FastAPI dependency that yields a single connection.

    Use in route handlers as: `conn = Depends(get_conn)`. Implemented as an
    async generator so FastAPI can manage entering/exiting the connection
    context automatically.
    """
    if _PG_MANAGER._pool is None:
        if dsn is None:
            raise RuntimeError('Postgres pool not initialized; call init_pg_pool(dsn) or provide dsn=')
        await init_pg_pool(dsn)
    async with _PG_MANAGER._pool.acquire() as conn:
        yield conn


async def postgres_store(m: 'NormalizedMessage', pool: AsyncpgPool | None = None, dsn: str | None = None) -> None:
    """Store a message record into PostgreSQL using `asyncpg`.

    This function preserves the original API but delegates to the
    manager when possible.
    """
    if asyncpg is None:
        raise RuntimeError('asyncpg is not installed; cannot use postgres_store')

    p = pool or _PG_MANAGER._pool
    if p is None:
        if dsn:
            p = await init_pg_pool(dsn)
        else:
            raise RuntimeError('Postgres pool not initialized; call init_pg_pool(dsn) or pass pool=')

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
