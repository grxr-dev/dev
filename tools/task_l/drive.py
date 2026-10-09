"""Issue the exact authorized 3 -> 5 -> 4 native interaction and one explicit Continue."""

import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_j"))
from control import records, send_action


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.out.resolve()
    assert root.is_relative_to(Path(__file__).resolve().parents[2] / "local/task-l")
    results = []
    initial = send_action(root, "sample", 1)
    assert initial["phase"] == "question" and initial["attempts"] == 0
    results.append(initial)
    started = time.monotonic()
    for answer, number, expected in ((3, 2, [3]), (5, 4, [3, 5]), (4, 6, [3, 5, 4])):
        reply = send_action(root, "choose", number, answer)
        assert reply["answers"] == expected and reply["attempts"] == len(expected)
        assert reply["completed"] == (answer == 4)
        assert reply["continue_available"] == (answer == 4)
        results.append(reply)
        if answer != 4:
            rejected = send_action(root, "continue", number + 1, expect_rejected=True)
            assert rejected["rejection"] == "not_completed" and rejected["answers"] == expected
            results.append(rejected)
        deadline = time.monotonic() + 5
        capture = root / f"native-panel.bmp.{reply['sequence']}.bmp"
        while not capture.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert capture.exists()
        print(f"choose {answer}: phase={reply['phase']}, attempts={reply['attempts']}, capture={capture.name}", flush=True)
    time.sleep(max(0, 6 - (time.monotonic() - started)))
    completed = send_action(root, "sample", 7)
    results.append(completed)
    assert completed["phase"] == "completed" and completed["answers"] == [3, 5, 4]
    rows = records(root)
    keys = ("pc", "current", "requested", "selected", "cpu_cycles", "system_cycles", "cycles7",
            "insn9", "insn7", "cpsr", "terminal", "flash_sha1", "r", "backend", "forced_tier3")
    invariant = {key: initial[key] for key in keys}
    assert all({key: row[key] for key in keys} == invariant for row in rows)
    assert invariant["backend"] == "compiled" and not invariant["forced_tier3"]
    assert not any(row["source"] == "native_ui" for row in rows)
    assert (root / "requests.jsonl").stat().st_size == (root / "flash.jsonl").stat().st_size == 0
    entries = [json.loads(line) for line in (root / "entries.jsonl").read_text().splitlines()]
    assert len(entries) == 1 and entries[0]["kind"] == "lifecycle"
    proof = {"invariants_identical": True, "guest_invariant": invariant,
             "host_seconds_initial_to_completed_sample": time.monotonic() - started,
             "controls": results, "entries_before_continue": entries, "no_manual_input": True}
    (root / "interaction-proof.json").write_text(json.dumps(proof, indent=2) + "\n")
    continuation = send_action(root, "continue", 8)
    assert continuation["phase"] == "resuming" and continuation["completed"]
    results.append(continuation)
    (root / "controls.json").write_text(json.dumps(results, indent=2) + "\n")
    print("PASS: explicit diagnostic 3 -> 5 -> 4, two premature Continues rejected, guest frozen, one Continue", flush=True)


if __name__ == "__main__":
    main()
