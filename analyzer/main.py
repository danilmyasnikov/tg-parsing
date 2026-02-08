"""CLI entry point for analyzer tasks."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .batch_runner import RunConfig, run_map_reduce
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
        choices=["topics", "style", "custom"],
        default="topics",
        help="Which analysis to run",
    )
    parser.add_argument(
        "--strategy",
        choices=["single", "map_reduce"],
        default="map_reduce",
        help="Use a single request or map-reduce batching",
    )
    parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model name")
    parser.add_argument("--system-instruction", help="Optional system instruction")
    parser.add_argument("--page-size", type=int, default=2000)
    parser.add_argument("--max-message-chars", type=int, default=400)
    parser.add_argument("--batch-max-chars", type=int, default=60000)
    parser.add_argument("--batch-max-tokens", type=int, default=15000)
    parser.add_argument("--max-messages", type=int, default=None)
    parser.add_argument("--run-id", help="Run identifier for resumable runs")
    parser.add_argument("--resume", action="store_true", help="Resume a previous run")
    parser.add_argument("--phase", choices=["map", "reduce", "all"], default="all")
    parser.add_argument("--request-interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-requests", type=int, default=None)
    parser.add_argument("--prompt", help="Custom prompt for job=custom")
    parser.add_argument("--prompt-file", help="Path to a text file with the custom prompt")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM responses (offline)")
    return parser


async def _run(args: argparse.Namespace) -> None:
    pg_dsn: Optional[str] = args.pg_dsn or os.getenv("PG_DSN")
    if not pg_dsn:
        raise SystemExit("PG_DSN is required (pass --pg-dsn or set PG_DSN in .env)")

    prompt_override: Optional[str] = args.prompt
    if args.prompt_file:
        prompt_override = Path(args.prompt_file).read_text(encoding="utf-8")

    if args.mock:
        os.environ["ANALYZER_MOCK"] = "1"

    if args.strategy == "single":
        context = await load_recent_messages(
            pg_dsn=pg_dsn,
            sender_id=args.sender_id,
            days_back=args.days_back,
            limit=args.limit,
        )

        if args.job == "custom":
            if not prompt_override:
                raise SystemExit("--prompt or --prompt-file is required for job=custom")
            prompt = prompt_override
        else:
            prompt = TOPIC_EXTRACTION_PROMPT if args.job == "topics" else STYLE_ANALYSIS_PROMPT

        result = await analyze_text(
            prompt,
            context,
            model_name=args.model,
            system_instruction=args.system_instruction,
        )
        if result:
            print(result)
        else:
            print("[analyzer] No response from model or empty context.")
        return

    max_messages = args.max_messages

    config = RunConfig(
        pg_dsn=pg_dsn,
        job=args.job,
        sender_id=args.sender_id,
        days_back=args.days_back,
        page_size=args.page_size,
        max_messages=max_messages,
        max_message_chars=args.max_message_chars,
        max_batch_chars=args.batch_max_chars,
        max_batch_tokens=args.batch_max_tokens,
        model_name=args.model,
        system_instruction=args.system_instruction,
        request_interval_s=args.request_interval,
        timeout_s=args.timeout,
        max_requests=args.max_requests,
        run_id=args.run_id or "",
        prompt_override=prompt_override,
    )

    result = await run_map_reduce(config, resume=args.resume, phase=args.phase)
    if result:
        print(result)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")
    parser = _build_parser()
    args = parser.parse_args()

    import logging
    # Suppress noisy asyncpg pool-cleanup warnings on abnormal exit
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)

    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
