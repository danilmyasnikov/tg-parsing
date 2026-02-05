# Project TODO — cross-cutting

This TODO contains items that apply to the whole repository and not only
the `collector` implementation. Keep these high-level, assignable tasks and
move implementation detail into per-package TODOs (e.g. `collector/TODO.md`).

## High priority
- [ ] Add unit tests & CI (due 2026-02-18)
- [ ] Add logging and verbosity option (apply across packages)
- [ ] Add linters/formatters: Black / Flake8 / Pylint
- [ ] Optional: Dockerization for production (Dockerfile + compose.prod.yml)

- [ ] Create `vibecoding` branch and scaffold (due 2026-02-05)  
	- Goal: create a feature branch named `vibecoding`, add an initial module/package skeleton, and push the branch to `origin` so work can proceed in isolation.  

- [ ] Handle Docker Engine not started in `dev_bootstrap` (scripts/dev_bootstrap.ps1)  
	- Goal: detect when Docker Engine/Daemon isn't running and either attempt to start Docker Desktop automatically (Windows) or show a clear, actionable message with instructions to start Docker. Prefer an automatic start where safe, otherwise fail fast with guidance.


## Infrastructure & schema
- [ ] Scaffold Alembic (init)
- [ ] Define production `messages` schema (entity_id, id, date, sender_id, text, raw JSONB, media_meta, content_hash)
- [ ] Create initial Alembic migration
- [ ] Polish Docker & Postgres dev setup (healthchecks, backups, CI integration)
- [ ] Add backup & restore scripts and docs
- [ ] Add indexes, partitioning and migration plan for large tables

## CI / testing / monitoring
- [ ] Add CI workflow for migrations and tests
- [ ] Add integration tests using `docker-compose` and a test DB
- [ ] Add monitoring, healthchecks and metrics (Prometheus)
- [ ] Performance and load testing harness

## Data & product features
- [ ] Add media pipeline (S3/local) and store media metadata
- [ ] Add export tools: JSONL and Parquet exporters
- [ ] Privacy / PII audit and redaction tooling

## Developer experience
- [ ] Detect Docker Engine not running in `dev_bootstrap` and show clear guidance

- [ ] Fix PowerShell `-Command` quoting when invoking Python scripts (e.g. `clear_messages.py`)  
	- Goal: ensure `dev_bootstrap.ps1` and helpers set `PG_DSN` safely (in-process or via `-File`) to avoid parse errors; add a short note/example to README.

---
Keep this file focused on cross-cutting work. Move collector-specific
implementation tasks into `collector/TODO.md` and create `analyzer/TODO.md`
and `generator/TODO.md` when those packages need their own implementation lists.
