"""Thin wrapper that delegates to the refactored `main` orchestrator."""

from __future__ import annotations
import argparse
import asyncio

from main import main


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch latest Telegram message from a channel')
    parser.add_argument('target', nargs='?', help='channel username or numeric id')
    parser.add_argument('--session', default='session', help='session filename prefix')
    args = parser.parse_args()
    asyncio.run(main(args.target, session=args.session))
