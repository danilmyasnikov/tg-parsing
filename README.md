## Architecture Overview 🏗️

This project uses a hybrid approach where your Python application runs on your host machine and connects to a Dockerized Postgres database:

```
┌──────────────────────────────────────────┐
│  Your Windows/Mac machine                │
│                                          │
│  ┌────────────────────────────────┐     │
│  │ Python app runs HERE           │     │
│  │ (fetch_messages.py)            │     │
│  │ Uses: .venv + Python 3.10      │     │
│  └────────────┬───────────────────┘     │
│               │                          │
│               │ connects to              │
│               │ (localhost:5432)         │
│               │                          │
│               ▼                          │
│  ┌────────────────────────────────┐     │
│  │ Docker container               │     │
│  │ postgres:15 (Debian-based)     │     │
│  │ Port: 5432                     │     │
│  └────────────────────────────────┘     │
└──────────────────────────────────────────┘
```

**Why this setup?**
- ✅ Easy Python debugging (runs natively on your machine)
- ✅ Consistent Postgres version across all developers
- ✅ No need to install Postgres system-wide
- ✅ Simple to tear down and recreate the database