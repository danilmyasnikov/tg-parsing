"""
End-to-end pipeline test for all analyzer jobs using mock mode.
Tests 100 messages from the Docker DB through the full map-reduce pipeline.
"""
import asyncio
import json
import os
import sys
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

os.environ["ANALYZER_MOCK"] = "1"

from analyzer.batch_runner import RunConfig, run_map_reduce

PG_DSN = "postgresql://pguser:pgpass@localhost:5432/tgdata"

JOBS = [
    {
        "name": "topics",
        "job": "topics",
        "run_id": "e2e-topics",
        "prompt_override": None,
    },
    {
        "name": "style",
        "job": "style",
        "run_id": "e2e-style",
        "prompt_override": None,
    },
    {
        "name": "custom",
        "job": "custom",
        "run_id": "e2e-custom",
        "prompt_override": "Составь список всех упомянутых финансовых инструментов. Ответ в JSON.",
    },
]


async def test_job(job_spec: dict) -> dict:
    run_id = job_spec["run_id"]
    run_dir = Path(__file__).resolve().parent / "analyzer" / "runs" / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)

    config = RunConfig(
        pg_dsn=PG_DSN,
        job=job_spec["job"],
        sender_id=None,
        days_back=0,
        page_size=2000,
        max_messages=100,
        max_message_chars=400,
        max_batch_chars=15000,
        max_batch_tokens=4000,
        model_name="gemini-3-flash-preview",
        system_instruction=None,
        request_interval_s=0.0,
        timeout_s=30.0,
        max_requests=None,
        run_id=run_id,
        prompt_override=job_spec["prompt_override"],
    )

    result = await run_map_reduce(config, resume=False, phase="all")
    
    # Validate artifacts
    assert (run_dir / "config.json").exists(), f"{run_id}: missing config.json"
    assert (run_dir / "state.json").exists(), f"{run_id}: missing state.json"
    assert (run_dir / "map_outputs.jsonl").exists(), f"{run_id}: missing map_outputs.jsonl"
    assert (run_dir / "final.txt").exists(), f"{run_id}: missing final.txt"
    
    # Check map outputs
    map_records = []
    with open(run_dir / "map_outputs.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                map_records.append(json.loads(line))
    
    total_msgs = sum(r["message_count"] for r in map_records)
    assert total_msgs == 100, f"{run_id}: expected 100 messages, got {total_msgs}"
    
    parse_errors = [r for r in map_records if r.get("parse_error")]
    assert len(parse_errors) == 0, f"{run_id}: {len(parse_errors)} parse errors in map"
    
    # Check state
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["phase"] == "reduce", f"{run_id}: expected reduce phase, got {state['phase']}"
    
    # Check final output
    final_text = (run_dir / "final.txt").read_text(encoding="utf-8").strip()
    assert len(final_text) > 10, f"{run_id}: final output too short ({len(final_text)} chars)"
    
    # Try parse final as JSON
    try:
        final_json = json.loads(final_text)
        is_json = True
    except json.JSONDecodeError:
        is_json = False
    
    return {
        "name": job_spec["name"],
        "run_id": run_id,
        "map_batches": len(map_records),
        "total_messages": total_msgs,
        "parse_errors": len(parse_errors),
        "reduce_rounds": state.get("reduce_round", "?"),
        "final_is_json": is_json,
        "final_length": len(final_text),
        "status": "PASS",
    }


async def main():
    print("=" * 60)
    print("ANALYZER E2E PIPELINE TEST (100 messages, mock mode)")
    print("=" * 60)
    
    results = []
    for job_spec in JOBS:
        print(f"\n--- Testing {job_spec['name']} ---")
        try:
            result = await test_job(job_spec)
            results.append(result)
            print(f"  PASS: {result['map_batches']} batches, {result['total_messages']} msgs, "
                  f"{result['reduce_rounds']} reduce round(s), final={result['final_length']} chars")
        except Exception as e:
            results.append({"name": job_spec["name"], "status": "FAIL", "error": str(e)})
            print(f"  FAIL: {e}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_pass = all(r.get("status") == "PASS" for r in results)
    for r in results:
        status = r["status"]
        name = r["name"]
        if status == "PASS":
            print(f"  [{status}] {name}: {r['map_batches']} batches, "
                  f"{r['reduce_rounds']} reduce rounds, JSON={r['final_is_json']}")
        else:
            print(f"  [{status}] {name}: {r.get('error', 'unknown')}")
    
    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
