#!/usr/bin/env python3
"""Fetch a small number of messages for testing and print concise summaries.

Usage:
    .venv/Scripts/python collect.py <target> --limit 3
"""
from __future__ import annotations
import argparse
import asyncio

import os
import tg_parsing as tg


async def main(target: str, session: str = 'session', limit: int = 3, pg_dsn: str | None = None) -> int:
    api_id, api_hash = tg.get_api_credentials()
    async with tg.create_client(session, api_id, api_hash) as client:
        entity = await tg.resolve_entity(client, target)
        if entity is None:
            print('Could not resolve target:', target)
            return 2

        # prefer explicit PG DSN (CLI) then environment variable `PG_DSN`
        if not pg_dsn:
            pg_dsn = os.getenv('PG_DSN')
            
        # Prefer explicit PG DSN (CLI) then environment variable `PG_DSN`.
        if pg_dsn:
            async with tg.pg_pool_context(pg_dsn) as pool:
                store_fn = lambda m: tg.postgres_store(m, pool=pool)
                count = await tg.consume_messages(client, entity, store_fn, limit=limit)
                print(f'Processed {count} messages')
        else:
            # fall back to module-level pool if previously initialized
            store_fn = tg.postgres_store
            count = await tg.consume_messages(client, entity, store_fn, limit=limit)
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
