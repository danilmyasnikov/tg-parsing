"""Inspect what the analyzer sent to the model and ask the model to explain it.

Usage: python -m analyzer.inspect_data
"""

from __future__ import annotations

import asyncio
from typing import Optional

from .context_loader import load_recent_messages
from .llm_client import analyze_text


async def main() -> None:
    pg_dsn: Optional[str] = "postgresql://pguser:pgpass@localhost:5432/tgdata"

    context = await load_recent_messages(pg_dsn=pg_dsn, days_back=1, limit=10)

    print("===FORMATTED_CONTEXT_START===")
    if context.strip():
        print(context)
    else:
        print("[EMPTY]")
    print("===FORMATTED_CONTEXT_END===\n")

    prompt = (
        "You received a DATA section. First, show the exact DATA you received (up to 1000 chars). "
        "Then, explain briefly why the DATA might be empty or missing. Be concise."
    )

    response = await analyze_text(prompt, context)

    print("===MODEL_RESPONSE===")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
