"""Run sentiment analysis over recent messages and print model JSON output."""

from __future__ import annotations

import asyncio
from typing import Optional, Any

from .context_loader import load_recent_messages
from .llm_client import analyze_text


async def main() -> None:
    pg_dsn: Optional[str] = "postgresql://pguser:pgpass@localhost:5432/tgdata"
    context = await load_recent_messages(pg_dsn=pg_dsn, days_back=7, limit=200)

    prompt = (
        """
You are an assistant. OUTPUT ONLY valid JSON (no commentary).
Return an object with keys: "overall" and "messages".
"overall" must be an object: { "label": "positive"|"neutral"|"negative", "score": 0.0-1.0 }.
"messages" must be an array of objects each with: { "id": int, "sender_id": str, "snippet": str, "sentiment": "positive"|"neutral"|"negative", "score": 0.0-1.0 }.
Analyze the DATA below and provide sentiment per message (use snippets up to 200 chars).
If there is no data, return {"overall": {"label": "neutral", "score": 0.0}, "messages": []}.
DATA:
"""
    )

    response: Any = await analyze_text(prompt, context, model_name="gemini-3-flash-preview")
    print("===SENTIMENT MODEL RESPONSE===")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
