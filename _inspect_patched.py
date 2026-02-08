import json, os

runs = {
    "patched-topics-100": "Patched Topics",
}

for run_id, label in runs.items():
    run = os.path.join(r'C:\Users\Danil\Desktop\TG-parsing\analyzer\runs', run_id)
    print(f"=== {label} ({run_id}) ===")
    
    # Final output
    final = open(os.path.join(run, 'final.txt'), encoding='utf-8').read()
    data = json.loads(final)
    print("Final topics:")
    for i, t in enumerate(data, 1):
        print(f"  {i}. {t}")
    
    # Map batches
    print("\nMap batches:")
    for line in open(os.path.join(run, 'map_outputs.jsonl'), encoding='utf-8'):
        rec = json.loads(line)
        print(f"  Batch {rec['batch_index']}: {rec['message_count']} msgs, parse_err={rec['parse_error']}")
        if rec.get('result'):
            for item in rec['result'][:4]:
                if isinstance(item, dict):
                    print(f"    - {item.get('topic', '?')} (count~{item.get('count_hint', '?')})")
    
    # Reduce rounds
    print("\nReduce rounds:")
    for line in open(os.path.join(run, 'reduce_outputs.jsonl'), encoding='utf-8'):
        rec = json.loads(line)
        print(f"  Round {rec['round']}: chunk_size={rec['chunk_size']}")
    
    # State
    state = json.load(open(os.path.join(run, 'state.json'), encoding='utf-8'))
    print(f"\nFinal state: phase={state.get('phase')}, reduce_rounds={state.get('reduce_round')}, chunks={state.get('chunks_in_round')}")
    
    # Errors
    err_path = os.path.join(run, 'errors.jsonl')
    if os.path.exists(err_path) and os.path.getsize(err_path) > 0:
        print("\nERRORS:")
        for line in open(err_path, encoding='utf-8'):
            print(f"  {json.loads(line)}")
    else:
        print("\nNo errors.")
    print()
