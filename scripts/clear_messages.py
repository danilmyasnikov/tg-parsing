#!/usr/bin/env python3
import asyncio
import os
import sys
import asyncpg

async def main():
    dsn = os.getenv('PG_DSN') or 'postgresql://pguser:pgpass@localhost:5432/tgdata'
    print('Using DSN:', dsn)
    conn = await asyncpg.connect(dsn)
    try:
        # Ensure table schema matches the storage implementation in
        # `collector/storage/postgres_store.py` which uses a composite
        # primary key (sender_id, id) and stores `sender_id` as TEXT.
        await conn.execute('DROP TABLE IF EXISTS messages;')
        await conn.execute(
            '''
            CREATE TABLE messages (
                sender_id TEXT,
                id BIGINT,
                date TIMESTAMP WITH TIME ZONE,
                text TEXT,
                has_media BOOLEAN,
                PRIMARY KEY (sender_id, id)
            )
            '''
        )
        # Verify the table is empty after truncate. If it's not, exit non-zero.
        row_count = await conn.fetchval('SELECT COUNT(*) FROM messages')
        if row_count != 0:
            print(f'ERROR: messages table not empty after TRUNCATE, row_count={row_count}')
            sys.exit(1)
        print('Truncated messages table')
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
