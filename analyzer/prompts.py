"""Prompt templates for analyzer jobs."""

from __future__ import annotations

from typing import Final

TOPIC_EXTRACTION_PROMPT: Final[str] = (
    "Identify the top 5 recurring topics in this Telegram channel history. "
    "Return a JSON array of topic strings."
)

TOPIC_MAP_PROMPT: Final[str] = (
    "You will receive a batch of Telegram messages in DATA. "
    "Extract up to 12 recurring topics from this batch. "
    "IMPORTANT: Use the SAME language as the messages for topic names. "
    "Return ONLY valid JSON: an array of objects with keys "
    '"topic" (string), "count_hint" (int, approximate), and "evidence" (short string).'
)

TOPIC_REDUCE_PROMPT: Final[str] = (
    "You will receive a JSON array of topic arrays/objects in DATA. "
    "These are extracted from different batches of the SAME dataset. "
    "Merge and deduplicate the topics across all batches, combining similar ones. "
    "Keep the ORIGINAL language of topics (do not translate). "
    "Return ONLY a valid JSON array of the top 5 topic strings."
)

STYLE_ANALYSIS_PROMPT: Final[str] = (
    "Analyze the writing style (formal/informal, emoji usage, length) of these "
    "messages. Return JSON with fields: tone, emoji_usage, avg_length, notes."
)

STYLE_MAP_PROMPT: Final[str] = (
    "You will receive a batch of Telegram messages in DATA. "
    "Analyze writing style for this batch. "
    "Return ONLY JSON with keys: tone (string), emoji_usage (string), "
    "avg_length (number), notes (string), message_count (int)."
)

STYLE_REDUCE_PROMPT: Final[str] = (
    "You will receive a JSON array of batch style objects in DATA. "
    "These are style analyses from different batches of the SAME dataset. "
    "Combine them into a single coherent style analysis. Use message_count to "
    "weight avg_length. Return ONLY valid JSON with keys: tone, emoji_usage, avg_length, notes."
)

CUSTOM_MAP_PROMPT_TEMPLATE: Final[str] = (
    "You are preparing evidence to answer the user's request: \"{user_prompt}\". "
    "From the DATA messages, extract only relevant facts, claims, or observations. "
    "Use the SAME language as the messages in your output. "
    "Return ONLY valid JSON with keys: facts (array of strings), "
    "notable_messages (array of short strings), and summary (string)."
)

CUSTOM_REDUCE_PROMPT_TEMPLATE: Final[str] = (
    "You are answering the user's request: \"{user_prompt}\". "
    "You will receive a JSON array of batch summaries in DATA. "
    "These summaries come from different batches of the SAME dataset. "
    "Synthesize a final coherent answer that follows the user's requested format. "
    "If the user requested JSON, output JSON only. Ignore invalid entries."
)

__all__ = [
    "TOPIC_EXTRACTION_PROMPT",
    "STYLE_ANALYSIS_PROMPT",
    "TOPIC_MAP_PROMPT",
    "TOPIC_REDUCE_PROMPT",
    "STYLE_MAP_PROMPT",
    "STYLE_REDUCE_PROMPT",
    "CUSTOM_MAP_PROMPT_TEMPLATE",
    "CUSTOM_REDUCE_PROMPT_TEMPLATE",
]
