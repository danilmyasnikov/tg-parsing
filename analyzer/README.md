# Analyzer

Lightweight package that formats recent Telegram messages from Postgres and
sends them to the Gemini model (via the `google-genai` SDK) for short
analyses such as topic extraction and sentiment.

This `analyzer` module is experimental — use the `feature/gemini-analyzer`
branch for ongoing changes.

Requirements
- Python 3.10+
- Postgres accessible via `PG_DSN` (see examples)
- `messages` table populated with columns: `sender_id, id, date, text`

Quick setup
1. Create and activate a virtual environment and install deps:

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

2. Add a `.env` in the repo root with at least:

```
GEMINI_API_KEY=your_gemini_api_key
PG_DSN=postgresql://pguser:pgpass@localhost:5432/tgdata
```

Notes:
- This code prefers `GEMINI_API_KEY` environment variable (it also accepts
	the legacy `GOOGLE_API` name for compatibility).
- `google-genai` must be installed (listed in `requirements.txt`).

Usage
- Run the CLI (topics or style):

```powershell
python -m analyzer.main --job topics --days-back 7 --limit 500
```

- Quick runners added for experimentation:
	- `python -m analyzer.run_topics` — strict topic extraction (JSON array)
	- `python -m analyzer.run_sentiment` — structured sentiment JSON
	- `python -m analyzer.inspect_data` — show formatted DATA and ask the model

Hints & troubleshooting
- Missing API key: ensure `.env` contains `GEMINI_API_KEY` and that the
	environment has been reloaded (restart shell or run `set`/`$env:` accordingly).
- No output from the analyzer: try a larger `--days-back` or increase
	`--limit`. Use `python -m analyzer.db_inspect` to inspect the `messages`
	table contents locally.
- If the analyzer echoes prompts or returns prose instead of JSON, try the
	strict runners (above) or adjust prompts in `analyzer/prompts.py`.

Files of interest
- `analyzer/context_loader.py` — loads and formats messages from Postgres
- `analyzer/llm_client.py` — wraps `google-genai` calls and handles API key
- `analyzer/prompts.py` — built-in prompt templates
- `analyzer/main.py` — CLI entrypoint used for basic jobs

Next steps
- Consider adding a small CI job for `mypy` and unit checks for
	`context_loader.format_messages` to prevent regressions when iterating.

