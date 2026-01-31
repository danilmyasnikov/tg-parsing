"""Storage package aggregator.

Expose the lightweight `print_store` and the Postgres-backed
`init_pg_pool`, `postgres_store`, and `close_pg_pool` from a
single import location (`storage`).
"""
from .storage_print import print_store
from .storage_pg import init_pg_pool, postgres_store, close_pg_pool

__all__ = [
    'print_store',
    'init_pg_pool',
    'postgres_store',
    'close_pg_pool',
]
