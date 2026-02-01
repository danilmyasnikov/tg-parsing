#!/usr/bin/env python3
"""Fetch a small number of messages for testing and print concise summaries.

Usage:
    .venv/Scripts/python fetch_messages.py <target> --limit 3
"""
from __future__ import annotations
import argparse
import asyncio

from tg_parsing.client import create_client
import os
from tg_parsing.config import get_api_credentials
import tg_parsing.entity_resolver as resolver
import tg_parsing.message_fetcher as fetcher
from tg_parsing.storage import postgres_store, pg_pool_context


async def main(target: str, session: str = 'session', limit: int = 3, pg_dsn: str | None = None) -> int:
    api_id, api_hash = get_api_credentials()
    async with create_client(session, api_id, api_hash) as client:
        entity = await resolver.resolve_entity(client, target)
        if entity is None:
            print('Could not resolve target:', target)
            return 2

        # prefer explicit PG DSN (CLI) then environment variable `PG_DSN`
        if not pg_dsn:
            pg_dsn = os.getenv('PG_DSN')
            
        # Prefer explicit PG DSN (CLI) then environment variable `PG_DSN`.
        if pg_dsn:
            async with pg_pool_context(pg_dsn) as pool:
                store_fn = lambda m: postgres_store(m, pool=pool)
                count = await fetcher.fetch_all_messages(client, entity, store_fn, limit=limit)
                print(f'Processed {count} messages')
        else:
            # fall back to module-level pool if previously initialized
            store_fn = postgres_store
            count = await fetcher.fetch_all_messages(client, entity, store_fn, limit=limit)
            print(f'Processed {count} messages')
        return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Fetch a few messages for testing')
    p.add_argument('target', help='channel username or numeric id')
    p.add_argument('--session', default='session', help='session filename prefix')
    p.add_argument('--limit', type=int, default=3, help='number of messages to fetch')
    p.add_argument('--pg-dsn', dest='pg_dsn', help='Postgres DSN to write messages (overrides PG_DSN env)')
    args = p.parse_args()
    raise SystemExit(asyncio.run(main(args.target, session=args.session, limit=args.limit, pg_dsn=args.pg_dsn)))
