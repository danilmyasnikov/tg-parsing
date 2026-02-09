"""
Map-reduce batch runner for Telegram message analysis.

Pipeline:
  1. MAP   – split messages into batches, send each to LLM
  2. REDUCE – iteratively merge partial results until one remains
  3. Output final.txt
"""
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from .db import fetch_messages, Message
from .llm_client import LLMConfig, chat
from .prompts import get_prompts

log = logging.getLogger(__name__)

RUNS_DIR = Path(__file__).resolve().parent / "runs"


@dataclass
class RunConfig:
    pg_dsn: str = "postgresql://pguser:pgpass@localhost:5432/tgdata"
    job: str = "topics"                   # topics | style | custom
    sender_id: Optional[int] = None
    days_back: int = 0
    page_size: int = 2000
    max_messages: int = 500
    max_message_chars: int = 400
    max_batch_chars: int = 12000          # characters per batch sent to LLM
    max_batch_tokens: int = 3500          # rough token estimate limit
    model_name: str = ""                  # ignored now (providers chosen automatically)
    system_instruction: Optional[str] = None
    request_interval_s: float = 0.5
    timeout_s: float = 60.0
    max_requests: Optional[int] = None
    run_id: str = "default"
    prompt_override: Optional[str] = None


@dataclass
class RunState:
    phase: str = "map"        # map | reduce | done
    map_done: int = 0
    reduce_round: int = 0
    chunks_in_round: int = 0
    errors: int = 0


# ── Helpers ───────────────────────────────────────────────────────────────

def _estimate_tokens(text: str) -> int:
    """Rough token estimate for Russian/English mix."""
    return max(len(text) // 3, len(text.split()))


def _batch_messages(messages: list[Message], max_chars: int, max_tokens: int) -> list[list[Message]]:
    """Split messages into batches respecting char/token limits."""
    batches: list[list[Message]] = []
    current: list[Message] = []
    current_chars = 0

    for msg in messages:
        msg_chars = len(msg.text)
        if current and (current_chars + msg_chars > max_chars
                        or _estimate_tokens(
                            "\n".join(m.text for m in current) + "\n" + msg.text
                        ) > max_tokens):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(msg)
        current_chars += msg_chars

    if current:
        batches.append(current)
    return batches


def _format_messages(batch: list[Message]) -> str:
    """Format a batch of messages into a single string for the prompt."""
    lines = []
    for m in batch:
        lines.append(f"[{m.date}] {m.text}")
    return "\n".join(lines)


def _save_jsonl(path: Path, record: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _parse_json_response(text: str):
    """Try to parse LLM response as JSON, stripping markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove ```json ... ``` wrapper
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as e:
        return cleaned, str(e)


# ── Pipeline ──────────────────────────────────────────────────────────────

async def run_map_reduce(
    config: RunConfig,
    *,
    resume: bool = False,
    phase: str = "all",
) -> dict:
    """Execute the full map-reduce pipeline. Returns summary dict."""

    run_dir = RUNS_DIR / config.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save config
    with open(run_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, ensure_ascii=False, indent=2, default=str)

    state = RunState()
    map_outputs_path = run_dir / "map_outputs.jsonl"
    reduce_outputs_path = run_dir / "reduce_outputs.jsonl"
    errors_path = run_dir / "errors.jsonl"
    final_path = run_dir / "final.txt"

    if not resume:
        for p in [map_outputs_path, reduce_outputs_path, errors_path, final_path]:
            if p.exists():
                p.unlink()

    llm_cfg = LLMConfig(
        temperature=0.3,
        max_tokens=4096,
        mock=os.environ.get("ANALYZER_MOCK") == "1",
        timeout_s=config.timeout_s,
        request_interval_s=config.request_interval_s,
    )

    prompts = get_prompts(config.job)
    request_count = 0

    # ── MAP PHASE ─────────────────────────────────────────────────────
    if phase in ("all", "map"):
        log.info("=== MAP PHASE ===")
        messages = await fetch_messages(
            config.pg_dsn,
            sender_id=config.sender_id,
            days_back=config.days_back,
            max_messages=config.max_messages,
            max_message_chars=config.max_message_chars,
            page_size=config.page_size,
        )
        log.info("Total messages: %d", len(messages))

        batches = _batch_messages(messages, config.max_batch_chars, config.max_batch_tokens)
        log.info("Batches: %d", len(batches))

        map_results = []

        for i, batch in enumerate(batches):
            if config.max_requests and request_count >= config.max_requests:
                log.warning("Max requests reached (%d), stopping map", request_count)
                break

            batch_text = _format_messages(batch)
            char_count = len(batch_text)
            token_est = _estimate_tokens(batch_text)

            # Build prompt
            user_content = prompts["map_user"].format(
                messages=batch_text,
                prompt=config.prompt_override or "",
            )
            msgs = [
                {"role": "system", "content": prompts["map_system"]},
                {"role": "user", "content": user_content},
            ]

            try:
                raw = await chat(msgs, llm_cfg)
                request_count += 1
                result, parse_err = _parse_json_response(raw)
            except Exception as e:
                log.error("Map batch %d failed: %s", i, e)
                result = None
                parse_err = str(e)
                raw = ""
                state.errors += 1
                _save_jsonl(errors_path, {"phase": "map", "batch": i, "error": str(e)})

            record = {
                "batch_index": i,
                "message_count": len(batch),
                "char_count": char_count,
                "token_estimate": token_est,
                "parse_error": parse_err,
                "result": result,
                "raw_length": len(raw) if raw else 0,
            }
            _save_jsonl(map_outputs_path, record)
            if result is not None:
                map_results.append(result)
            state.map_done = i + 1
            log.info("  Batch %d/%d: %d msgs, %d chars → %s",
                     i + 1, len(batches), len(batch), char_count,
                     "OK" if not parse_err else f"parse_err={parse_err}")

        state.phase = "reduce"

    # ── REDUCE PHASE ──────────────────────────────────────────────────
    if phase in ("all", "reduce"):
        log.info("=== REDUCE PHASE ===")

        # Reload map results from disk
        if phase == "reduce":
            map_results = []
            with open(map_outputs_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        rec = json.loads(line)
                        if rec.get("result") is not None:
                            map_results.append(rec["result"])

        # Iteratively reduce
        partials = map_results
        round_num = 0
        chunk_size = 4  # merge N partial results at a time

        while len(partials) > 1:
            round_num += 1
            log.info("  Reduce round %d: %d partials, chunk_size=%d",
                     round_num, len(partials), chunk_size)
            new_partials = []

            for ci in range(0, len(partials), chunk_size):
                if config.max_requests and request_count >= config.max_requests:
                    log.warning("Max requests reached, stopping reduce")
                    break

                chunk = partials[ci:ci + chunk_size]
                chunk_json = json.dumps(chunk, ensure_ascii=False)

                user_content = prompts["reduce_user"].format(
                    partials=chunk_json,
                    prompt=config.prompt_override or "",
                )
                msgs = [
                    {"role": "system", "content": prompts["reduce_system"]},
                    {"role": "user", "content": user_content},
                ]

                try:
                    raw = await chat(msgs, llm_cfg)
                    request_count += 1
                    result, parse_err = _parse_json_response(raw)
                except Exception as e:
                    log.error("Reduce round %d chunk %d failed: %s", round_num, ci, e)
                    result = chunk[0]  # fallback: keep first
                    parse_err = str(e)
                    state.errors += 1
                    _save_jsonl(errors_path, {
                        "phase": "reduce", "round": round_num, "chunk": ci, "error": str(e)
                    })

                _save_jsonl(reduce_outputs_path, {
                    "round": round_num,
                    "chunk_index": ci,
                    "chunk_size": len(chunk),
                    "parse_error": parse_err,
                    "result": result,
                })
                new_partials.append(result)

            partials = new_partials
            state.reduce_round = round_num
            state.chunks_in_round = len(new_partials)

        # Write final
        final_result = partials[0] if partials else {}
        final_text = json.dumps(final_result, ensure_ascii=False, indent=2) \
            if not isinstance(final_result, str) else final_result
        final_path.write_text(final_text, encoding="utf-8")
        state.phase = "done" if phase == "all" else "reduce"
        log.info("Final output written to %s (%d chars)", final_path, len(final_text))

    # Save state
    with open(run_dir / "state.json", "w", encoding="utf-8") as f:
        json.dump(asdict(state), f, indent=2)

    return asdict(state)
