from __future__ import annotations
from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import AsyncIterator, Any, cast
from telethon import TelegramClient


@asynccontextmanager
async def create_client(session: str, api_id: int, api_hash: str) -> AsyncIterator[TelegramClient]:
    """Async context manager that starts and disconnects a TelegramClient."""
    # Ensure .sessions directory exists and use it for session files when
    # a bare session name (no path) is provided. If the caller passes a
    # path (contains a directory component) we respect it as-is.
    sessions_dir = Path('.sessions')
    try:
        sessions_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    sess_path = Path(session)
    if str(sess_path.parent) in ('.', ''):
        session_arg = str(sessions_dir / session)
    else:
        session_arg = session

    client = cast(Any, TelegramClient(session_arg, api_id, api_hash))
    phone: str | None = os.getenv('TG_PHONE')
    if phone is not None:
        await client.start(phone=phone)
    else:
        await client.start()
    try:
        yield client
    finally:
        await client.disconnect()
