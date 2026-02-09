import json, os
from pathlib import Path

base = Path(__file__).resolve().parent / 'analyzer' / 'runs'

runs = {
    "prod-topics": "Topics",
    "prod-style": "Style",
    "prod-post": "Post",
}

for run_id, label in runs.items():
    run = base / run_id
    if not run.exists():
        print(f"=== {label} ({run_id}) === NOT FOUND\n")
        continue

    print(f"=== {label} ({run_id}) ===")

    # Final output
    final_path = run / 'final.txt'
    post_path = run / 'post.txt'
    out_path = post_path if post_path.exists() else final_path

    if out_path.exists():
        text = open(out_path, encoding='utf-8').read().strip()
        try:
            data = json.loads(text)
            if isinstance(data, list):
                print("Final items:")
                for i, t in enumerate(data[:15], 1):
                    if isinstance(t, dict):
                        print(f"  {i}. {t.get('topic', t)}")
                    else:
                        print(f"  {i}. {t}")
                if len(data) > 15:
                    print(f"  ... and {len(data) - 15} more")
            else:
                print("Final output:")
                print(f"  {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
        except json.JSONDecodeError:
            print("Final text:")
            print(f"  {text[:500]}")
            if len(text) > 500:
                print(f"  ... ({len(text)} chars total)")
    else:
        print("  No output file found")

    # Map batches
    map_path = run / 'map_outputs.jsonl'
    if map_path.exists():
        print("\nMap batches:")
        for line in open(map_path, encoding='utf-8'):
            rec = json.loads(line)
            print(f"  Batch {rec['batch_index']}: {rec['message_count']} msgs, parse_err={rec['parse_error']}")

    # State
    state_path = run / 'state.json'
    if state_path.exists():
        state = json.load(open(state_path, encoding='utf-8'))
        print(f"\nState: phase={state.get('phase')}, reduce_rounds={state.get('reduce_round')}, "
              f"errors={state.get('errors', 0)}")

    # Errors
    err_path = run / 'errors.jsonl'
    if err_path.exists() and os.path.getsize(err_path) > 0:
        print("\nERRORS:")
        for line in open(err_path, encoding='utf-8'):
            print(f"  {json.loads(line)}")
    else:
        print("\nNo errors.")
    print()
