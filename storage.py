"""Compatibility wrapper re-exporting the split storage modules.

This module keeps the original `storage` import path working for
callers while the heavy Postgres code and the test-only print sink
live in separate modules (`storage_pg` and `storage_print`).
"""
from storage_print import print_store
from storage_pg import init_pg_pool, postgres_store, close_pg_pool

__all__ = [
    'print_store',
    'init_pg_pool',
    'postgres_store',
    'close_pg_pool',
]

