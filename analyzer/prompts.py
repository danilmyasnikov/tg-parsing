"""Prompt templates for analyzer jobs."""

from __future__ import annotations

from typing import Final

TOPIC_EXTRACTION_PROMPT: Final[str] = (
    "Identify the top 5 recurring topics in this Telegram channel history. "
    "Return a JSON array of topic strings."
)

STYLE_ANALYSIS_PROMPT: Final[str] = (
    "Analyze the writing style (formal/informal, emoji usage, length) of these "
    "messages. Return JSON with fields: tone, emoji_usage, avg_length, notes."
)

__all__ = ["TOPIC_EXTRACTION_PROMPT", "STYLE_ANALYSIS_PROMPT"]
