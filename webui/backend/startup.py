from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from .database import DEFAULT_PG_DSN, close_pool
from collector.storage.postgres_store import init_pg_pool

logger = logging.getLogger("webui")


@asynccontextmanager
async def lifespan(app):
    """Application lifespan handler: initialize and close shared DB pool."""
    try:
        try:
            await init_pg_pool(DEFAULT_PG_DSN)
        except Exception:
            logger.exception("Postgres pool init failed during startup")
            # don't fail startup; handlers will surface DB errors
        logger.info("Web UI available at: http://localhost:8000 (bind: 0.0.0.0:8000)")
        print("Web UI available at: http://localhost:8000 (bind: 0.0.0.0:8000)")
    except Exception:
        pass
    try:
        yield
    finally:
        await close_pool()
