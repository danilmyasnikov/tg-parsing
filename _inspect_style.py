import json, os
from pathlib import Path

run = Path(__file__).resolve().parent / 'analyzer' / 'runs' / 'prod-style'
final_path = run / 'final.txt'
map_path = run / 'map_outputs.jsonl'

if final_path.exists():
    print('=== FINAL STYLE ===')
    print(open(final_path, encoding='utf-8').read())
    print()
    print('=== MAP BATCHES ===')
    for line in open(map_path, encoding='utf-8'):
        rec = json.loads(line)
        bi = rec['batch_index']
        mc = rec['message_count']
        pe = rec['parse_error']
        print(f'  Batch {bi}: {mc} msgs, parse_err={pe}')
        if rec.get('result'):
            print(f'    {json.dumps(rec["result"], ensure_ascii=False)[:300]}')
else:
    print('Run not found or not complete yet')
    print(f'Looked in: {run}')
