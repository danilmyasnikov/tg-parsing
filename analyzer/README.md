# Analyzer

The analyzer package loads recent Telegram messages from Postgres, formats
them into a compact context, and sends that context to Gemini for analysis.
It supports basic jobs like topic extraction and style analysis, and is built
to be a simple, deployable component in the repository.

## How it works

1. **Context loading**: `analyzer.context_loader.load_recent_messages()` pulls
	 rows from the `messages` table (sender_id, id, date, text), applies
	 truncation to long messages, and formats a chronological context block.
2. **Prompt selection**: `analyzer.prompts` provides two default prompt
	 templates: topic extraction and style analysis.
3. **LLM call**: `analyzer.llm_client.analyze_text()` sends the prompt and
	 context to Gemini via the `google-genai` SDK and returns plain text.

## Requirements

- Python 3.10+
- Postgres running (local Docker compose or external instance)
- `messages` table populated by the collector

## Setup

1. **Install dependencies**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. **Configure `.env`**

Add these to the repo root `.env` file:

```
GOOGLE_API=your_gemini_api_key
PG_DSN=postgresql://pguser:pgpass@localhost:5432/tgdata
```

Notes:
- `GOOGLE_API` is preferred; `GEMINI_API_KEY` also works.
- `PG_DSN` is optional on the CLI if you pass `--pg-dsn`.

## Usage examples

### Topic extraction (default)

```powershell
.\.venv\Scripts\python.exe -m analyzer.main --job topics --days-back 7 --limit 500
```

### Style analysis

```powershell
.\.venv\Scripts\python.exe -m analyzer.main --job style --days-back 30 --limit 1000
```

### Analyze a single channel (by sender_id)

```powershell
.\.venv\Scripts\python.exe -m analyzer.main --job topics --sender-id 2118600117 --days-back 14 --limit 300
```

### Provide DSN explicitly

```powershell
.\.venv\Scripts\python.exe -m analyzer.main --job topics --pg-dsn "postgresql://pguser:pgpass@localhost:5432/tgdata"
```

## Troubleshooting

- **Missing API key**: ensure `.env` exists in the repo root and contains
	`GOOGLE_API`. The loader also accepts `GEMINI_API_KEY`.
- **No output**: likely no messages in the selected time window. Try a larger
	`--days-back` or confirm the `messages` table has data.
- **Postgres connection error**: confirm Postgres is running and `PG_DSN`
	points to the correct host/port/user/password.

## Files

- `analyzer/context_loader.py` — Postgres query + message formatting
- `analyzer/llm_client.py` — Gemini client wrapper (`google-genai`)
- `analyzer/prompts.py` — default prompt templates
- `analyzer/main.py` — CLI entry point

## Notes

- Uses `google-genai` (recommended SDK).
- Messages are pulled from the existing `messages` table (sender_id, id, date, text).
