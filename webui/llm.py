"""LLM integration for web UI chat."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path to import analyzer
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer.llm_client import analyze_text

# Available models - currently only Gemini
AVAILABLE_MODELS = [
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
]

DEFAULT_MODEL = "gemini-2.0-flash"


async def chat_with_context(
    user_message: str,
    context_messages: list[dict],
    model_id: str = DEFAULT_MODEL,
    system_instruction: Optional[str] = None,
) -> str:
    """
    Send a chat message with context from selected channels.
    
    Args:
        user_message: The user's question or prompt
        context_messages: List of messages from selected channels
        model_id: The model to use for generation
        system_instruction: Optional system instruction
    
    Returns:
        The model's response text
    """
    # Format context data from messages
    if context_messages:
        context_parts = []
        for msg in context_messages:
            sender = msg.get("sender_id", "Unknown")
            date = msg.get("date", "Unknown date")
            text = msg.get("text", "")
            if text:
                context_parts.append(f"[{sender}] ({date}): {text}")
        context_data = "\n".join(context_parts)
    else:
        context_data = "No messages selected as context."
    
    # Default system instruction for chat
    if system_instruction is None:
        system_instruction = (
            "You are a helpful assistant analyzing Telegram channel messages. "
            "The user will ask questions about the provided message data. "
            "Answer based on the context provided. If the context doesn't contain "
            "relevant information, say so."
        )
    
    response = await analyze_text(
        prompt=user_message,
        context_data=context_data,
        model_name=model_id,
        system_instruction=system_instruction,
    )
    
    return response


def get_available_models() -> list[dict]:
    """Return list of available models."""
    return AVAILABLE_MODELS
