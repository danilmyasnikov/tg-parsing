"""tg_parsing - Telegram message parsing and storage library.

This module re-exports the package's public API so callers can do:

	from tg_parsing import create_client, fetch_all_messages, postgres_store

Keep exported symbols small and stable; prefer importing modules for
less commonly used internals.
"""

from __future__ import annotations

# Client / config
from .client import create_client
from .config import get_api_credentials, load_config

# Entity resolution & parsing
from .entity_resolver import resolve_entity
from .stream import stream_messages

# Fetcher
from .consumer import fetch_all_messages

# Storage
from .storage import (
	print_store,
	init_pg_pool,
	postgres_store,
	close_pg_pool,
	pg_pool_context,
)

__all__ = [
	# client/config
	'create_client',
	'get_api_credentials',
	'load_config',

	# entity / parser
	'resolve_entity',
	'stream_messages',

	# fetcher
	'fetch_all_messages',

	# storage
	'print_store',
	'init_pg_pool',
	'postgres_store',
	'close_pg_pool',
	'pg_pool_context',
]

