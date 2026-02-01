from __future__ import annotations
from contextlib import asynccontextmanager
import os
from typing import AsyncIterator, Any, cast
from telethon import TelegramClient


@asynccontextmanager
async def create_client(session: str, api_id: int, api_hash: str) -> AsyncIterator[TelegramClient]:
    """Async context manager that starts and disconnects a TelegramClient."""
    client = cast(Any, TelegramClient(session, api_id, api_hash))
    phone: str | None = os.getenv('TG_PHONE')
    if phone is not None:
        await client.start(phone=phone)
    else:
        await client.start()
    try:
        yield client
    finally:
        await client.disconnect()
