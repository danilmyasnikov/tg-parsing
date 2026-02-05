"""Gemini client wrapper for analysis tasks (google.genai SDK)."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Optional, Any

from dotenv import dotenv_values
from google import genai


def _get_api_key() -> str:
    # Prefer `GEMINI_API_KEY` (new name); fall back to legacy `GOOGLE_API`.
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API")
    if not api_key:
        repo_root = Path(__file__).resolve().parents[1]
        values = dotenv_values(repo_root / ".env")
        api_key = values.get("GOOGLE_API") or values.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing API key. Set GOOGLE_API (preferred) or GEMINI_API_KEY in .env or env."
        )
    return api_key


def _build_client() -> Any:
    """Create and return a google.genai client.

    Use an untyped return to avoid hard dependency on a specific SDK type
    in type-checking environments.
    """
    return genai.Client(api_key=_get_api_key())


async def analyze_text(
    prompt: str,
    context_data: str,
    model_name: str = "gemini-3-flash-preview",
    system_instruction: Optional[str] = None,
) -> str:
    """Analyze context_data using Gemini and return model text output."""
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

    return await asyncio.to_thread(_call)
