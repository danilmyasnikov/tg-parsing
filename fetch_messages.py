#!/usr/bin/env python3
"""Fetch a small number of messages for testing and print concise summaries.

Usage:
    .venv/Scripts/python fetch_messages.py <target> --limit 3
"""
from __future__ import annotations
import argparse
import asyncio

from client import create_client
import os
from config import get_api_credentials
import resolver
import fetcher
from storage_pg import init_pg_pool, postgres_store, close_pg_pool


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
            
        pool = None
        if pg_dsn:
            # initialize pool once at startup and capture it in the store function
            pool = await init_pg_pool(pg_dsn)
            store_fn = lambda m: postgres_store(m, pool=pool)
        else:
            # fall back to module-level pool if previously initialized
            store_fn = postgres_store

        count = await fetcher.fetch_all_messages(client, entity, store_fn, limit=limit)
        print(f'Processed {count} messages')

        # if we created a pool here, close it
        if pool is not None:
            await close_pg_pool()
        return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Fetch a few messages for testing')
    p.add_argument('target', help='channel username or numeric id')
    p.add_argument('--session', default='session', help='session filename prefix')
    p.add_argument('--limit', type=int, default=3, help='number of messages to fetch')
    p.add_argument('--pg-dsn', dest='pg_dsn', help='Postgres DSN to write messages (overrides PG_DSN env)')
    args = p.parse_args()
    raise SystemExit(asyncio.run(main(args.target, session=args.session, limit=args.limit, pg_dsn=args.pg_dsn)))
