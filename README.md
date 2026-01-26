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