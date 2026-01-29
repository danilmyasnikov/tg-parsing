# TG-parsing — Developer README

This repository contains small Telethon-based utilities for inspecting dialogs
and fetching channel messages. The codebase is intentionally minimal and
focused on a reproducible developer workflow with an async Postgres sink for
message storage.

This README documents a detailed developer setup, how to run the fetcher,
database wiring (Docker), and notes about recent design changes in the code
(pool initialization, PEP-604 typing, race-safe pool creation).

Prerequisites 🚧
 - Python 3.10+ (project uses PEP-604 `X | None` annotations)
 - Git
 - Docker (recommended for Postgres local dev)

Quick local setup (PowerShell) ⚙️

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Credentials (.env) 🔐

Create a `.env` file in the project root (do NOT commit) with your Telegram
credentials. Example:

```
TG_API_ID=123456
TG_API_HASH=your_api_hash_here
# Optional: phone to avoid retyping each run
TG_PHONE=+7999xxxxxxx
# Optional: session name
SESSION_NAME=session
```

On first run a Telethon session file will be created (ignored by git).

Repository layout (high level)
 - `config.py` — load `config.json` and environment credentials
 - `client.py` — async Telethon client context manager
 - `annotations.py` — type aliases used for editor/type-checker convenience
 - `resolver.py` — resolve CLI `target` to a Telethon entity
 - `parser.py` — async message iterators (resumable)
 - `fetcher.py` — consumes `parser` and calls a `store_func` for each message
 - `storage.py` — storage sinks: `print_store` and `postgres_store`
 - `export_targets.py` — exports dialog identifiers
 - `fetch_messages.py` — CLI runner used during development/testing
 - `scripts/` — helper scripts (truncate/inspect DB, demos)

Config example

`config.json` contains one key `targets` with numeric ids or usernames:

```json
{
  "targets": [2118600117]
}
```

Running Postgres for development (Docker) 🐘

Quick one-liner (PowerShell):

```powershell
docker run --name tg-postgres `
  -e POSTGRES_USER=pguser `
  -e POSTGRES_PASSWORD=pgpass `
  -e POSTGRES_DB=tgdata `
  -p 5432:5432 `
  -v pgdata:/var/lib/postgresql/data `
  -d postgres:15
```

Alternatively use the included `docker-compose.yml` and run:

```powershell
docker compose up -d
```

Set the DSN for the current shell session (PowerShell example):

```powershell
$env:PG_DSN = 'postgresql://pguser:pgpass@localhost:5432/tgdata'
```

Running the fetcher (clean run) ▶️

1. Optional: truncate the messages table for a clean test (we provide
   `scripts/clear_messages.py` which ensures the table exists and truncates it):

```powershell
.venv\Scripts\python.exe scripts\clear_messages.py
```

2. Run the fetcher for a target id (write into Postgres):

```powershell
.venv\Scripts\python.exe fetch_messages.py 2118600117 --limit 100 --pg-dsn "postgresql://pguser:pgpass@localhost:5432/tgdata"
```

Inspecting the DB 🛠️
- Quick check helper: `scripts/check_messages.py` prints the row count and a
  sample of the latest rows.
- You can also use `psql` inside the container or any Postgres client.

Type checking ✅
- We use `pyright` for static checks in CI and local verification. Install
  via `python -m pip install --user pyright` or `npm i -g pyright`.
- Running `pyright` in the repo should report no errors with the current
  codebase (some optional warnings may appear for demo scripts).

Helper scripts 🧰
- `scripts/clear_messages.py` — create table (if missing) and truncate messages
- `scripts/check_messages.py` — print row count and sample rows
- `examples/lambda_coroutine_demo.py` — small runnable demo explaining how
  lambdas return coroutine objects and how to await them (useful when
  wiring `store_fn` wrappers)

Testing notes 🧪
- We intentionally avoid downloading media during crawls in the example
  fetcher to reduce rate limits. If you need media, add a dedicated media
  pipeline (download, upload to storage, persist references) and throttle it
  separately.

Migrations and production 🚀
- This repo currently creates the `messages` table on demand. For long-term
  projects, add Alembic migrations, explicit schema versions, and CI tests to
  validate migrations.


If you want me to update the README further (more examples, a troubleshooting
section, or platform-specific instructions), tell me which parts to expand
and I'll patch the file. ✨

If you want, I can implement the SQLite prototype next and wire a small `store_func`
that writes minimal message metadata for benchmarking.