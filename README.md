# TG-parsing — Developer README

A small collection of Telethon-based utilities for inspecting dialogs and
fetching channel messages. The project provides a simple developer workflow
and an async Postgres sink for message storage.

## Prerequisites
- Python 3.10+
- Git
- Docker (recommended for local Postgres)

## Quick local setup (PowerShell)

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Credentials (.env)

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

Obtain `TG_API_ID` and `TG_API_HASH` from https://my.telegram.org (API
development tools).

## Repository layout (high level)
- `collector/` — core library used by the CLI and scripts (client, config,
  normalization, streaming, consumer and storage helpers)
- `collect.py` — CLI runner used during development/testing
- `export_targets.py` — export dialog identifiers
- `scripts/` — helper scripts (truncate/inspect DB)

## Config example

`config.json` contains a `targets` array with numeric ids or usernames, e.g.: 

```json
{
  "targets": [2118600117]
}
```

## Running Postgres for development

Use the included `docker-compose.yml` to run a local Postgres instance:

```powershell
docker compose up -d
docker compose logs -f postgres
docker compose down
```

Or run a single container:

```powershell
docker run --name tg-postgres \\
  -e POSTGRES_USER=pguser \\
  -e POSTGRES_PASSWORD=pgpass \\
  -e POSTGRES_DB=tgdata \\
  -p 5432:5432 \\
  -v pgdata:/var/lib/postgresql/data \\
  -d postgres:15
```

Set the DSN for a PowerShell session:

```powershell
$env:PG_DSN = 'postgresql://pguser:pgpass@localhost:5432/tgdata'
```

## Running the fetcher

Optional: truncate the messages table for a clean test:

```powershell
.venv\\Scripts\\python.exe scripts\\clear_messages.py
```

Run the fetcher for a target id:

```powershell
.venv\\Scripts\\python.exe collect.py 2118600117 --limit 100 --pg-dsn "postgresql://pguser:pgpass@localhost:5432/tgdata"
```

## Helper scripts
- `scripts/clear_messages.py` — create table (if missing) and truncate messages
- `scripts/check_messages.py` — print row count and sample rows
- `scripts/print_pg.py` — print a sample of rows from Postgres

## Notes
- The example fetcher avoids downloading media to reduce rate limits. Add a
  separate media pipeline if required.
- For production use, add proper migrations (Alembic), schema versioning, and
  CI validation for migrations.
