"""Gemini client wrapper for analysis tasks (google.genai SDK)."""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
import time
from collections import Counter
from pathlib import Path
from typing import Optional, Any, Tuple

from dotenv import dotenv_values
from google import genai


def _get_api_key() -> str:
    # Prefer `GEMINI_API_KEY` (new name); fall back to legacy `GOOGLE_API`.
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API")
    if not api_key:
        repo_root = Path(__file__).resolve().parents[1]
        values = dotenv_values(repo_root / ".env")
        api_key = values.get("GEMINI_API_KEY") or values.get("GOOGLE_API")
    if not api_key:
        raise RuntimeError(
            "Missing API key. Set GEMINI_API_KEY (preferred) or GOOGLE_API in .env or env."
        )
    return api_key


def _build_client() -> Any:
    """Create and return a google.genai client.

    Use an untyped return to avoid hard dependency on a specific SDK type
    in type-checking environments.
    """
    return genai.Client(api_key=_get_api_key())


def _extract_words(text: str) -> list[str]:
    # Keep ascii and cyrillic words, drop short tokens.
    tokens = re.findall(r"[A-Za-zА-Яа-яЁё0-9]{3,}", text.lower())
    stopwords = {
        "the",
        "and",
        "for",
        "that",
        "this",
        "with",
        "you",
        "your",
        "from",
        "not",
        "are",
        "but",
        "have",
        "was",
        "they",
        "them",
        "our",
        "about",
        "into",
        "out",
        "there",
        "here",
        "как",
        "что",
        "это",
        "для",
        "она",
        "они",
        "есть",
        "его",
        "или",
        "если",
        "будет",
        "так",
        "уже",
        "при",
        "только",
    }
    return [t for t in tokens if t not in stopwords and not t.isdigit()]


def _detect_emoji(text: str) -> bool:
    return bool(re.search(r"[\U0001F300-\U0001FAFF]", text))


def _mock_topics_from_text(text: str, limit: int) -> list[str]:
    words = _extract_words(text)
    counts = Counter(words)
    if not counts:
        return []
    return [word for word, _ in counts.most_common(limit)]


def _mock_style_from_text(text: str) -> dict[str, Any]:
    lines = [line for line in text.splitlines() if line.strip()]
    lengths = [len(line) for line in lines]
    avg_len = sum(lengths) / len(lengths) if lengths else 0.0
    emoji_usage = "some" if _detect_emoji(text) else "none"
    tone = "neutral"
    return {
        "tone": tone,
        "emoji_usage": emoji_usage,
        "avg_length": round(avg_len, 2),
        "notes": "mock analysis",
        "message_count": len(lines),
    }


def _flatten_topic_items(items: Any) -> list[str]:
    topics: list[str] = []
    if isinstance(items, list):
        for item in items:
            topics.extend(_flatten_topic_items(item))
    elif isinstance(items, dict):
        if "topic" in items and isinstance(items["topic"], str):
            topics.append(items["topic"])
    elif isinstance(items, str):
        topics.append(items)
    return topics


def _mock_response(prompt: str, context_data: str) -> str:
    if "Extract up to 12 recurring topics" in prompt:
        topics = _mock_topics_from_text(context_data, limit=12)
        return json.dumps(
            [
                {"topic": t, "count_hint": 1, "evidence": f"{t} mentioned"}
                for t in topics
            ]
        )
    if "Merge and deduplicate the topics" in prompt:
        try:
            items = json.loads(context_data)
        except json.JSONDecodeError:
            items = []
        topics = _flatten_topic_items(items)
        counts = Counter(topics)
        return json.dumps([t for t, _ in counts.most_common(5)])

    if "Analyze writing style for this batch" in prompt:
        return json.dumps(_mock_style_from_text(context_data))
    if "Combine them into a single style analysis" in prompt:
        try:
            items = json.loads(context_data)
        except json.JSONDecodeError:
            items = []
        if not isinstance(items, list) or not items:
            return json.dumps(_mock_style_from_text(""))
        total_msgs = sum(int(item.get("message_count", 0)) for item in items if isinstance(item, dict))
        if total_msgs == 0:
            return json.dumps(_mock_style_from_text(""))
        avg_len = 0.0
        tone_counts = Counter()
        emoji_counts = Counter()
        for item in items:
            if not isinstance(item, dict):
                continue
            msg_count = int(item.get("message_count", 0))
            avg_len += float(item.get("avg_length", 0.0)) * msg_count
            tone_counts[item.get("tone", "neutral")] += msg_count
            emoji_counts[item.get("emoji_usage", "none")] += msg_count
        avg_len = avg_len / total_msgs
        return json.dumps(
            {
                "tone": tone_counts.most_common(1)[0][0],
                "emoji_usage": emoji_counts.most_common(1)[0][0],
                "avg_length": round(avg_len, 2),
                "notes": "mock combined analysis",
            }
        )

    if "extract only relevant facts" in prompt:
        lines = [line.strip() for line in context_data.splitlines() if line.strip()]
        facts = lines[:5]
        return json.dumps(
            {
                "facts": facts,
                "notable_messages": facts[:3],
                "summary": f"mock summary based on {len(lines)} messages",
            }
        )
    if "Synthesize a final answer" in prompt:
        try:
            items = json.loads(context_data)
        except json.JSONDecodeError:
            items = []
        summaries = []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    if item.get("summary"):
                        summaries.append(str(item["summary"]))
        if not summaries:
            return json.dumps({"summary": "mock summary", "facts": []})
        return json.dumps({"summary": " ".join(summaries)[:1000], "facts": []})

    if "Return a JSON array of topic strings" in prompt:
        topics = _mock_topics_from_text(context_data, limit=5)
        return json.dumps(topics)
    if "Return JSON with fields: tone" in prompt:
        style = _mock_style_from_text(context_data)
        style.pop("message_count", None)
        return json.dumps(style)

    return json.dumps({"status": "mock", "message": "no matching prompt rule"})


class RateLimiter:
    def __init__(self, min_interval_s: float = 1.0) -> None:
        self._min_interval_s = min_interval_s
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            delay = self._min_interval_s - (now - self._last_call)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_call = time.monotonic()


class RetryConfig:
    def __init__(
        self,
        max_retries: int = 6,
        initial_backoff_s: float = 2.0,
        max_backoff_s: float = 65.0,
        jitter_s: float = 1.0,
    ) -> None:
        self.max_retries = max_retries
        self.initial_backoff_s = initial_backoff_s
        self.max_backoff_s = max_backoff_s
        self.jitter_s = jitter_s


def _extract_retry_delay(exc: Exception) -> Optional[float]:
    """Try to extract server-suggested retry delay from Gemini error."""
    msg = str(exc)
    # Pattern: "retry in 44.443268429s" or "retryDelay: '44s'"
    match = re.search(r'retry\s+in\s+([\d.]+)s', msg, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    match = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?([\d.]+)s", msg, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def _classify_error(exc: Exception) -> Tuple[bool, str]:
    message = str(exc).lower()
    # 429 / RESOURCE_EXHAUSTED with a per-minute quota id is retryable.
    # However, if the error mentions "PerDay" quota AND limit: 0 (or the
    # daily cap is clearly hit), further retries within the same minute
    # won't help — but we still mark it retryable so the runner can
    # respect the server-provided delay.  The retry loop's finite
    # max_retries prevents infinite waits.
    if "429" in message or "resource_exhausted" in message:
        # Distinguish hard daily exhaustion (limit: 0 / PerDay)
        if "perday" in message and ("limit: 0" in message or "limit\": 0" in message):
            return False, "daily_quota_exhausted"
        return True, "rate_limit"
    if "rate" in message and "limit" in message:
        return True, "rate_limit"
    if "quota" in message or "billing" in message or "insufficient" in message:
        return False, "quota"
    if "permission" in message or "unauthorized" in message or "forbidden" in message:
        return False, "auth"
    if "invalid" in message or "argument" in message:
        return False, "invalid_request"
    if "timeout" in message or "timed out" in message or "deadline" in message:
        return True, "timeout"
    if "unavailable" in message or "500" in message or "502" in message or "503" in message:
        return True, "server_error"
    return False, "unknown"


async def analyze_text(
    prompt: str,
    context_data: str,
    model_name: str = "gemini-3-flash-preview",
    system_instruction: Optional[str] = None,
    retry_config: Optional[RetryConfig] = None,
    timeout_s: Optional[float] = 120.0,
    rate_limiter: Optional[RateLimiter] = None,
) -> str:
    """Analyze context_data using Gemini and return model text output."""
    if os.getenv("ANALYZER_MOCK") == "1":
        return _mock_response(prompt, context_data)
    # If a system-level instruction is provided, prepend it to the prompt
    # since the SDK does not accept `system_instruction` as a keyword.
    content = f"{prompt}\n\nDATA:\n{context_data}"
    if system_instruction:
        content = f"SYSTEM INSTRUCTION: {system_instruction}\n\n{content}"

    def _call() -> str:
        client = _build_client()
        # The google.genai SDK returns a response object; prefer `text`
        # attribute when present, otherwise fall back to string form.
        response = client.models.generate_content(
            model=model_name,
            contents=content,
        )
        return getattr(response, "text", str(response))

    config = retry_config or RetryConfig()
    attempt = 0

    while True:
        if rate_limiter:
            await rate_limiter.wait()

        try:
            if timeout_s:
                return await asyncio.wait_for(asyncio.to_thread(_call), timeout=timeout_s)
            return await asyncio.to_thread(_call)
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, asyncio.TimeoutError):
                retryable, reason = True, "timeout"
            else:
                retryable, reason = _classify_error(exc)
            if attempt >= config.max_retries or not retryable:
                raise RuntimeError(f"LLM call failed ({reason}): {exc}") from exc

            # Use server-suggested delay if available (e.g. Gemini 429s)
            server_delay = _extract_retry_delay(exc)
            if server_delay and server_delay > 0:
                backoff = server_delay + random.uniform(1, config.jitter_s + 2)
                print(f"[analyzer] Rate limited, server says retry in {server_delay:.0f}s. Waiting {backoff:.1f}s (attempt {attempt + 1}/{config.max_retries})...")
            else:
                backoff = min(config.max_backoff_s, config.initial_backoff_s * (2**attempt))
                backoff += random.uniform(0, config.jitter_s)
                print(f"[analyzer] Retryable error ({reason}), waiting {backoff:.1f}s (attempt {attempt + 1}/{config.max_retries})...")
            await asyncio.sleep(backoff)
            attempt += 1
