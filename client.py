from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator
from telethon import TelegramClient


@asynccontextmanager
async def create_client(session: str, api_id: int, api_hash: str) -> AsyncIterator[TelegramClient]:
    """Async context manager that starts and disconnects a TelegramClient."""
    client = TelegramClient(session, api_id, api_hash)
    await client.start()
    try:
        yield client
    finally:
        await client.disconnect()
