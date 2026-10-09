"""Supply one session-bound, acknowledged native action without advancing guest logic directly."""

import argparse
import json
from pathlib import Path
import time


def records(root):
    return [json.loads(line) for line in (root / "native-probe.jsonl").read_text().splitlines(keepends=True) if line.endswith("\n")]


def send_action(root, action, sequence, answer=None, expect_rejected=False):
    project = Path(__file__).resolve().parents[2]
    root = Path(root).resolve()
    assert any(root.is_relative_to(project / name) for name in ("local/task-j", "local/task-k", "local/task-l", "local/task-m", "local/task-n"))
    rows = records(root)
    assert rows and rows[-1]["enabled"] and any(row["event"] == "panel_active" for row in rows)
    assert not any(row["event"] in ("continue", "continue_original") for row in rows), "probe already resumed"
    state = rows[-1]
    assert state["session"] and 0 < sequence <= 0xFFFFFFFF
    assert sequence == state["control_sequence"] + 1, "sequence must be exactly next"
    assert action in ("sample", "choose", "continue")
    assert (answer in (3, 4, 5)) if action == "choose" else answer is None
    if not expect_rejected:
        assert action != "continue" or state["continue_available"], "correct answer required before Continue"
        assert action != "choose" or not state["completed"], "exercise already completed"
    temporary = root / "native-control.next"
    suffix = f" {answer}" if answer is not None else ""
    temporary.write_text(f"{state['session']} {sequence} {action}{suffix}\n")
    temporary.replace(root / "native-control.txt")
    deadline = time.monotonic() + 10
    terminal = {"sample": {"held_sample", "control_rejected"},
                "choose": {"incorrect_result", "correct_result", "control_rejected"},
                "continue": {"continue", "control_rejected"}}[action]
    while time.monotonic() < deadline:
        replies = [row for row in records(root) if row["source"] == "diagnostic" and
                   row["action_sequence"] == sequence and row["event"] in terminal]
        if replies:
            reply = replies[0]
            assert (reply["event"] == "control_rejected") == expect_rejected, reply
            return reply
        time.sleep(0.02)
    raise TimeoutError("native action was not acknowledged")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--action", choices=("sample", "choose", "continue"), required=True)
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--answer", type=int, choices=(3, 4, 5))
    parser.add_argument("--expect-rejected", action="store_true")
    args = parser.parse_args()
    reply = send_action(args.out, args.action, args.sequence, args.answer, args.expect_rejected)
    print(json.dumps(reply, indent=2))


if __name__ == "__main__":
    main()
