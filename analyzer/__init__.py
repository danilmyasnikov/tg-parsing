"""Analyzer package for AI-assisted insights and content tooling."""

from __future__ import annotations

from typing import List
from pathlib import Path
from dotenv import load_dotenv

from .llm_client import analyze_text
from .prompts import TOPIC_EXTRACTION_PROMPT, STYLE_ANALYSIS_PROMPT
from .context_loader import load_recent_messages

# Load repository .env early so all modules can rely on environment vars.
repo_root = Path(__file__).resolve().parents[1]
load_dotenv(repo_root / ".env")

__all__: List[str] = [
    "analyze_text",
    "TOPIC_EXTRACTION_PROMPT",
    "STYLE_ANALYSIS_PROMPT",
    "load_recent_messages",
]
