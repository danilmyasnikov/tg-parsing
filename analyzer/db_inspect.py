"""Inspect the Postgres `messages` table: count and sample rows."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import asyncpg


def get_dsn() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")
    return os.getenv("PG_DSN") or "postgresql://pguser:pgpass@localhost:5432/tgdata"


async def inspect(pg_dsn: str) -> None:
    try:
        conn = await asyncpg.connect(pg_dsn)
    except Exception as e:
        print(f"ERROR connecting to Postgres: {e}")
        return

    try:
        cnt = await conn.fetchval("SELECT count(*) FROM messages")
        print(f"messages table row count: {cnt}")

        rows = await conn.fetch(
            "SELECT sender_id, id, date, text FROM messages ORDER BY date DESC LIMIT 10"
        )
        if not rows:
            print("No recent rows returned (table empty or no rows matching query).")
        else:
            print("Recent rows (most recent first):")
            for r in rows:
                d: dict[str, Any] = dict(r)
                text_preview = (d.get("text") or "").replace("\n", " ")
                if len(text_preview) > 200:
                    text_preview = text_preview[:200] + "…"
                print(f"- sender_id={d.get('sender_id')} id={d.get('id')} date={d.get('date')} text_present={bool(d.get('text'))} text_preview={text_preview}")

        # Now run the same filtered query that the analyzer uses to see if
        # the date cutoff filters out rows unexpectedly.
        from datetime import datetime, timedelta, timezone

        since = datetime.now(timezone.utc) - timedelta(days=1)
        filtered_query = (
            "SELECT sender_id, id, date, text FROM messages WHERE date >= $1 ORDER BY date DESC LIMIT $2"
        )
        filtered_rows = await conn.fetch(filtered_query, since, 10)
        print(f"\nFiltered query returned {len(filtered_rows)} rows (since={since.isoformat()})")

    except asyncpg.exceptions.UndefinedTableError:
        print("Table `messages` does not exist in the database.")
    except Exception as e:
        print(f"ERROR querying messages table: {e}")
    finally:
        await conn.close()


def main() -> None:
    pg_dsn = get_dsn()
    asyncio.run(inspect(pg_dsn))


if __name__ == "__main__":
    main()
