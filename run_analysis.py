"""
Main entry-point: analyse Telegram messages and generate an original post.

Usage:
    python run_analysis.py                  # full pipeline, 500 messages
    python run_analysis.py --max-messages 100 --mock   # test with mock LLM
    python run_analysis.py --phase topics   # only run topics analysis
    python run_analysis.py --phase post     # only generate post (needs prior runs)
"""
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyzer.batch_runner import RunConfig, run_map_reduce
from analyzer.generate_post import generate_post
from analyzer.llm_client import LLMConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("run_analysis")

PG_DSN = os.environ.get("PG_DSN", "postgresql://pguser:pgpass@localhost:5432/tgdata")


def make_config(job: str, run_id: str, args) -> RunConfig:
    return RunConfig(
        pg_dsn=PG_DSN,
        job=job,
        max_messages=args.max_messages,
        max_message_chars=400,
        max_batch_chars=10000,
        max_batch_tokens=3000,
        request_interval_s=0.5 if not args.mock else 0.0,
        timeout_s=60.0,
        run_id=run_id,
        prompt_override=args.prompt if hasattr(args, "prompt") else None,
    )


async def main():
    parser = argparse.ArgumentParser(description="Telegram message analyzer")
    parser.add_argument("--max-messages", type=int, default=500)
    parser.add_argument("--mock", action="store_true", help="Use mock LLM (no API calls)")
    parser.add_argument("--phase", default="all",
                        choices=["all", "topics", "style", "post", "custom"],
                        help="Which phase to run")
    parser.add_argument("--prompt", type=str, default=None,
                        help="Custom prompt for 'custom' job")
    parser.add_argument("--run-prefix", type=str, default="prod",
                        help="Prefix for run IDs")
    args = parser.parse_args()

    if args.mock:
        os.environ["ANALYZER_MOCK"] = "1"

    prefix = args.run_prefix

    if args.phase in ("all", "topics"):
        log.info("═══ TOPICS ANALYSIS ═══")
        cfg = make_config("topics", f"{prefix}-topics", args)
        result = await run_map_reduce(cfg, phase="all")
        log.info("Topics done: %s", result)

    if args.phase in ("all", "style"):
        log.info("═══ STYLE ANALYSIS ═══")
        cfg = make_config("style", f"{prefix}-style", args)
        result = await run_map_reduce(cfg, phase="all")
        log.info("Style done: %s", result)

    if args.phase == "custom":
        if not args.prompt:
            log.error("--prompt is required for custom job")
            return 1
        log.info("═══ CUSTOM ANALYSIS ═══")
        cfg = make_config("custom", f"{prefix}-custom", args)
        cfg.prompt_override = args.prompt
        result = await run_map_reduce(cfg, phase="all")
        log.info("Custom done: %s", result)

    if args.phase in ("all", "post"):
        log.info("═══ POST GENERATION ═══")
        llm_cfg = LLMConfig(
            mock=args.mock or os.environ.get("ANALYZER_MOCK") == "1",
            request_interval_s=0.0 if args.mock else 0.5,
        )
        post = await generate_post(
            topics_run_id=f"{prefix}-topics",
            style_run_id=f"{prefix}-style",
            output_run_id=f"{prefix}-post",
            llm_cfg=llm_cfg,
        )
        log.info("═══ GENERATED POST ═══")
        print("\n" + "=" * 60)
        print(post)
        print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
