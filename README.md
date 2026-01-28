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

- Fetch a small number of messages (test/benchmark):

```powershell
python fetch_messages.py 2118600117 --limit 3
```

**Developer notes**

- `parser.fetch_all_messages(client, entity, store_func=None, *, resume_after_id=None, limit=None)`
  provides a streaming, resumable fetch loop and accepts a `store_func(message)`
  callback for persisting messages (useful for SQLite/Postgres backends).
- FloodWaits are handled with exponential backoff in the fetcher; avoid bulk
  media downloads during large crawls to reduce risk of rate limits.

**Next steps & roadmap**

- Prototype SQLite ingestion for `fetch_all_messages` (fast, zero-config test).
- Add progress/ETA instrumentation to the fetcher and then integrate a
  Postgres-backed storage with migrations.

See `TODO.md` for an up-to-date task list and priorities.

**Security & etiquette**

- Keep `.env` and session files out of version control.
- Be mindful of Telegram rate limits and account safety when performing full
  history crawls.

If you want, I can implement the SQLite prototype next and wire a small
`store_func` that writes minimal message metadata for benchmarking.
# TG-parsing

Small Telethon-based utilities to inspect your Telegram dialogs and fetch the latest
message from a channel (supports private channels you are a member of or can join
via invite link).

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

The first run will prompt for the Telegram login code and create a session file
(`session.session` or the `SESSION_NAME` you set). The session file is ignored by
git (`.gitignore` includes `session.*`).

**Config targets**

You can store one or more dialog identifiers in `config.json`. Example:

```json
{
  "targets": [2118600117]
}
```

If you run `fetch_latest.py` without arguments it will use the first entry from
`config.json` (if present). Targets can be numeric dialog ids, usernames, or
invite links.

**Scripts & usage examples**

- List dialogs (shows id, username, title):

```powershell
python list_dialogs.py
```

- Fetch latest message (uses `config.json` or interactive chooser):

```powershell
python fetch_latest.py            # uses config.json first target or prompts
python fetch_latest.py 2118600117 # use numeric id
python fetch_latest.py @mychan    # use username
python fetch_latest.py "https://t.me/joinchat/AAAA..." # invite link
```

The script prints message id, date, sender and text. If the message contains
media it reports that as well (you can extend the script to call
`message.download_media()` to save attachments).


**Notes & security**
- Keep `.env` and `session.*` out of version control (already in `.gitignore`).
- If you regenerate `api_id`/`api_hash` at https://my.telegram.org, update `.env`.
- Private channels must either be in your dialogs (you are a member) or you must
  provide an invite link so the script can join it.

If you want, I can add automatic media download, text cleaning (strip Markdown),
or support multiple targets from `config.json` in a single run.