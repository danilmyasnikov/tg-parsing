# Analyzer — detailed overview

The `analyzer` package formats Telegram messages stored in Postgres and runs short, focused analyses over large datasets using a map-reduce batching pattern. It is designed to process many messages without losing context, produce structured JSON outputs (topics, style summaries, or custom extractions), and support resumable long-running runs.

Key design goals
- Process large message volumes reliably using batching and resumable runs.
- Preserve cross-batch context during reduction to produce coherent final outputs.
- Keep prompts strict and language-consistent so outputs are parseable JSON.
- Offer a mock/offline mode for fast testing without paying for LLM calls.

When to use
- Quick analysis of recent channel/chat history (topics, stylistic overview).
- Large-scale extraction over an entire message archive (use `--run-id` and `--resume`).
- Custom extraction workflows where you provide your own prompt.

How it works (high-level)
1. Context loading: the package reads `messages` rows from Postgres and formats each row as a single-line record with a timestamp, sender id and truncated text. See `analyzer/context_loader.py`.
2. Map phase: messages are batched by character and token budgets and each batch is sent to the LLM with a strict "map" prompt. Each map response is written to `runs/<run-id>/map_outputs.jsonl` with parse results or raw text and parse errors.
3. Reduce phase: map outputs (already condensed JSON-like summaries) are re-chunked (with a larger budget) and sent to the LLM with a "reduce" prompt that merges and deduplicates across batches. The reduction repeats until a single final JSON/text result remains; this is written to `runs/<run-id>/final.txt`.
4. Resumability: state is saved to `runs/<run-id>/state.json` after each map request and after each reduce round so long runs can be resumed without reprocessing completed batches.

Primary components
- `context_loader.py` — DB access, formatting and safe keyset pagination, and batching utilities.
- `llm_client.py` — wraps the `google-genai` SDK, provides mock responses for offline testing, rate limiting and retries with server-suggested backoff handling.
- `prompts.py` — map/reduce and job prompt templates (topics, style, custom). Prompts are strict about JSON output and preserve message language.
- `batch_runner.py` — orchestrates map+reduce phases, state management, JSONL logging and final output generation.
- `main.py` — CLI entrypoint and argument parsing.

Quick setup
1. Create a virtualenv and install dependencies (Python 3.10+):

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

2. Create a `.env` in the repo root with at least:

```
GEMINI_API_KEY=your_gemini_api_key
PG_DSN=postgresql://pguser:pgpass@localhost:5432/tgdata
```

Notes
- The code reads `GEMINI_API_KEY` (preferred) and falls back to legacy `GOOGLE_API` if present.
- The Postgres `messages` table must include `sender_id, id, date, text` columns.

CLI usage (examples)
- Topics (map-reduce, resumable):

```powershell
python -m analyzer.main --job topics --days-back 7 --max-messages 1000 --run-id my-topics-run
```

- Style analysis:

```powershell
python -m analyzer.main --job style --days-back 7 --max-messages 1000 --run-id my-style-run
```

- Custom prompt (read prompt from file):

```powershell
python -m analyzer.main --job custom --prompt-file prompts.txt --days-back 0 --run-id my-custom-run
```

- Mock/offline testing (no LLM calls):

```powershell
python -m analyzer.main --job topics --max-messages 100 --run-id test-mock --mock
```

Important CLI flags
- `--run-id` — identifier for the run; required to resume previously interrupted runs.
- `--resume` — resume an existing `run-id`; validates config consistency.
- `--max-messages` — cap how many messages to process (useful for testing).
- `--batch-max-chars` / `--batch-max-tokens` — control map-phase batch sizes.
- `--request-interval` — minimum seconds between LLM requests (helps with rate limits).
- `--mock` — produce deterministic mock LLM responses for offline testing.

Output and artifacts
- `runs/<run-id>/config.json` — recorded config for the run.
- `runs/<run-id>/map_outputs.jsonl` — newline-delimited JSON records for every map request.
- `runs/<run-id>/reduce_outputs.jsonl` — reduce-round intermediate results.
- `runs/<run-id>/state.json` — resumable run state (last processed key, counters).
- `runs/<run-id>/final.txt` — the final reduced output (JSON formatted when applicable).

Troubleshooting & tips
- Missing API key: ensure `GEMINI_API_KEY` is available in env or `.env`.
- Rate limits / quotas: the LLM provider may return 429/RESOURCE_EXHAUSTED. The client performs exponential backoff and honors server-provided retry delays, but if your project quota is exhausted you'll need to upgrade the plan or use `--mock` to continue testing.
- JSON parse errors: map outputs include `parse_error` and `raw` when the LLM response isn't valid JSON. Use `map_outputs.jsonl` to inspect and adjust prompts in `prompts.py`.
- Language consistency: prompts are written to preserve the language of input messages; if you need translations, post-process the final JSON separately.

Developer notes
- To change analysis behavior, edit `analyzer/prompts.py` (map & reduce templates).
- For local E2E tests without API usage, run the provided `_e2e_test.py` script which uses mock mode.
- Add unit tests for `context_loader.format_messages` and `iter_message_batches` to avoid regressions during refactors.

Files of interest
- See `analyzer/context_loader.py`, `analyzer/llm_client.py`, `analyzer/prompts.py`, `analyzer/batch_runner.py` and `analyzer/main.py` for the core logic.

If you'd like, I can also:
- Add a short `examples/` folder with example prompts and run commands.
- Create a small test suite (pytest) targeting `context_loader` and the batching logic.

---
Updated to provide a clear, actionable reference for users and maintainers.


