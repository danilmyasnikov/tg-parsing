"""Normalize and validate Telethon `Message` objects before persistence.

The helper aims to be conservative: it validates required fields (id, sender)
and coerces optional ones to safe Python types. On validation failure it
raises ValueError with a clear message naming the field and the reason.
"""
from __future__ import annotations
from typing import Any
import datetime
from dataclasses import dataclass


@dataclass
class NormalizedMessage:
    id: int
    sender: str
    date: datetime.datetime | None
    text: str
    has_media: bool


def normalize_message(m: Any) -> NormalizedMessage:
    """Return a NormalizedMessage built from `m`.

    Coerces and validates fields deterministically. Raises ValueError
    with a clear message if a required field is missing or cannot be
    coerced.
    """
    mid = getattr(m, 'id', None)
    if mid is None:
        raise ValueError("normalize_message: missing required field 'id'")
    try:
        mid_val = int(mid)
    except Exception as e:
        raise ValueError(f"normalize_message: invalid 'id' value {mid!r}: {e}")

    sender = getattr(m, 'sender_id', None)
    if sender is None:
        raise ValueError(f"normalize_message: missing required field 'sender_id' for message id {mid_val!r}")
    try:
        sender_str = str(sender)
    except Exception as e:
        raise ValueError(f"normalize_message: cannot stringify 'sender_id' ({sender!r}) for message id {mid_val!r}: {e}")

    date = getattr(m, 'date', None)
    if date is None:
        date_val = None
    else:
        if isinstance(date, datetime.datetime):
            date_val = date
        else:
            try:
                date_val = datetime.datetime.fromisoformat(str(date))
            except Exception:
                # fallback to string-preserved value (DB will accept str)
                date_val = None

    text = getattr(m, 'text', '') or ''
    try:
        text = str(text)
    except Exception as e:
        raise ValueError(f"normalize_message: cannot coerce 'text' to str for message id {mid_val!r}: {e}")
    text = text.replace('\n', ' ')

    has_media = bool(getattr(m, 'media', None))

    return NormalizedMessage(id=mid_val, sender=sender_str, date=date_val, text=text, has_media=has_media)
