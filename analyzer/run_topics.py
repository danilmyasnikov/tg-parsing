"""Run a strict topic-extraction prompt and print the model response.

This runner asks the model to output ONLY a JSON array of the top 5
recurring topics. It includes an explicit instruction to avoid echoing
the prompt or other prose.
"""

from __future__ import annotations

import asyncio
from typing import Optional, Any

from .context_loader import load_recent_messages
from .llm_client import analyze_text


async def main() -> None:
    pg_dsn: Optional[str] = "postgresql://pguser:pgpass@localhost:5432/tgdata"
    context = await load_recent_messages(pg_dsn=pg_dsn, days_back=7, limit=200)

    strict_prompt = (
        "You are an assistant. DO NOT repeat the prompt or add commentary. "
        "Output ONLY a JSON array of the top 5 recurring topics found in the DATA section. "
        "If fewer than 5 topics exist, output only the ones you find. "
        "If there is no data, output an empty JSON array: []."
    )

    response: Any = await analyze_text(strict_prompt, context, model_name="gemini-3-flash-preview")
    print("===RAW MODEL RESPONSE===")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
