from __future__ import annotations
from telethon.tl.custom.message import Message


def show_message(m: Message) -> None:
    print('--- Latest message ---')
    print('id:', m.id)
    print('date:', m.date)
    print('sender_id:', m.sender_id)
    print('text:', m.text)
    if m.media:
        print('Has media: yes (not downloaded)')
