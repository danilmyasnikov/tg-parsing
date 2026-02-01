"""Storage package aggregator.

Expose the lightweight `print_store` and the Postgres-backed
`init_pg_pool`, `postgres_store`, and `close_pg_pool` from a
single import location (`storage`).
"""
from .print_store import print_store
from .postgres_store import init_pg_pool, postgres_store, close_pg_pool, pg_pool_context

__all__ = [
    'print_store',
    'init_pg_pool',
    'postgres_store',
    'close_pg_pool',
    'pg_pool_context',
]
