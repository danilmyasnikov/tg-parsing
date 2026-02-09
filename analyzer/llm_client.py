"""
Unified LLM client – tries Cerebras first, falls back to Groq.
Both expose an OpenAI-compatible chat completions API.
"""
import os
import json
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider wrappers (sync calls executed in a thread so the rest stays async)
# ---------------------------------------------------------------------------

def _call_cerebras(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    from cerebras.cloud.sdk import Cerebras
    client = Cerebras(api_key=os.environ["CEREBRAS_API_KEY"])
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def _call_groq(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# Mock provider for testing without API keys
# ---------------------------------------------------------------------------

_MOCK_RESPONSES = {
    "topics": json.dumps([
        {"topic": "Криптовалюта", "count_hint": 30},
        {"topic": "Политика", "count_hint": 20},
        {"topic": "Технологии", "count_hint": 15},
        {"topic": "Финансы", "count_hint": 10},
        {"topic": "Юмор", "count_hint": 8},
    ], ensure_ascii=False),
    "style": json.dumps({
        "tone": "неформальный, ироничный",
        "avg_length": "короткие сообщения",
        "emoji_use": "умеренное",
        "vocabulary": "разговорный с жаргоном",
    }, ensure_ascii=False),
    "default": json.dumps({"summary": "Mock summary of the messages."}, ensure_ascii=False),
}


def _call_mock(messages: list[dict], **_kw) -> str:
    # Determine which mock to return based on system prompt content
    sys_text = " ".join(m.get("content", "") for m in messages if m["role"] == "system").lower()
    if "topic" in sys_text or "тем" in sys_text:
        return _MOCK_RESPONSES["topics"]
    if "style" in sys_text or "стил" in sys_text:
        return _MOCK_RESPONSES["style"]
    return _MOCK_RESPONSES["default"]


# ---------------------------------------------------------------------------
# Public async interface
# ---------------------------------------------------------------------------

@dataclass
class LLMConfig:
    """LLM configuration passed around the pipeline."""
    cerebras_model: str = "llama-4-scout-17b-16e-instruct"
    groq_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.3
    max_tokens: int = 4096
    mock: bool = False
    timeout_s: float = 60.0
    request_interval_s: float = 0.5  # polite pause between requests

_last_request_time: float = 0.0
_lock = asyncio.Lock()


async def chat(
    messages: list[dict],
    cfg: LLMConfig,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """Send a chat completion request. Returns the assistant text."""
    global _last_request_time

    temp = temperature if temperature is not None else cfg.temperature
    mt = max_tokens if max_tokens is not None else cfg.max_tokens

    if cfg.mock or os.environ.get("ANALYZER_MOCK") == "1":
        return _call_mock(messages)

    # Rate-limit
    async with _lock:
        now = asyncio.get_event_loop().time()
        wait = cfg.request_interval_s - (now - _last_request_time)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request_time = asyncio.get_event_loop().time()

    loop = asyncio.get_event_loop()

    # Try Cerebras first
    cerebras_key = os.environ.get("CEREBRAS_API_KEY", "")
    if cerebras_key:
        try:
            text = await asyncio.wait_for(
                loop.run_in_executor(
                    None, _call_cerebras, cfg.cerebras_model, messages, temp, mt
                ),
                timeout=cfg.timeout_s,
            )
            log.debug("Cerebras OK, %d chars", len(text))
            return text
        except Exception as e:
            log.warning("Cerebras failed (%s), falling back to Groq", e)

    # Fallback to Groq
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        try:
            text = await asyncio.wait_for(
                loop.run_in_executor(
                    None, _call_groq, cfg.groq_model, messages, temp, mt
                ),
                timeout=cfg.timeout_s,
            )
            log.debug("Groq OK, %d chars", len(text))
            return text
        except Exception as e:
            log.error("Groq also failed: %s", e)
            raise

    raise RuntimeError("No LLM API key configured. Set CEREBRAS_API_KEY or GROQ_API_KEY in .env")
