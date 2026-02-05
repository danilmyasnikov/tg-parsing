"""CLI entry point for analyzer tasks."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .context_loader import load_recent_messages
from .llm_client import analyze_text
from .prompts import TOPIC_EXTRACTION_PROMPT, STYLE_ANALYSIS_PROMPT


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze Telegram messages using Gemini.")
    parser.add_argument("--pg-dsn", default=os.getenv("PG_DSN"), help="Postgres DSN")
    parser.add_argument("--sender-id", help="Channel/chat sender_id to filter")
    parser.add_argument("--days-back", type=int, default=30)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument(
        "--job",
        choices=["topics", "style"],
        default="topics",
        help="Which analysis to run",
    )
    return parser


async def _run(args: argparse.Namespace) -> None:
    pg_dsn: Optional[str] = args.pg_dsn or os.getenv("PG_DSN")
    if not pg_dsn:
        raise SystemExit("PG_DSN is required (pass --pg-dsn or set PG_DSN in .env)")

    context = await load_recent_messages(
        pg_dsn=pg_dsn,
        sender_id=args.sender_id,
        days_back=args.days_back,
        limit=args.limit,
    )

    prompt = TOPIC_EXTRACTION_PROMPT if args.job == "topics" else STYLE_ANALYSIS_PROMPT
    result = await analyze_text(prompt, context)
    if result:
        print(result)
    else:
        print("[analyzer] No response from model or empty context.")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")
    parser = _build_parser()
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
