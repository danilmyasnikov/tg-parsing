#!/usr/bin/env python3
"""Fetch a small number of messages for testing and print concise summaries.

Usage:
    .venv/Scripts/python fetch_messages.py <target> --limit 3
"""
from __future__ import annotations
import argparse
import asyncio

from client import create_client
from config import get_api_credentials
import resolver
import parser


async def _print_store(m):
    mid = getattr(m, 'id', None)
    date = getattr(m, 'date', None)
    sender = getattr(m, 'sender_id', None)
    text = (getattr(m, 'text', '') or '').replace('\n', ' ')[:200]
    has_media = bool(getattr(m, 'media', None))
    print(f'id={mid} date={date} sender={sender} media={has_media} text="{text}"')


async def main(target: str, session: str = 'session', limit: int = 3) -> int:
    api_id, api_hash = get_api_credentials()
    async with create_client(session, api_id, api_hash) as client:
        entity = await resolver.resolve_entity(client, target)
        if entity is None:
            print('Could not resolve target:', target)
            return 2

        count = await parser.fetch_all_messages(client, entity, _print_store, limit=limit)
        print(f'Processed {count} messages')
        return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Fetch a few messages for testing')
    p.add_argument('target', help='channel username or numeric id')
    p.add_argument('--session', default='session', help='session filename prefix')
    p.add_argument('--limit', type=int, default=3, help='number of messages to fetch')
    args = p.parse_args()
    raise SystemExit(asyncio.run(main(args.target, session=args.session, limit=args.limit)))
