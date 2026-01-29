# TG-parsing

Small Telethon-based utilities to inspect your Telegram dialogs and fetch messages.
This repository was refactored into small modules (typed for Python 3.10+) and
includes non-interactive, config-driven scripts for exporting targets and
fetching messages.
**Quick start (PowerShell)**

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
**Credentials (.env)**

Create a `.env` file in the project root with your credentials (do NOT commit it):

```
TG_API_ID=123456
TG_API_HASH=your_api_hash_here
# Optional: phone to avoid retyping each run
TG_PHONE=+7999xxxxxxx
# Optional: session name
SESSION_NAME=session
```
On first run the scripts will create a session file (`session.session` by default).
Session files and `.env` are ignored by git.

**Project layout**

- `config.py`: load runtime config and credentials.
- `client.py`: async Telethon client context manager.
- `annotations.py`: shared typing aliases used across modules.
- `resolver.py`: resolve a CLI target (id/username) to a Telethon entity.
- `parser.py`: message fetching helpers; includes `fetch_all_messages` (streaming,
  resumable) and `fetch_latest_message`.
- `storage.py`: small helpers for displaying/storing messages (used by examples).
- `export_targets.py`: exports dialog identifiers to `exported_config.json`.
- `fetch_latest.py`: fetch the latest message for a single target (non-interactive).
- `fetch_messages.py`: small runner to fetch N messages (useful for testing/bench).

**Config targets**

You can store one or more dialog identifiers in `config.json`. Example:

```json
{
  "targets": [2118600117]
}
```

By design the CLI is non-interactive: pass a target on the command line or put
it into `config.json`. Invite-link *joining* was removed to avoid surprises —
private channels must already be present in your dialogs (you are a member).

**Usage examples**

- Export dialogs to JSON (creates `exported_config.json`):

```powershell
python export_targets.py
```

- Fetch the latest message for a target:

```powershell
python fetch_latest.py 2118600117
python fetch_latest.py @mychannel
```

# TG-parsing

Small Telethon-based utilities to inspect your Telegram dialogs and fetch messages.
This project was refactored into small, typed modules (Python 3.10+).

## Quick start (PowerShell)

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Credentials (.env)

Create a `.env` file in the project root with your credentials (do NOT commit it):

```
TG_API_ID=123456
TG_API_HASH=your_api_hash_here
# Optional: phone to avoid retyping each run
TG_PHONE=+7999xxxxxxx
# Optional: session name
SESSION_NAME=session
```

On first run the scripts will create a session file (ignored by git).

## Project layout

- `config.py`: load runtime config and credentials
- `client.py`: async Telethon client context manager
- `resolver.py`: resolve CLI targets (id/username/invite link)
- `parser.py`: parsing helpers; includes `iter_messages_from_entity` (async generator)
- `fetcher.py`: drains parser output and calls a `store_func` for each message
- `storage.py`: default console `store_func` (`print_store`) and storage helpers
- `export_targets.py`: export dialog identifiers to `exported_config.json`
- `fetch_messages.py`: small runner to fetch N messages (useful for testing/bench)

See the source files for full behavior and available helpers.

## Usage examples

- Export dialogs to JSON (creates `exported_config.json`):

```powershell
python export_targets.py
```

- Fetch a small number of messages (test/benchmark):

```powershell
python fetch_messages.py 2118600117 --limit 3
```

## Postgres (Docker) — Quick dev setup

For development we recommend running Postgres in Docker. This is fast to start,
reproducible and isolates the database from your host environment.

1. Start Postgres (one-liner, PowerShell):

```powershell
docker run --name tg-postgres `
  -e POSTGRES_USER=pguser `
  -e POSTGRES_PASSWORD=pgpass `
  -e POSTGRES_DB=tgdata `
  -p 5432:5432 `
  -v pgdata:/var/lib/postgresql/data `
  -d postgres:15
```

2. Set the DSN for this session (PowerShell):

```powershell
$env:PG_DSN = 'postgresql://pguser:pgpass@localhost:5432/tgdata'
```

3. Run the fetcher and write messages to Postgres (example):

```powershell
.venv\Scripts\python fetch_messages.py 2118600117 --limit 100 --pg-dsn "postgresql://pguser:pgpass@localhost:5432/tgdata"
```

4. Verify rows (inside container using `psql`):

```bash
docker exec -it tg-postgres psql -U pguser -d tgdata -c "SELECT id,date,sender_id,text,has_media FROM messages LIMIT 10;"
```

Or use the provided Python inspector (from the repo venv):

```powershell
.venv\Scripts\python scripts/print_pg.py "postgresql://pguser:pgpass@localhost:5432/tgdata"
```

Notes
- The `-v pgdata:/var/lib/postgresql/data` option creates a named volume so data
  persists across container restarts.
- Use a real password for anything outside local testing; percent-encode special
  characters when embedding them in the DSN.
- For production use a managed Postgres provider and add migrations (Alembic).

Optional: `docker-compose.yml`

```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: pguser
      POSTGRES_PASSWORD: pgpass
      POSTGRES_DB: tgdata
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

Start with:

```bash
docker compose up -d
```

## Developer notes

- `parser.iter_messages_from_entity(client, entity, *, resume_after_id=None, limit=None)`
  yields `Message` objects asynchronously and is resilient to resend/duplicate events.
- `fetcher.fetch_all_messages(client, entity, store_func, *, resume_after_id=None, limit=None)`
  consumes the generator and calls `await store_func(message)` for each item.
- `storage.print_store(message)` is the built-in console sink used by examples.
- Checkpointing / resume: the fetcher accepts a resume parameter and the
  project plans persistent checkpoints (see `TODO.md`) so a future `store_func`
  can persist the last-processed message id and resume later.

FloodWaits are handled with backoff in the fetcher; avoid bulk media downloads
during large crawls to reduce rate-limit exposure.

## Next steps & roadmap

- Prototype SQLite ingestion for `fetcher.fetch_all_messages` (fast, zero-config)
- Add progress/ETA instrumentation and integrate Postgres-backed storage with migrations

See `TODO.md` for the up-to-date task list and priorities.

## Security & etiquette

- Keep `.env` and session files out of version control.
- Respect Telegram rate limits and account safety when crawling large histories.

If you want, I can implement the SQLite prototype next and wire a small `store_func`
that writes minimal message metadata for benchmarking.