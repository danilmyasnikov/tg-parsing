# TODO — prioritized

## Urgent (ASAP)
- [ ] Retrieve all posts using PostgreSQL (migrate from prototype; due 2026-02-30)
	- Goal: reliably iterate channel history and persist every message into Postgres (use migrations, checkpoints, and deduplication).

- [ ] Store posts in PostgreSQL (due 2026-01-30)  
	- Goal: create importable table and persist messages with minimal metadata.

## High priority
- [ ] Implement DB migrations & schema (due 2026-02-01)
- [ ] Integrate storage into main flow

## Medium priority
- [ ] Evaluate and plan migration to OOP design
	- Goal: assess benefits of converting procedural modules into classes (e.g. `Fetcher`, `Store`, `DBPool`) for clearer responsibility boundaries, easier testing, and dependency injection. Provide [...]
- [ ] Add unit tests & CI (due 2026-02-18)
- [ ] Add logging and verbosity option
- [ ] Export targets as structured records (id/username/type/access_hash) — backward-compatible
- [ ] Add progress/ETA display to `fetch_all_messages` (show ETA, respect FloodWait) — Medium priority
- [ ] Implement checkpointing / resume for message fetching
	- Description: Persist the last-processed message id and resume ingestion from that checkpoint. Use DB-driven deduplication (insert-if-not-exists + stop-on-duplicate) and optionally leverage Tele[...]  
 - [ ] Migrate core modules into a `tg_parsing` package
	 - Goal: move application code into `tg_parsing/` (package) to separate app logic from repo metadata and scripts; update imports, CI, and README.
	# 🗂️ TODO — Prioritized

This file groups short-term and long-term work. Tasks are ordered by priority — pick one small item to make progress.

## 🔥 Urgent (ASAP)
- [ ] Retrieve all posts using PostgreSQL (migrate from prototype; due 2026-02-30)
	- Goal: reliably iterate channel history and persist every message into Postgres (use migrations, checkpoints, and deduplication).

- [ ] Store posts in PostgreSQL (due 2026-01-30)
	- Goal: create importable `messages` table and persist messages with minimal metadata.

## ⚠️ High priority
- [ ] Implement DB migrations & schema (due 2026-02-01)
- [ ] Integrate storage into main flow

## 🧭 Medium priority
- [ ] Evaluate and plan migration to OOP design
	- Goal: assess benefits of converting procedural modules into classes (e.g. `Fetcher`, `Store`, `DBPool`) for clearer responsibilities, easier testing, and DI. Produce a phased migration plan.
- [ ] Plan and migrate repository into a `tg_parsing` package (Priority: Medium)
	- Goal: move application code into `tg_parsing/` to separate app logic from repo metadata and scripts; update imports, README and CI. See checklist inside the file for steps.
- [ ] Add unit tests & CI (due 2026-02-18)
- [ ] Add logging and verbosity option
- [ ] Export targets as structured records (id/username/type/access_hash)
- [ ] Add progress/ETA display to `fetch_all_messages` (show ETA, respect FloodWait)
- [ ] Implement checkpointing / resume for message fetching
	- Description: persist last-processed message id and resume ingestion; use DB-driven deduplication and support Telethon `min_id`/`max_id` options. Keep behavior idempotent and add tests.

## 🪛 Low priority / Backlog
- [ ] Exporter improvements (skip-users flag)
- [ ] Backlog: side quests & polish
- [ ] Add linters/formatters: Black / Flake8 / Pylint
- [ ] Fix PowerShell `-Command` quoting when invoking Python scripts (e.g. `clear_messages.py`)
	- Goal: ensure `dev_bootstrap.ps1` and helpers set `PG_DSN` safely (in-process or via `-File`) to avoid parse errors; add a short note/example to README.

- [ ] Optional Dockerization for deployment (Priority: Low)
	- Goal: Add Dockerfile for Python app (optional, for production deployment only). Keep current hybrid setup for development.
	- Add docker-compose.prod.yml with app + db for production
	- Document two modes: local dev (current) vs Docker (production)
	- Rationale: Current hybrid setup (Python on host + Dockerized Postgres) is optimal for active development. Dockerization makes sense later for deployment, CI/CD, or onboarding. Interactive Telegram sessions and debugging are easier with native Python.

## 📦 Planned (Tentative)
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

## ✅ Done
- [x] Prototype SQLite ingestion for testing `fetch_all_messages` (completed 2026-01-29)
	- Goal: local, zero-config store of minimal message metadata for quick benchmarking and debugging.
