import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://pguser:pgpass@localhost:5432/tgdata')
    count = await conn.fetchval('SELECT COUNT(*) FROM messages')
    print(f'Total messages: {count}')
    
    # Check date range
    date_range = await conn.fetchrow(
        'SELECT MIN(date) as earliest, MAX(date) as latest FROM messages'
    )
    print(f'Date range: {date_range["earliest"]} to {date_range["latest"]}')
    
    # Sample messages
    sample = await conn.fetch(
        'SELECT sender_id, id, date, LEFT(text, 80) as text_preview FROM messages ORDER BY date DESC LIMIT 5'
    )
    for r in sample:
        print(dict(r))
    
    # Check distinct senders
    senders = await conn.fetch(
        'SELECT sender_id, COUNT(*) as cnt FROM messages GROUP BY sender_id ORDER BY cnt DESC LIMIT 10'
    )
    print('\nSenders:')
    for s in senders:
        print(f'  {s["sender_id"]}: {s["cnt"]} messages')
    
    await conn.close()

asyncio.run(main())
