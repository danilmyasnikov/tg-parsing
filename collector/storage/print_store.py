from __future__ import annotations
from typing import Any
from ..normalize import NormalizedMessage


async def print_store(m: Any) -> None:
    """Async console storage used by small runners/tests.

    Accepts either the original Telethon `Message` or a
    `NormalizedMessage` produced by `normalize_message()`.
    """
    print('--- Latest message ---')
    if isinstance(m, NormalizedMessage):
        mid = m.id
        date = m.date
        sender = m.sender
        text = m.text
        has_media = m.has_media
    else:
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
