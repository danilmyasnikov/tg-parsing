# TODO — prioritized

This file groups short-term and long-term work. Tasks are ordered by priority — pick one small item to make progress.

## Urgent (ASAP)
 - [ ] Retrieve all posts using PostgreSQL (migrate from prototype; due 2026-02-30)
  - Goal: reliably iterate channel history and persist every message into Postgres (use migrations, checkpoints, and deduplication).
 - [ ] Create `vibecoding` branch and scaffold (due 2026-02-05)
   - Goal: create a feature branch named `vibecoding`, add an initial module/package skeleton, and push the branch to `origin` so work can proceed in isolation.

- ## High priority
- [ ] Implement DB migrations & schema (due 2026-02-01)
- [ ] Handle Docker Engine not started in `dev_bootstrap` (scripts/dev_bootstrap.ps1)
   - Goal: detect when Docker Engine/Daemon isn't running and either attempt to
     start Docker Desktop automatically (Windows) or show a clear, actionable
     message with instructions to start Docker. This should reduce confusing
     bootstrap failures; prefer an automatic start where safe, otherwise fail
     fast with guidance. Priority: **High**.

## Medium priority
- [ ] Evaluate and plan migration to OOP design
  - Goal: assess benefits of converting procedural modules into classes (`Fetcher`, `Store`, `DBPool`) for clearer responsibilities, easier testing, and DI; produce a phased migration plan.
- [ ] Add unit tests & CI (due 2026-02-18)
- [ ] Add logging and verbosity option
- [ ] Export targets as structured records (id/username/type/access_hash)
- [ ] Add progress/ETA display to `fetch_all_messages` (show ETA, respect FloodWait)
   - Recommendation: consider using `tqdm` for local CLI progress bars — it's lightweight,
     well-maintained, and easy to integrate by updating a counter as messages are processed.
     For async flows you can call `tqdm.update()` from the consumer or use manual wrappers;
     for long-running/background ingestion prefer metrics/logging (Prometheus) rather than
     a transient progress bar. Ensure the progress display accounts for `FloodWait` sleeps.
- [ ] Implement checkpointing / resume for message fetching
  - Description: persist last-processed message id and resume ingestion; use DB-driven deduplication and support Telethon `min_id`/`max_id`. Keep behavior idempotent and add tests.
- [ ] Telethon connectivity troubleshooting (priority: Medium)
   - Short: document transient connection fixes and mitigations.
   - Quick fixes: retry/backoff around `client.start()`, increase Telethon timeouts/retries, use a SOCKS/HTTP proxy if required by your network, and catch `FloodWaitError` to sleep when rate-limited.
   - Rationale: transient network or regional blocks can cause `TimeoutError` or repeated connection failures that block fetches; add notes and small code patterns in `collector/client.py`.
 

## Low priority / Backlog
- [ ] Exporter improvements (skip-users flag)
- [ ] Add linters/formatters: Black / Flake8 / Pylint
- [ ] Fix PowerShell `-Command` quoting when invoking Python scripts (e.g. `clear_messages.py`)
  - Goal: ensure `dev_bootstrap.ps1` and helpers set `PG_DSN` safely (in-process or via `-File`) to avoid parse errors; add a short note/example to README.
- [ ] Optional Dockerization for deployment (Priority: Low)
  - Goal: Add Dockerfile for the Python app (production) and a `docker-compose.prod.yml` for app+db; document local dev vs Docker production modes.

## Planned (Tentative)
- [ ] Scaffold Alembic (init)
- [ ] Define production `messages` schema (entity_id, id, date, sender_id, text, raw JSONB, media_meta, content_hash)
- [ ] Create initial Alembic migration
- [ ] Polish Docker & Postgres dev setup (healthchecks, backups, CI integration)
- [ ] Implement DB-backed checkpoints & resume logic
- [ ] Implement idempotent upsert/dedup in fetch pipeline
- [ ] Add media pipeline (S3/local) and store media metadata
- [ ] Add backup & restore scripts and docs
- [ ] Add indexes, partitioning and migration plan for large tables
- [ ] Add monitoring, healthchecks and metrics (Prometheus)
- [ ] Add CI workflow for migrations and tests
- [ ] Add integration tests using `docker-compose` and a test DB
- [ ] Add export tools: JSONL and Parquet exporters
- [ ] Privacy / PII audit and redaction tooling
- [ ] Performance and load testing harness

## Done
- [x] Prototype SQLite ingestion for testing `fetch_all_messages` (completed 2026-01-29)
  - Goal: local, zero-config store of minimal message metadata for quick benchmarking and debugging.
- [x] Migrate core modules into a `tg_parsing` package
  - Goal: move application code into `tg_parsing/` to separate app logic from repo metadata and scripts; update imports, README, and CI.
 - [x] Implemented DB schema for `messages` (composite PK and TEXT sender_id)
   - Note: `scripts/clear_messages.py` recreates the table for local dev.
 - [x] Store posts in PostgreSQL (ingestion pipeline persisted messages)
 - [x] Integrated storage into main flow (consumer now normalizes messages and writes to Postgres)
