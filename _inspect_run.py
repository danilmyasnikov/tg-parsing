import json, sys
from pathlib import Path

base = Path(__file__).resolve().parent / 'analyzer' / 'runs'
run_id = sys.argv[1] if len(sys.argv) > 1 else 'prod-topics'
run = base / run_id

if not run.exists():
    print(f"Run not found: {run}")
    sys.exit(1)

map_path = run / 'map_outputs.jsonl'
if map_path.exists():
    lines = open(map_path, encoding='utf-8').readlines()
    print(f'Map batches: {len(lines)}')
    for l in lines:
        d = json.loads(l)
        print(f"  Batch {d['batch_index']}: {d['message_count']} msgs, "
              f"{d.get('char_count', '?')} chars, tokens~{d.get('token_estimate', '?')}, "
              f"parse_error={d['parse_error']}")

state_path = run / 'state.json'
if state_path.exists():
    print('\nState:')
    print(json.dumps(json.load(open(state_path, encoding='utf-8')), indent=2))

final_path = run / 'final.txt'
if final_path.exists():
    print('\nFinal output:')
    text = open(final_path, encoding='utf-8').read()
    print(text[:2000])
    if len(text) > 2000:
        print(f"... ({len(text)} chars total)")
else:
    print('\nNo final.txt yet')
