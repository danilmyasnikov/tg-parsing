from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telethon.tl.types import User, Chat, Channel
    Entity = User | Chat | Channel
else:
    # Runtime fallback — the real alias is only needed for type checkers
    Entity = object
