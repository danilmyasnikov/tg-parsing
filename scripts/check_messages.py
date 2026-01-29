#!/usr/bin/env python3
import asyncio
import os
import asyncpg

async def main():
    dsn = os.getenv('PG_DSN') or 'postgresql://pguser:pgpass@localhost:5432/tgdata'
    conn = await asyncpg.connect(dsn)
    try:
        r = await conn.fetchrow('SELECT count(*) AS c FROM information_schema.tables WHERE table_schema = ANY (ARRAY[\'public\']) AND table_name = \'messages\'')
        if r is None or r['c'] == 0:
            print('messages table does not exist')
            return
        row = await conn.fetchval('SELECT COUNT(*) FROM messages')
        print('rows in messages:', row)
        sample = await conn.fetch('SELECT id, date, sender_id, has_media FROM messages ORDER BY date DESC LIMIT 3')
        if sample:
            print('latest rows:')
            for s in sample:
                print(s)
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
