"""
Generate an original Telegram post based on analysis results.
"""
import json
import logging
from pathlib import Path

from .llm_client import LLMConfig, chat
from .prompts import POST_SYSTEM, POST_USER

log = logging.getLogger(__name__)

RUNS_DIR = Path(__file__).resolve().parent / "runs"


async def generate_post(
    topics_run_id: str = "prod-topics",
    style_run_id: str = "prod-style",
    output_run_id: str = "prod-post",
    llm_cfg: LLMConfig | None = None,
) -> str:
    """Read topics + style analysis, generate a Telegram post."""
    if llm_cfg is None:
        llm_cfg = LLMConfig()

    # Load topics
    topics_path = RUNS_DIR / topics_run_id / "final.txt"
    topics_text = topics_path.read_text(encoding="utf-8").strip() if topics_path.exists() else "[]"

    # Load style
    style_path = RUNS_DIR / style_run_id / "final.txt"
    style_text = style_path.read_text(encoding="utf-8").strip() if style_path.exists() else "{}"

    user_content = POST_USER.format(topics=topics_text, style=style_text)
    messages = [
        {"role": "system", "content": POST_SYSTEM},
        {"role": "user", "content": user_content},
    ]

    post_text = await chat(messages, llm_cfg, temperature=0.7, max_tokens=2048)

    # Save
    out_dir = RUNS_DIR / output_run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "post.txt").write_text(post_text, encoding="utf-8")
    log.info("Post saved to %s (%d chars)", out_dir / "post.txt", len(post_text))

    return post_text
