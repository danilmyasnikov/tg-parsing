from __future__ import annotations
from typing import Callable, Awaitable, List, cast, AsyncIterator
import asyncio
from telethon.errors import FloodWaitError
from telethon import TelegramClient
from telethon.tl.custom.message import Message
from .type_annotations import Entity


async def fetch_latest_message(client: TelegramClient, entity) -> Message | None:
    msgs = await client.get_messages(entity, limit=1)
    if not msgs:
        return None
    # Telethon may return a single Message or a sequence; handle both.
    if isinstance(msgs, (list, tuple)):
        return cast(Message, msgs[0])
    return cast(Message, msgs)



async def iter_messages_from_entity(
    client: TelegramClient,
    entity,
    *,
    resume_after_id: int | None = None,
    limit: int | None = None,
) -> AsyncIterator[Message]:
    """Async generator yielding `Message` objects newest->oldest.

    This generator handles `FloodWaitError` by sleeping and resuming.
    It does not perform any storage; callers should handle persistence.
    """
    count = 0
    try:
        async for m in client.iter_messages(entity):
            m = cast(Message, m)

            mid = getattr(m, "id", None)
            if resume_after_id is not None and mid is not None and mid <= resume_after_id:
                break

            yield m

            count += 1
            if limit is not None and count >= limit:
                break

    except FloodWaitError as e:
        wait = int(getattr(e, 'seconds', 0)) or 60
        print(f'FloodWaitError: sleeping for {wait}s before resuming')
        await asyncio.sleep(wait + 1)
        # resume and yield remaining messages
        async for m in iter_messages_from_entity(
            client, entity, resume_after_id=resume_after_id, limit=(None if limit is None else max(0, limit - count))
        ):
            yield m
