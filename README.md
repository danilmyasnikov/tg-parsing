# TG-parsing

Simple Telethon-based project to fetch messages from a (private) Telegram channel.

Quick start (PowerShell):

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# set env vars or create a .env with TG_API_ID and TG_API_HASH
python fetch_telegram.py "https://t.me/joinchat/AAAA..." --limit 200
```

Files to edit:
- `fetch_telegram.py` — script to fetch messages
- `.gitignore` — already created
- `requirements.txt` — already created

Note: don't commit `.venv` or session files (they're in `.gitignore`).
