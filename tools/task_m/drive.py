"""Inject session-bound ordinary DS down/up events through the runner's shared touch setter."""

import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_j"))
from control import records, send_action


def touch(root, x, y, down):
    rows = records(root)
    state = rows[-1]
    assert state["touch_owner"] and not any(row["event"] == "continue" for row in rows)
    assert 0 <= x <= 255 and 0 <= y <= 191
    number = state["control_sequence"] + 1
    temporary = root / "native-control.next"
    temporary.write_text(f"{state['session']} {number} touch {x} {y} {int(down)}\n")
    temporary.replace(root / "native-control.txt")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        replies = [row for row in records(root) if row["event"] == "touch_consumed" and
                   row["action_sequence"] == number]
        if replies:
            row = replies[0]
            assert row["source"] == "ds_touch" and row["consumed"] and row["touch_owner"]
            assert (row["touch_x"], row["touch_y"], row["touch_down"]) == (x, y, down)
            assert row["event_guest_deliveries"] == 0 and not row["guest_pen_down"]
            return row
        time.sleep(0.02)
    raise TimeoutError("raw DS touch was not consumed")


def tap(root, x, y, terminal):
    result = [touch(root, x, y, True), touch(root, x, y, False)]
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if any(row["action_sequence"] == result[-1]["action_sequence"] and row["event"] == terminal
               for row in records(root)):
            return result
        time.sleep(0.02)
    raise TimeoutError("tap result missing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.out.resolve()
    assert root.is_relative_to(Path(__file__).resolve().parents[2] / "local/task-m")
    started = time.monotonic()
    samples, taps = [], []

    def sample():
        row = send_action(root, "sample", records(root)[-1]["control_sequence"] + 1)
        samples.append(row)
        return row

    initial = sample()
    assert initial["attempts"] == 0
    for x, y, terminal, attempts, completed in (
        (54, 116, "incorrect_result", 1, False),
        (128, 166, "control_rejected", 1, False),
        (202, 116, "incorrect_result", 2, False),
        (128, 166, "control_rejected", 2, False),
        (128, 116, "correct_result", 3, True),
    ):
        taps.extend(tap(root, x, y, terminal))
        state = sample()
        assert state["attempts"] == attempts and state["completed"] == completed
        assert not state["native_contact"] and state["touch_owner"]
        print(f"DS tap ({x},{y}): {state['phase']}, attempts={attempts}", flush=True)
    time.sleep(max(0, 6 - (time.monotonic() - started)))
    completed = sample()
    assert completed["answers"] == [3, 5, 4] and completed["continue_available"]
    rows = records(root)
    keys = ("pc", "current", "requested", "selected", "cpu_cycles", "system_cycles", "cycles7",
            "insn9", "insn7", "cpsr", "terminal", "flash_sha1", "r", "backend", "forced_tier3",
            "guest_pen_down", "guest_adc_x", "guest_adc_y", "guest_touch_deliveries")
    invariant = {key: initial[key] for key in keys}
    assert all({key: row[key] for key in keys} == invariant for row in rows)
    assert invariant["backend"] == "compiled" and not invariant["forced_tier3"]
    assert (root / "requests.jsonl").stat().st_size == (root / "flash.jsonl").stat().st_size == 0
    entries = [json.loads(line) for line in (root / "entries.jsonl").read_text().splitlines()]
    assert len(entries) == 1 and entries[0]["kind"] == "lifecycle"
    proof = {"invariants_identical": True, "guest_invariant": invariant,
             "host_seconds_initial_to_completed_sample": time.monotonic() - started,
             "samples": samples, "entries_before_continue": entries,
             "answer_specific_commands_used": False, "manual_input": False}
    (root / "interaction-proof.json").write_text(json.dumps(proof, indent=2) + "\n")
    taps.extend(tap(root, 128, 166, "continue"))
    (root / "touch-inputs.json").write_text(json.dumps(taps, indent=2) + "\n")
    print("PASS: shared raw DS touch path, 3/reject/5/reject/4/Continue, frozen guest", flush=True)


if __name__ == "__main__":
    main()
