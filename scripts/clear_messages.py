#!/usr/bin/env python3
import asyncio
import os
import asyncpg

async def main():
    dsn = os.getenv('PG_DSN') or 'postgresql://pguser:pgpass@localhost:5432/tgdata'
    print('Using DSN:', dsn)
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS messages (
                id BIGINT PRIMARY KEY,
                date TIMESTAMP WITH TIME ZONE,
                sender_id BIGINT,
                text TEXT,
                has_media BOOLEAN
            )
            '''
        )
        await conn.execute('TRUNCATE TABLE messages;')
        print('Truncated messages table')
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
