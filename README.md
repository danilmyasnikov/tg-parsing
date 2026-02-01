# TG-parsing — Developer README

This repository contains small Telethon-based utilities for inspecting dialogs
and fetching channel messages. The codebase is intentionally minimal and
focused on a reproducible developer workflow with an async Postgres sink for
message storage.

## Prerequisites 🚧
 - Python 3.10+ (project uses PEP-604 `X | None` annotations)
 - Git
 - Docker (recommended for Postgres local dev)

## Quick local setup (PowerShell) ⚙️

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Credentials (.env) 🔐

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

Obtain `TG_API_ID` and `TG_API_HASH` from https://my.telegram.org (open "API development tools" and create a new application to receive your credentials).

On first run a Telethon session file will be created (ignored by git).

## Repository layout (high level)
 - `config.py` — load `config.json` and environment credentials
 - `client.py` — async Telethon client context manager
 - `type_annotations.py` — type aliases used for editor/type-checker convenience
 - `entity_resolver.py` — resolve CLI `target` to a Telethon entity
 - `stream.py` — async message iterators (resumable)
 - `consumer.py` — consumes `stream` and calls a `store_func` for each message
 - `storage/` — storage package exposing `print_store`, `postgres_store` and pool helpers
 - `export_targets.py` — exports dialog identifiers
-- `collect.py` — CLI runner used during development/testing
 - `scripts/` — helper scripts (truncate/inspect DB)

## Config example

`config.json` contains one key `targets` with numeric ids or usernames:

```json
{
  "targets": [2118600117]
}
```

## Running Postgres for development (Docker) 🐘

Recommended: use the included `docker-compose.yml` for a reproducible local Postgres service.

Advantages:
- single command setup for all developers
- managed volumes and networking in the compose file
- easy to view logs, restart, and teardown without retyping options

Quick start (PowerShell):

```powershell
# Start Postgres in detached mode (recommended)
docker compose up -d

# Follow Postgres logs
docker compose logs -f postgres

# Stop services (preserves volumes):
docker compose down

# Stop and remove volumes (start fresh):
docker compose down -v
```

Notes:
- Use `docker compose` (built-in plugin) rather than the old `docker-compose` binary on modern Docker engines.
- The compose file in this repository defines the `postgres` service and a named volume for persistent data.

Fallback (single-container one-liner):

```powershell
docker run --name tg-postgres `
  -e POSTGRES_USER=pguser `
  -e POSTGRES_PASSWORD=pgpass `
  -e POSTGRES_DB=tgdata `
  -p 5432:5432 `
  -v pgdata:/var/lib/postgresql/data `
  -d postgres:15
```

Set the DSN for the current shell session (PowerShell example):

```powershell
$env:PG_DSN = 'postgresql://pguser:pgpass@localhost:5432/tgdata'
```

## Architecture Overview 🏗️

This project uses a hybrid approach where your Python application runs on your host machine and connects to a Dockerized Postgres database:

```
┌──────────────────────────────────────────┐
│  Your Windows/Mac machine                │
│                                          │
│  ┌────────────────────────────────┐      │
│  │ Python app runs HERE           │      │
│  │ (collect.py)                   │      |
│  │ Uses: .venv + Python 3.10      │      │
│  └────────────┬───────────────────┘      │
│               │                          │
│               │ connects to              │
│               │ (localhost:5432)         │
│               │                          │
│               ▼                          │
│  ┌────────────────────────────────┐      │
│  │ Docker container               │      │
│  │ postgres:15 (Debian-based)     │      │
│  │ Port: 5432                     │      │
│  └────────────────────────────────┘      │
└──────────────────────────────────────────┘
```

**Why this setup?**
- ✅ Easy Python debugging (runs natively on your machine)
- ✅ Consistent Postgres version across all developers
- ✅ No need to install Postgres system-wide
- ✅ Simple to tear down and recreate the database

## Running the fetcher (clean run) ▶️

1. Optional: truncate the messages table for a clean test (we provide
   `scripts/clear_messages.py` which ensures the table exists and truncates it):

```powershell
.venv\Scripts\python.exe scripts\clear_messages.py
```

2. Run the fetcher for a target id (write into Postgres):

```powershell
.venv\Scripts\python.exe collect.py 2118600117 --limit 100 --pg-dsn "postgresql://pguser:pgpass@localhost:5432/tgdata"
```

## Inspecting the DB 🛠️
- Quick check helper: `scripts/check_messages.py` prints the row count and a
  sample of the latest rows.
- You can also use `psql` inside the container or any Postgres client.


## Helper scripts 🧰
 - `scripts/clear_messages.py` — create table (if missing) and truncate messages
 - `scripts/check_messages.py` — print row count and sample rows
 - `scripts/print_pg.py` — print a sample of rows from Postgres for verification

## Testing notes 🧪
- We intentionally avoid downloading media during crawls in the example
  fetcher to reduce rate limits. If you need media, add a dedicated media
  pipeline (download, upload to storage, persist references) and throttle it
  separately.

## Migrations and production 🚀
- This repo currently creates the `messages` table on demand. For long-term
  projects, add Alembic migrations, explicit schema versions, and CI tests to
  validate migrations.

If you want me to update the README further (more examples, a troubleshooting
section, or platform-specific instructions), tell me which parts to expand
and I'll patch the file. ✨