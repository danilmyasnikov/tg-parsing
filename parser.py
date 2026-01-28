from __future__ import annotations
from typing import Callable, Awaitable, Optional, List
import asyncio
from telethon.errors import FloodWaitError
from telethon.tl.custom.message import Message
from annotations import Entity


async def fetch_latest_message(client, entity) -> Message | None:
    msgs = await client.get_messages(entity, limit=1)
    if not msgs:
        return None
    return msgs[0]


async def fetch_all_messages(
    client,
    entity,
    store_func: Optional[Callable[[Message], Awaitable[None]]] = None,
    *,
    resume_after_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> int:
    """Stream all messages from `entity` (newest->oldest).

    - If `store_func` is provided it will be awaited for each message.
    - If `store_func` is None, messages are collected in-memory and discarded
      after the call returns (caller should prefer providing `store_func`).
    - `resume_after_id` stops fetching when a message id <= that value is seen.
    - `limit` caps the total number of messages fetched.

    Returns the number of messages processed.
    """
    count = 0
    collected: List[Message] = [] if store_func is None else []

    try:
        async for m in client.iter_messages(entity):
            # stop if we've reached saved checkpoint
            mid = getattr(m, "id", None)
            if resume_after_id is not None and mid is not None and mid <= resume_after_id:
                break

            if store_func is not None:
                try:
                    await store_func(m)
                except Exception as e:
                    # if storing fails, log and continue
                    print('Warning: store_func raised:', e)
            else:
                collected.append(m)

            count += 1
            if limit is not None and count >= limit:
                break

    except FloodWaitError as e:
        # Respect Telegram's request to pause
        wait = int(getattr(e, 'seconds', 0)) or 60
        print(f'FloodWaitError: sleeping for {wait}s before resuming')
        await asyncio.sleep(wait + 1)
        # resume recursively (preserves resume_after_id and limit)
        more = await fetch_all_messages(
            client, entity, store_func, resume_after_id=resume_after_id, limit=(None if limit is None else max(0, limit - count))
        )
        return count + more
    except Exception as e:
        print('Error while iterating messages:', e)
        return count

    return count
