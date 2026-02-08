import json, os

run = r'C:\Users\Danil\Desktop\TG-parsing\analyzer\runs\real-style-100'
final_path = os.path.join(run, 'final.txt')
map_path = os.path.join(run, 'map_outputs.jsonl')

if os.path.exists(final_path):
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
