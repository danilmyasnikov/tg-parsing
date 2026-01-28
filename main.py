from __future__ import annotations
import asyncio

from config import get_api_credentials, load_config, DOTENV_AVAILABLE
from client import create_client
import parser
import resolver
import storage
from annotations import Entity


async def main(target: str | None = None, session: str = 'session') -> None:
    try:
        api_id, api_hash = get_api_credentials()
    except RuntimeError as e:
        print(e)
        if not DOTENV_AVAILABLE:
            print('Tip: create a .env file and install python-dotenv to load it automatically.')
            print('Example .env content:')
            print('TG_API_ID=123456')
            print('TG_API_HASH=your_api_hash_here')
        else:
            print('If you already have a .env, ensure TG_API_ID and TG_API_HASH are defined in it.')
        return

    config_targets: list[str] = load_config()

    async with create_client(session, api_id, api_hash) as client:
        # If no target provided, prefer config.json targets, otherwise exit
        if not target:
            if config_targets:
                target = config_targets[0]
                print(f'Using target from config.json: {target}')
            else:
                print('No target provided and no `targets` in config.json. Provide a target via CLI or config.')
                return

        # Resolve entity: numeric id -> search dialogs, otherwise handle invite or get_entity
        entity: Entity | None = None
        if target is not None:
            entity = await resolver.resolve_entity(client, target)
            if entity is None:
                return

        # Fetch and show latest message
        m = await parser.fetch_latest_message(client, entity)
        if not m:
            print('No messages found in', getattr(entity, 'title', str(entity)))
        else:
            storage.show_message(m)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fetch latest Telegram message from a channel')
    parser.add_argument('target', nargs='?', help='channel username or numeric id')
    parser.add_argument('--session', default='session', help='session filename prefix')
    args = parser.parse_args()
    asyncio.run(main(args.target, session=args.session))
