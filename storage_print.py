from __future__ import annotations
from telethon.tl.custom.message import Message


async def print_store(m: Message) -> None:
    """Async console storage used by small runners/tests.

    Consolidates message printing here and uses `getattr` to avoid
    attribute errors when fields are missing.
    """
    print('--- Latest message ---')
    mid = getattr(m, 'id', None)
    date = getattr(m, 'date', None)
    sender = getattr(m, 'sender_id', None)
    text = (getattr(m, 'text', '') or '').replace('\n', ' ')
    has_media = bool(getattr(m, 'media', None))

    print('id:', mid)
    print('date:', date)
    print('sender_id:', sender)
    print('text:', text)
    if has_media:
        print('Has media: yes (not downloaded)')
