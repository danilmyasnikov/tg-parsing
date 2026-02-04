#!/usr/bin/env python3
"""Export your dialogs/entities into a JSON file compatible with config.json.

Produces a JSON object with a single key `targets` whose value is a list of
usernames (when available) or numeric ids for each dialog the account can see.

Usage:
  python scripts/export_targets.py [-o OUTPUT.json] [--session NAME] [--limit N]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so imports work when running from `scripts/`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.type_annotations import Entity

import collector


async def gather_targets(output: str, session: str = 'session', limit: int | None = None) -> int:
    try:
        api_id, api_hash = collector.get_api_credentials()
    except RuntimeError as err:
        print(err)
        if not collector.DOTENV_AVAILABLE:
            print('Tip: create a .env file and install python-dotenv to load it automatically.')
            print('Example .env content:')
            print('TG_API_ID=123456')
            print('TG_API_HASH=your_api_hash_here')
        else:
            print('If you already have a .env, ensure TG_API_ID and TG_API_HASH are defined in it.')
        return 2

    targets: list[str | int] = []

    async with collector.create_client(session, api_id, api_hash) as client:
        if limit is None:
            dialogs = [d async for d in client.iter_dialogs()]
        else:
            dialogs = [d async for d in client.iter_dialogs(limit=float(limit))]
        for d in dialogs:
            e: Entity = d.entity
            username = getattr(e, 'username', None)
            if username:
                targets.append(username)
            else:
                eid = getattr(e, 'id', None)
                if eid is not None:
                    targets.append(eid)

    payload = {'targets': targets}
    p = Path(output)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f'Wrote {len(targets)} targets to {p}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Export dialogs/entities to a config-style JSON file')
    parser.add_argument('-o', '--output', default='exported_config.json', help='output filename')
    parser.add_argument('--session', default='session', help='session filename prefix')
    parser.add_argument('--limit', type=int, default=0, help='limit dialogs to N (0 means no limit)')
    args = parser.parse_args()

    limit = args.limit if args.limit > 0 else None
    return asyncio.run(gather_targets(args.output, session=args.session, limit=limit))


if __name__ == '__main__':
    raise SystemExit(main())
