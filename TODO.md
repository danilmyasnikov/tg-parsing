# TODO — prioritized

## Urgent (ASAP)
- [ ] Prototype SQLite ingestion for testing `fetch_all_messages` (due 2026-01-29)
 	- Goal: local, zero-config store of minimal message metadata and metrics for quick benchmarking and debugging.

- [ ] Retrieve all posts (postponed until SQLite prototype) (due 2026-02-30)
 	- Goal: reliably iterate channel history and export every message (run after SQLite prototype).

- [ ] Store posts in PostgreSQL (due 2026-01-30)  
 	- Goal: create importable table and persist messages with minimal metadata.

## High priority
- [ ] Implement DB migrations & schema (due 2026-02-01)
- [ ] Integrate storage into main flow

## Medium priority
- [ ] Add unit tests & CI (due 2026-02-18)
- [ ] Add logging and verbosity option
- [ ] Export targets as structured records (id/username/type/access_hash) — backward-compatible
- [ ] Add progress/ETA display to `fetch_all_messages` (show ETA, respect FloodWait) — Medium priority

## Low priority / Backlog
- [ ] Exporter improvements (skip-users flag)
- [ ] Backlog: side quests & polish