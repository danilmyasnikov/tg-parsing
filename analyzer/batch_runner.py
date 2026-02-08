"""Batch map-reduce runner for analyzer jobs."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional, Tuple

from .context_loader import MessageKey, estimate_tokens, iter_message_batches
from .llm_client import RateLimiter, RetryConfig, analyze_text
from .prompts import (
    CUSTOM_MAP_PROMPT_TEMPLATE,
    CUSTOM_REDUCE_PROMPT_TEMPLATE,
    STYLE_MAP_PROMPT,
    STYLE_REDUCE_PROMPT,
    TOPIC_MAP_PROMPT,
    TOPIC_REDUCE_PROMPT,
)


@dataclass(frozen=True)
class RunConfig:
    pg_dsn: str
    job: str
    sender_id: Optional[str]
    days_back: int
    page_size: int
    max_messages: Optional[int]
    max_message_chars: int
    max_batch_chars: int
    max_batch_tokens: int
    model_name: str
    system_instruction: Optional[str]
    request_interval_s: float
    timeout_s: Optional[float]
    max_requests: Optional[int]
    run_id: str
    prompt_override: Optional[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_dir(run_id: str) -> Path:
    return _repo_root() / "analyzer" / "runs" / run_id


def _ensure_run_dir(run_id: str) -> Path:
    path = _run_dir(run_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _message_key_to_dict(key: MessageKey) -> dict[str, Any]:
    return {
        "date": key.date.isoformat(),
        "message_id": key.message_id,
        "sender_id": key.sender_id,
    }


def _message_key_from_dict(data: dict[str, Any]) -> MessageKey:
    return MessageKey(
        date=datetime.fromisoformat(data["date"]),
        message_id=int(data["message_id"]),
        sender_id=str(data["sender_id"]),
    )


def _load_state(path: Path) -> Optional[dict[str, Any]]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _load_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _try_parse_json(text: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        pass

    start_candidates = [text.find("{"), text.find("[")]
    start_candidates = [c for c in start_candidates if c != -1]
    if not start_candidates:
        return None, "no_json_start"

    start = min(start_candidates)
    end_candidates = [text.rfind("}"), text.rfind("]")]
    end_candidates = [c for c in end_candidates if c != -1]
    if not end_candidates:
        return None, "no_json_end"

    end = max(end_candidates)
    if end <= start:
        return None, "invalid_json_bounds"

    candidate = text[start : end + 1]
    try:
        return json.loads(candidate), None
    except json.JSONDecodeError as exc:
        return None, f"json_parse_error: {exc}"


def _chunk_items(
    items: Iterable[Any],
    max_chars: int,
    max_tokens: int,
) -> Iterable[list[Any]]:
    chunk: list[Any] = []
    chunk_chars = 0
    chunk_tokens = 0

    for item in items:
        serialized = json.dumps(item)
        item_chars = len(serialized) + 1
        item_tokens = estimate_tokens(serialized)

        if chunk and (chunk_chars + item_chars > max_chars or chunk_tokens + item_tokens > max_tokens):
            yield chunk
            chunk = []
            chunk_chars = 0
            chunk_tokens = 0

        chunk.append(item)
        chunk_chars += item_chars
        chunk_tokens += item_tokens

    if chunk:
        yield chunk


def _build_prompts(job: str, prompt_override: Optional[str]) -> Tuple[str, str]:
    if job == "topics":
        return TOPIC_MAP_PROMPT, TOPIC_REDUCE_PROMPT
    if job == "style":
        return STYLE_MAP_PROMPT, STYLE_REDUCE_PROMPT
    if job == "custom":
        if not prompt_override:
            raise SystemExit("--prompt or --prompt-file is required for job=custom")
        return (
            CUSTOM_MAP_PROMPT_TEMPLATE.format(user_prompt=prompt_override),
            CUSTOM_REDUCE_PROMPT_TEMPLATE.format(user_prompt=prompt_override),
        )
    raise SystemExit(f"Unknown job: {job}")


def _default_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"run-{stamp}-{uuid.uuid4().hex[:6]}"


def _load_or_init_config(run_dir: Path, config: RunConfig, resume: bool) -> RunConfig:
    config_path = run_dir / "config.json"
    if resume and config_path.exists():
        stored = json.loads(config_path.read_text(encoding="utf-8"))
        if (
            stored.get("job") != config.job
            or stored.get("pg_dsn") != config.pg_dsn
            or stored.get("sender_id") != config.sender_id
            or stored.get("days_back") != config.days_back
        ):
            raise SystemExit("Resume config mismatch: job, pg_dsn, sender_id, or days_back changed.")
        return config

    config_path.write_text(json.dumps(config.__dict__, indent=2), encoding="utf-8")
    return config


async def run_map_phase(config: RunConfig, resume: bool) -> Path:
    run_dir = _ensure_run_dir(config.run_id)
    config = _load_or_init_config(run_dir, config, resume)

    state_path = run_dir / "state.json"
    map_path = run_dir / "map_outputs.jsonl"
    error_path = run_dir / "errors.jsonl"

    state = _load_state(state_path) if resume else None
    last_key = _message_key_from_dict(state["last_key"]) if state and state.get("last_key") else None
    batches_completed = state.get("batches_completed", 0) if state else 0
    messages_processed = state.get("messages_processed", 0) if state else 0
    requests_made = state.get("requests_made", 0) if state else 0

    map_prompt, _ = _build_prompts(config.job, config.prompt_override)
    rate_limiter = RateLimiter(min_interval_s=config.request_interval_s)
    retry_config = RetryConfig()

    async for batch in iter_message_batches(
        pg_dsn=config.pg_dsn,
        sender_id=config.sender_id,
        days_back=config.days_back,
        page_size=config.page_size,
        max_message_chars=config.max_message_chars,
        max_batch_chars=config.max_batch_chars,
        max_batch_tokens=config.max_batch_tokens,
        start_key=last_key,
        max_messages=config.max_messages,
    ):
        if config.max_requests is not None and requests_made >= config.max_requests:
            break

        try:
            response = await analyze_text(
                prompt=map_prompt,
                context_data=batch.text,
                model_name=config.model_name,
                system_instruction=config.system_instruction,
                retry_config=retry_config,
                timeout_s=config.timeout_s,
                rate_limiter=rate_limiter,
            )
        except Exception as exc:  # noqa: BLE001
            _append_jsonl(
                error_path,
                {
                    "at": _now_iso(),
                    "batch_index": batches_completed,
                    "error": str(exc),
                },
            )
            raise

        parsed, parse_error = _try_parse_json(response)
        record = {
            "batch_index": batches_completed,
            "first_key": _message_key_to_dict(batch.first_key),
            "last_key": _message_key_to_dict(batch.last_key),
            "message_count": len(batch.rows),
            "char_count": batch.char_count,
            "token_estimate": batch.token_estimate,
            "result": parsed,
            "raw": response if parsed is None else None,
            "parse_error": parse_error,
            "created_at": _now_iso(),
        }
        _append_jsonl(map_path, record)

        batches_completed += 1
        messages_processed += len(batch.rows)
        requests_made += 1
        last_key = batch.last_key

        _save_state(
            state_path,
            {
                "run_id": config.run_id,
                "job": config.job,
                "phase": "map",
                "batches_completed": batches_completed,
                "messages_processed": messages_processed,
                "requests_made": requests_made,
                "last_key": _message_key_to_dict(last_key),
                "updated_at": _now_iso(),
            },
        )

    return map_path


async def run_reduce_phase(config: RunConfig, map_path: Path, resume: bool) -> str:
    run_dir = _ensure_run_dir(config.run_id)
    config = _load_or_init_config(run_dir, config, resume)

    state_path = run_dir / "state.json"
    reduce_path = run_dir / "reduce_outputs.jsonl"

    _, reduce_prompt = _build_prompts(config.job, config.prompt_override)
    rate_limiter = RateLimiter(min_interval_s=config.request_interval_s)
    retry_config = RetryConfig()

    records = list(_load_jsonl(map_path))
    items: list[Any] = []
    for record in records:
        if record.get("result") is not None:
            items.append(record["result"])
        else:
            items.append(
                {
                    "raw": record.get("raw"),
                    "parse_error": record.get("parse_error"),
                }
            )

    round_index = 0
    # Reduce items are condensed summaries, much smaller than raw message
    # batches.  Use 4x the map-phase limits so all map outputs typically
    # fit into a single reduce request, preserving cross-batch context.
    reduce_max_chars = config.max_batch_chars * 4
    reduce_max_tokens = config.max_batch_tokens * 4
    while True:
        round_index += 1
        next_items: list[Any] = []
        for chunk in _chunk_items(items, reduce_max_chars, reduce_max_tokens):
            data = json.dumps(chunk, ensure_ascii=False)
            response = await analyze_text(
                prompt=reduce_prompt,
                context_data=data,
                model_name=config.model_name,
                system_instruction=config.system_instruction,
                retry_config=retry_config,
                timeout_s=config.timeout_s,
                rate_limiter=rate_limiter,
            )
            parsed, _ = _try_parse_json(response)
            next_item = parsed if parsed is not None else response
            next_items.append(next_item)
            _append_jsonl(
                reduce_path,
                {
                    "round": round_index,
                    "chunk_size": len(chunk),
                    "result": next_item,
                    "created_at": _now_iso(),
                },
            )

        items = next_items

        _save_state(
            state_path,
            {
                "run_id": config.run_id,
                "job": config.job,
                "phase": "reduce",
                "reduce_round": round_index,
                "chunks_in_round": len(items),
                "updated_at": _now_iso(),
            },
        )

        if len(items) <= 1:
            break

    final_output = items[0] if items else ""
    if isinstance(final_output, (dict, list)):
        final_text = json.dumps(final_output, indent=2, ensure_ascii=False)
    else:
        final_text = str(final_output)

    final_path = run_dir / "final.txt"
    final_path.write_text(final_text, encoding="utf-8")
    return final_text


async def run_map_reduce(config: RunConfig, resume: bool, phase: str) -> str:
    if not config.run_id:
        config = RunConfig(**{**config.__dict__, "run_id": _default_run_id()})

    map_path = _run_dir(config.run_id) / "map_outputs.jsonl"

    if phase in ("map", "all"):
        map_path = await run_map_phase(config, resume=resume)

    if phase in ("reduce", "all"):
        if not map_path.exists():
            raise SystemExit("map_outputs.jsonl not found. Run map phase first.")
        return await run_reduce_phase(config, map_path, resume=resume)

    return ""
