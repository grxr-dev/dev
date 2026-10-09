"""Capture shared runner readback and inject only normal DS-coordinate touch during the native hold."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_j"))
from control import records, send_action
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_m"))
from drive import tap
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_a"))
from probe_boot import write_frame


def capture(root, name):
    state = records(root)[-1]
    assert state["presentation_owner"] and state["touch_owner"]
    number = state["control_sequence"] + 1
    temporary = root / "native-control.next"
    temporary.write_text(f"{state['session']} {number} capture {name}\n")
    temporary.replace(root / "native-control.txt")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        events = [row for row in records(root) if row["event"] == "capture_complete" and
                  row["action_sequence"] == number and row["capture"] == name]
        if events:
            event = events[0]
            for engine in ("A", "B"):
                frame = json.loads((root / f"surface-{name}-{engine}.json").read_text())
                assert (frame["w"], frame["h"]) == (256, 192)
                rgb = bytes.fromhex(frame["rgb"])
                assert len(rgb) == 256 * 192 * 3
                digest = hashlib.sha1(rgb).hexdigest()
                if engine == "B":
                    assert frame["source"] == "native" and frame["presentation_owned"]
                    assert digest == event["native_sha1"] == event["presented_bottom_sha1"]
                else:
                    assert frame["source"] == "guest" and not frame["presentation_owned"]
                    assert digest == event["guest_top_sha1"]
                write_frame(root / f"surface-{name}-{engine}.png", frame)
            return event
        time.sleep(0.02)
    raise TimeoutError("shared runner readback capture missing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.out.resolve()
    assert root.is_relative_to(Path(__file__).resolve().parents[2] / "local/task-n")
    started = time.monotonic()
    initial = capture(root, "initial")
    assert initial["attempts"] == 0
    taps = tap(root, 54, 116, "incorrect_result")
    incorrect = capture(root, "incorrect")
    assert incorrect["answers"] == [3] and not incorrect["completed"]
    taps.extend(tap(root, 128, 116, "correct_result"))
    correct = capture(root, "correct")
    assert correct["answers"] == [3, 4] and correct["completed"]
    time.sleep(max(0, 6 - (time.monotonic() - started)))
    held = send_action(root, "sample", records(root)[-1]["control_sequence"] + 1)
    assert held["completed"] and held["presentation_owner"] and held["touch_owner"]
    keys = ("pc", "current", "requested", "selected", "cpu_cycles", "cycles7", "insn9", "insn7", "r", "flash_sha1",
            "guest_adc_x", "guest_adc_y", "guest_pen_down", "guest_touch_deliveries", "guest_top_sha1", "guest_bottom_sha1", "video_sha1")
    invariant = {key: initial[key] for key in keys}
    assert all({key: row[key] for key in keys} == invariant for row in records(root))
    assert len({event["native_sha1"] for event in (initial, incorrect, correct)}) == 3
    assert initial["backend"] == "compiled" and not initial["forced_tier3"]
    assert (root / "requests.jsonl").stat().st_size == (root / "flash.jsonl").stat().st_size == 0
    entries = [json.loads(line) for line in (root / "entries.jsonl").read_text().splitlines()]
    assert len(entries) == 1 and entries[0]["kind"] == "lifecycle"
    proof = {"guest_invariant": invariant, "invariants_identical": True,
             "initial": initial, "incorrect": incorrect, "correct": correct, "held_sample": held,
             "host_seconds_initial_to_completed_sample": time.monotonic() - started,
             "entries_before_continue": entries, "popup_required": False, "answer_specific_commands_used": False}
    (root / "interaction-proof.json").write_text(json.dumps(proof, indent=2) + "\n")
    taps.extend(tap(root, 128, 166, "continue"))
    (root / "touch-inputs.json").write_text(json.dumps(taps, indent=2) + "\n")
    print("PASS: shared 256x192 readback initial/incorrect/correct, DS taps 3/4/Continue, frozen guest/video", flush=True)


if __name__ == "__main__":
    main()
