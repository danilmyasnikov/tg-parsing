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
- [ ] Evaluate and plan migration to OOP design (Priority: Medium)
	- Goal: assess benefits of converting procedural modules into classes (e.g. `Fetcher`, `Store`, `DBPool`) for clearer responsibility boundaries, easier testing, and dependency injection. Provide a migration plan with phases and estimated effort.
- [ ] Add unit tests & CI (due 2026-02-18)
- [ ] Add logging and verbosity option
- [ ] Export targets as structured records (id/username/type/access_hash) — backward-compatible
- [ ] Add progress/ETA display to `fetch_all_messages` (show ETA, respect FloodWait) — Medium priority
- [ ] Implement checkpointing / resume for message fetching (Priority: Medium)
	- Description: Persist the last-processed message id and resume ingestion from that checkpoint. Use DB-driven deduplication (insert-if-not-exists + stop-on-duplicate) and optionally leverage Telethon `min_id`/`max_id` to limit API work. Keep behavior idempotent; handle FloodWait errors; add tests and README example.

## Low priority / Backlog
- [ ] Exporter improvements (skip-users flag)
- [ ] Backlog: side quests & polish
- [ ] Add linters/formatters: Black/Flake8/Pylint

- [ ] Fix PowerShell `-Command` quoting when invoking Python scripts (e.g. `clear_messages.py`) — Priority: Low
	- Goal: ensure `dev_bootstrap.ps1` and any helper invocations set `PG_DSN` safely (in-process or via `-File`) to avoid parse errors; add a short note/example to README.

## Planned (Tentative)
- [ ] Scaffold Alembic (init)
- [ ] Define `messages` schema (entity_id, id, date, sender_id, text, raw JSONB, media_meta, content_hash)
- [ ] Create initial Alembic migration
- [ ] Polish Docker & Postgres dev setup (refactor `docker-compose.yml`, add healthchecks, backups/docs, CI integration)
- [ ] Implement DB-backed checkpoints & resume logic
- [ ] Implement idempotent upsert/dedup in `fetcher.py`
- [ ] Add media pipeline (S3/local) and store media metadata
- [ ] Add backup & restore scripts and docs
- [ ] Add indexes, partitioning and migration plan for large tables
- [ ] Add monitoring, healthchecks and metrics (Prometheus/ops)
- [ ] Add CI workflow for migrations and tests
- [ ] Add integration tests using `docker-compose` and test DB
- [ ] Add export tools: JSONL and Parquet exporters
- [ ] Privacy / PII audit and redaction tooling
- [ ] Performance and load testing harness

## Done
- [x] Prototype SQLite ingestion for testing `fetch_all_messages` (completed 2026-01-29)  
	- Goal: local, zero-config store of minimal message metadata and metrics for quick benchmarking and debugging.