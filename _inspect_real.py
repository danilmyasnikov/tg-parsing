import json

# Read and decode final output
with open(r'C:\Users\Danil\Desktop\TG-parsing\analyzer\runs\real-topics-100\final.txt', encoding='utf-8') as f:
    data = json.loads(f.read())

print("=== FINAL TOPICS ===")
for i, topic in enumerate(data, 1):
    print(f"  {i}. {topic}")

# Check map outputs
print("\n=== MAP PHASE ===")
with open(r'C:\Users\Danil\Desktop\TG-parsing\analyzer\runs\real-topics-100\map_outputs.jsonl', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        print(f"  Batch {rec['batch_index']}: {rec['message_count']} msgs, {rec['char_count']} chars, parse_error={rec['parse_error']}")
        if rec.get('result'):
            for item in rec['result'][:3]:
                if isinstance(item, dict):
                    print(f"    - {item.get('topic', '?')} (count~{item.get('count_hint', '?')})")
                else:
                    print(f"    - {item}")
            if len(rec['result']) > 3:
                print(f"    ... and {len(rec['result']) - 3} more")

# Check reduce outputs  
print("\n=== REDUCE PHASE ===")
with open(r'C:\Users\Danil\Desktop\TG-parsing\analyzer\runs\real-topics-100\reduce_outputs.jsonl', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        print(f"  Round {rec['round']}: chunk_size={rec['chunk_size']}")
        if isinstance(rec.get('result'), list):
            for item in rec['result']:
                if isinstance(item, str):
                    print(f"    - {item}")

# Check errors
import os
err_path = r'C:\Users\Danil\Desktop\TG-parsing\analyzer\runs\real-topics-100\errors.jsonl'
if os.path.exists(err_path) and os.path.getsize(err_path) > 0:
    print("\n=== ERRORS ===")
    with open(err_path, encoding='utf-8') as f:
        for line in f:
            print(f"  {json.loads(line)}")
else:
    print("\n=== NO ERRORS ===")
