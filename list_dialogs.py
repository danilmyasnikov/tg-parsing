"""List recent dialogs (channels/groups/users) for your account.

Usage:
  & .\.venv\Scripts\Activate.ps1
  python list_dialogs.py

This prints each dialog with index, title, username (if any), and id.
"""

import os
import asyncio
from telethon import TelegramClient

# optional .env loading
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_id = os.getenv('TG_API_ID')
api_hash = os.getenv('TG_API_HASH')
session_name = os.getenv('SESSION_NAME')

async def main(session: str = session_name, limit: int = 100):

    if not api_id or not api_hash:
        print('Please set TG_API_ID and TG_API_HASH (env or .env)')
        return

    client = TelegramClient(session, int(api_id), api_hash)
    await client.start()
    try:
        i = 0
        async for dialog in client.iter_dialogs(limit=limit):
            i += 1
            e = dialog.entity
            title = getattr(e, 'title', None) or getattr(e, 'first_name', None) or getattr(e, 'username', None) or str(e)
            username = getattr(e, 'username', None)
            eid = getattr(e, 'id', None)
            print(f"{i:3d}) {title} | username={username} | id={eid}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', default=session_name)
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    asyncio.run(main(session=args.session, limit=args.limit))
