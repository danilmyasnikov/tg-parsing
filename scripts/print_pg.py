import asyncio, asyncpg, os, sys


async def main(dsn: str | None = None):
    if dsn is None:
        dsn = os.getenv('PG_DSN')
    if not dsn:
        raise RuntimeError('PG_DSN not set (pass as first arg or set PG_DSN env)')
    conn = await asyncpg.connect(dsn)
    rows = await conn.fetch('SELECT COUNT(*) as c FROM messages')
    print('rows in messages:', rows[0]['c'])
    sample = await conn.fetch('SELECT id,date,sender_id,text,has_media FROM messages ORDER BY date DESC LIMIT 3')
    print('latest 3 rows:')
    for r in reversed(sample):
        print(r)
    await conn.close()

if __name__ == '__main__':
    dsn_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(dsn_arg))
