import json

lines = open(r'C:\Users\Danil\Desktop\TG-parsing\analyzer\runs\test-mock-100\map_outputs.jsonl').readlines()
print(f'Map batches: {len(lines)}')
for l in lines:
    d = json.loads(l)
    print(f"  Batch {d['batch_index']}: {d['message_count']} msgs, {d['char_count']} chars, tokens~{d['token_estimate']}, parse_error={d['parse_error']}")

print()
print("State:")
print(json.dumps(json.load(open(r'C:\Users\Danil\Desktop\TG-parsing\analyzer\runs\test-mock-100\state.json')), indent=2))

print()
print("Final output:")
print(open(r'C:\Users\Danil\Desktop\TG-parsing\analyzer\runs\test-mock-100\final.txt').read())
