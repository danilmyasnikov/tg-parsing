"""Small demo script for the analyzer package.

This script demonstrates a quick call to the Google Gemini model using the
`google-genai` SDK. Types are annotated for static checking.
"""

from __future__ import annotations

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai.client import Client as GenaiClient
from google.genai import types as genai_types

# Build a typed client. Pass `GEMINI_API_KEY` explicitly to avoid ambiguous
# behavior across environments.
# Load repository .env (if present) then read API key (prefer GEMINI_API_KEY).
repo_root = Path(__file__).resolve().parents[1]
load_dotenv(repo_root / ".env")
api_key: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API")
if not api_key:
    raise SystemExit("GEMINI_API_KEY or GOOGLE_API must be set in the environment")

client: GenaiClient = genai.Client(api_key=api_key)

# Call the model and annotate the response precisely.
response: genai_types.GenerateContentResponse = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain how AI works in a few words",
)

print(getattr(response, "text", str(response)))
