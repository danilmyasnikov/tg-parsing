"""Fetch the latest message from a chosen dialog or provided target.

If no `target` is specified on the command line, this script lists your
recent dialogs and prompts you to choose one interactively.
"""

import os
import re
import json
import pathlib
import asyncio
import argparse
from typing import TypedDict, Any
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import User, Chat, Channel
from telethon.tl.custom.message import Message

class Config(TypedDict, total=False):
    targets: list[str]


Entity = User | Chat | Channel

# Optional .env support: will load if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

api_id: str | None = os.getenv("TG_API_ID")
api_hash: str | None = os.getenv("TG_API_HASH")

if api_id is None:
    raise RuntimeError("TG_API_ID environment variable is not set")

if api_hash is None:
    raise RuntimeError("TG_API_HASH environment variable is not set")

try:
    api_id_int: int = int(api_id)
except ValueError:
    raise RuntimeError("TG_API_ID must be an integer")




CONFIG_TARGETS: list[str] = []


# Optional config file with target dialog ids/usernames
def load_config() -> Config:
    cfg_path: pathlib.Path = pathlib.Path('config.json')
    if cfg_path.exists():
        try:
            cfg: Config = json.loads(cfg_path.read_text())
            if isinstance(cfg, dict):
                return cfg.get('targets', []) or []
        except Exception as e:
            print('Warning: failed to read config.json:', e)

CONFIG_TARGETS = load_config()

async def choose_dialog(client: TelegramClient, limit: int = 50) -> Entity | None:
    """List dialogs and prompt the user to choose one. Returns the entity."""
    dialogs = [d async for d in client.iter_dialogs(limit=limit)]
    if not dialogs:
        print('No dialogs found for this account.')
        return None

    for i, d in enumerate(dialogs, 1):
        e = d.entity
        name: str = getattr(e, 'title', None) or getattr(e, 'first_name', None) or getattr(e, 'username', None) or str(e)
        extra: list[str] = []
        if getattr(e, 'username', None):
            extra.append(f'@{e.username}')
        if getattr(e, 'id', None):
            extra.append(f'id={e.id}')
        print(f'{i:3d}) {name} {" ".join(extra)}')

    while True:
        choice: str = input(f'Select dialog [1-{len(dialogs)}] (or q to cancel): ').strip()
        if choice.lower() in ('q', 'quit', 'exit'):
            return None
        if not choice:
            continue
        try:
            idx: int = int(choice)
            if 1 <= idx <= len(dialogs):
                return dialogs[idx - 1].entity
        except ValueError:
            print('Please enter a number or q to cancel.')


async def main(target: str | None = None, session: str = 'session') -> None:
    if not api_id or not api_hash:
        print('Please set TG_API_ID and TG_API_HASH environment variables.')
        if not DOTENV_AVAILABLE:
            print('Tip: create a .env file and install python-dotenv to load it automatically.')
            print('Example .env content:')
            print('TG_API_ID=123456')
            print('TG_API_HASH=your_api_hash_here')
        else:
            print('If you already have a .env, ensure TG_API_ID and TG_API_HASH are defined in it.')
        return

    client: TelegramClient = TelegramClient(session, api_id_int, api_hash)
    await client.start()
    try:
        # If no target provided, prefer config.json targets, else interactive choose
        if not target:
            if CONFIG_TARGETS:
                target = CONFIG_TARGETS[0]
                print(f'Using target from config.json: {target}')
            else:
                print('No target provided — listing your recent dialogs...')
                entity: Entity | None = await choose_dialog(client)
                if not entity:
                    print('Cancelled.')
                    return

        # Resolve entity: numeric id -> search dialogs, otherwise handle invite or get_entity
        entity: Entity | None = None
        if target is not None:
            # numeric id in config may be int or string; try to interpret
            target_id: int | None = None
            try:
                target_id = int(str(target))
            except Exception:
                target_id = None

            if target_id is not None:
                entity = await client.get_entity(target_id)


            # If still not found and looks like invite link, attempt to join
            if entity is None and (('joinchat' in str(target)) or ('/+' in str(target)) or str(target).startswith('+')):
                invite_hash: str = str(target).rstrip('/').split('/')[-1]
                try:
                    await client(ImportChatInviteRequest(invite_hash))
                    print('Joined via invite:', invite_hash)
                except errors.UserAlreadyParticipantError:
                    print('Already a participant')
                except Exception as e:
                    print('Could not join via invite:', e)

            if entity is None:
                try:
                    entity = await client.get_entity(target)
                except Exception as e:
                    print('Failed to get entity for target:', target, 'Error:', e)
                    return

        # Fetch and show latest message
        msgs: list[Message] = await client.get_messages(entity, limit=1)
        if not msgs:
            print('No messages found in', getattr(entity, 'title', str(entity)))
        else:
            m: Message = msgs[0]
            print('--- Latest message ---')
            print('id:', m.id)
            print('date:', m.date)
            print('sender_id:', m.sender_id)
            print('text:', m.text)
            if m.media:
                print('Has media: yes (not downloaded)')
    finally:
        await client.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch latest Telegram message from a channel')
    parser.add_argument('target', nargs='?', help='channel username, t.me link, or invite link')
    parser.add_argument('--session', default='session', help='session filename prefix')
    args = parser.parse_args()
    asyncio.run(main(args.target, session=args.session))
