from __future__ import annotations
from typing import Callable, Awaitable
from telethon import TelegramClient

from .type_annotations import Entity
import asyncio
from telethon.errors import FloodWaitError
from telethon.tl.custom.message import Message

from .stream import stream_messages
from .storage import print_store


async def consume_messages(
    client: TelegramClient,
    entity: Entity,
    store_func: Callable[[Message], Awaitable[None]] = print_store,
    *,
    resume_after_id: int | None = None,
    limit: int | None = None,
) -> int:
    """Compatibility wrapper: consume `stream_messages` and
    call `store_func` for each message or collect in-memory when
    `store_func` is None. Returns the number of messages processed.
    """
    count = 0
    try:
        async for m in stream_messages(client, entity, resume_after_id=resume_after_id, limit=limit):
            if store_func is not None:
                try:
                    await store_func(m)
                except Exception as e:
                    print('Warning: store_func raised:', e)
            else:
                # keep previous behavior of collecting messages in-memory
                # by doing nothing here; callers that relied on returned
                # collection should use the async generator instead.
                pass

            count += 1

    except FloodWaitError as e:
        # This should be handled by the generator, but keep a fallback
        wait = int(getattr(e, 'seconds', 0)) or 60
        print(f'FloodWaitError: sleeping for {wait}s before resuming')
        await asyncio.sleep(wait + 1)
        more = await consume_messages(
            client, entity, store_func, resume_after_id=resume_after_id, limit=(None if limit is None else max(0, limit - count))
        )
        return count + more
    except Exception as e:
        print('Error while processing messages in fetcher:', e)
        return count

    return count
