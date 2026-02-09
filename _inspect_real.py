import json, os
from pathlib import Path

base = Path(__file__).resolve().parent / 'analyzer' / 'runs'
run_id = 'prod-topics'
run = base / run_id

# Read and decode final output
final_path = run / 'final.txt'
if not final_path.exists():
    print(f"Run not found: {run}")
    exit(1)

with open(final_path, encoding='utf-8') as f:
    raw = f.read().strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = raw

print("=== FINAL TOPICS ===")
if isinstance(data, list):
    for i, topic in enumerate(data, 1):
        if isinstance(topic, dict):
            print(f"  {i}. {topic.get('topic', '?')} (count~{topic.get('count_hint', '?')})")
        else:
            print(f"  {i}. {topic}")
else:
    print(data[:1000])

# Check map outputs
map_path = run / 'map_outputs.jsonl'
if map_path.exists():
    print("\n=== MAP PHASE ===")
    with open(map_path, encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            print(f"  Batch {rec['batch_index']}: {rec['message_count']} msgs, "
                  f"{rec.get('char_count', '?')} chars, parse_error={rec['parse_error']}")
            if rec.get('result') and isinstance(rec['result'], list):
                for item in rec['result'][:3]:
                    if isinstance(item, dict):
                        print(f"    - {item.get('topic', '?')} (count~{item.get('count_hint', '?')})")
                    else:
                        print(f"    - {item}")
                if len(rec['result']) > 3:
                    print(f"    ... and {len(rec['result']) - 3} more")

# Check reduce outputs
reduce_path = run / 'reduce_outputs.jsonl'
if reduce_path.exists():
    print("\n=== REDUCE PHASE ===")
    with open(reduce_path, encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            print(f"  Round {rec['round']}: chunk_size={rec['chunk_size']}")

# Check errors
err_path = run / 'errors.jsonl'
if err_path.exists() and os.path.getsize(err_path) > 0:
    print("\n=== ERRORS ===")
    with open(err_path, encoding='utf-8') as f:
        for line in f:
            print(f"  {json.loads(line)}")
else:
    print("\n=== NO ERRORS ===")
