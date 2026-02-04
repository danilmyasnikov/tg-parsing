from __future__ import annotations
from contextlib import asynccontextmanager
import asyncio
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

    max_attempts = 5
    base_delay = 5  # seconds

    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            if phone is not None:
                await client.start(phone=phone)
            else:
                await client.start()
            last_exc = None
            break
        except (ConnectionError, TimeoutError, OSError) as e:
            last_exc = e
            if attempt < max_attempts:
                wait = base_delay * attempt
                print(f"Connection attempt {attempt} failed: {e!r}. Retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                # re-raise the last exception after exhausting retries
                raise

    try:
        yield client
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
