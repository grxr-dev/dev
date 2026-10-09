"""Audit the bounded native quiz, exact original continuation and unchanged Flash."""

import argparse
import hashlib
import json
from pathlib import Path


BASELINE = "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"


def read(path):
    return json.loads(path.read_text())


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[2]
    root = args.out.resolve()
    assert root.is_relative_to(project / "local/task-l")
    reference = project / "local/task-k/normal-disabled-001"
    manifest = read(project / "local/task-l/reference-integrity.json")
    for filename, digest in manifest.items():
        path = project / "local/task-g/session-001/04-training-menu/checkpoint.state" if filename == "checkpoint.state" else reference / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    left, right = read(reference / "restore.json"), read(root / "restore.json")
    for key in ("source", "state_sha256", "save_sha256", "io_state", "rtc_state", "selector_after"):
        assert left[key] == right[key]
    assert right["save_sha256"] == BASELINE and not right["selector_after"]["forced_tier3"]
    assert "--force-tier3" not in read(root / "session.json")["command"]
    rows = records(root / "native-probe.jsonl")
    expected = ["boundary_context", "intercept", "panel_active", "held_sample",
                "choose", "incorrect_result", "control_rejected", "choose", "incorrect_result",
                "control_rejected", "choose", "correct_result", "held_sample", "continue", "continue_original"]
    assert [row["event"] for row in rows] == expected
    assert [row["sequence"] for row in rows] == list(range(1, 16))
    keys = ("pc", "current", "requested", "selected", "cpu_cycles", "system_cycles", "cycles7",
            "insn9", "insn7", "cpsr", "terminal", "flash_sha1", "r", "backend", "forced_tier3")
    invariant = {key: rows[0][key] for key in keys}
    assert invariant == {key: records(reference / "native-probe.jsonl")[0][key] for key in keys}
    assert all({key: row[key] for key in keys} == invariant for row in rows)
    assert invariant["backend"] == "compiled" and not invariant["forced_tier3"]
    assert (invariant["current"], invariant["requested"], invariant["selected"]) == (0x32, 0x41, 0x11)
    assert invariant["pc"] == 0x0204D790 and invariant["r"][14] == 0x02050268
    assert all(row["session"] == rows[1]["session"] and row["session"] for row in rows[1:])
    assert all(row["source"] == "diagnostic" for row in rows[3:])
    choices = [row for row in rows if row["event"] == "choose"]
    for index, row in enumerate(choices):
        assert row["answer"] == [3, 5, 4][index]
        assert row["attempts"] == index + 1 and row["answers"] == [3, 5, 4][:index + 1]
        assert row["completed"] == row["continue_available"] == (index == 2)
        assert row["phase"] == ("completed" if index == 2 else "incorrect")
    assert rows[3]["attempts"] == 0 and not rows[3]["continue_available"]
    for row in (rows[6], rows[9]):
        assert row["rejection"] == "not_completed" and not row["completed"] and not row["continue_available"]
    assert rows[12]["phase"] == "completed" and rows[12]["continue_available"]
    assert rows[13]["phase"] == rows[14]["phase"] == "resuming"
    controls = read(root / "controls.json")
    assert [row["action_sequence"] for row in controls] == list(range(1, 9))
    assert [row["action"] for row in controls] == ["sample", "choose", "continue", "choose", "continue", "choose", "sample", "continue"]
    assert read(root / "duplicate-continue-rejection.json")["control_file_unchanged"]
    interaction = read(root / "interaction-proof.json")
    assert interaction["invariants_identical"] and interaction["no_manual_input"]
    assert interaction["host_seconds_initial_to_completed_sample"] >= 6
    assert len(interaction["entries_before_continue"]) == 1
    assert read(root / "rules-context.json") == read(reference / "rules-context.json")
    rules = read(root / "rules-context.json")
    returned = read(root / "returned-menu-context.json")
    assert rules["globals"]["current"] == rules["globals"]["requested"] == 0x41
    assert rules["globals"]["selected"] == 0x11 and rules["globals"]["calculation_object"] == 0
    assert returned["globals"]["current"] == returned["globals"]["requested"] == 0x32
    assert returned["globals"]["calculation_object"] == 0
    assert not rules["dispatch"]["forced_tier3"] and not returned["dispatch"]["forced_tier3"]
    assert returned["dispatch"]["forced_tier3_misses"] == right["selector_after"]["forced_tier3_misses"]
    for filename in ("after.sav", "after-A-book.png", "after-B-book.png"):
        assert (root / "01-select-x20" / filename).read_bytes() == (reference / "01-select-x20" / filename).read_bytes()
    entries = records(root / "entries.jsonl")
    assert [row["kind"] for row in entries] == ["lifecycle", "rules_initializer", "lifecycle"]
    assert entries[0]["r0"] == 0x41 and entries[1]["r1"] == 0x41 and entries[2]["r0"] == 0x32
    assert entries[0]["backend"] == entries[2]["backend"] == "compiled"
    assert (root / "requests.jsonl").stat().st_size == (root / "flash.jsonl").stat().st_size == 0
    assert read(root / "00-menu/summary.json")["tap"] is None
    assert read(root / "01-select-x20/summary.json")["tap"] == [166, 75]
    assert read(root / "02-normal-back/summary.json")["tap"] == [240, 32]
    for path in sorted(root.glob("*/summary.json")):
        summary = read(path)
        assert summary["api_operations"] == summary["commit_events"] == summary["accepted_bytes"] == summary["changed_bytes"] == 0
        assert summary["save_sha256_before"] == summary["save_sha256_after"] == BASELINE
        assert summary["answer"] is None and not summary["strokes"]
        assert summary["replay_matches_live"] and summary["live_matches_disk"]
        assert hashlib.sha256((path.parent / "after.sav").read_bytes()).hexdigest() == BASELINE
    compact_keys = ("sequence", "event", "phase", "attempts", "answer", "answers", "completed", "continue_available",
                    "action_sequence", "control_sequence", "source", "action", "rejection", "current", "requested", "selected",
                    "cpu_cycles", "cycles7", "insn9", "insn7", "flash_sha1", "backend")
    audit_events = [{key: row[key] for key in compact_keys} for row in rows]
    for label, kind, context, counts in (
        ("rules_reached", "derived_checkpoint", rules, rules["io"]["counts"]),
        ("normal_back", "derived_action", rules, read(root / "02-normal-back/summary.json")["initial"]["counts"]),
        ("training_menu_restored", "derived_checkpoint", returned, returned["io"]["counts"]),
    ):
        audit_events.append({"sequence": len(audit_events) + 1, "event": label, "kind": kind,
                             "globals": context["globals"], "counts": counts, "flash_sha256": BASELINE})
    result = {"pass": True, "authoritative_root": str(root), "same_checkpoint": True,
              "normal_compiled_boundary": True, "answers": [3, 5, 4], "attempts": 3,
              "premature_continue_rejections": 2, "accepted_continue_count": 1,
              "manual_input": False, "guest_invariant": invariant,
              "host_seconds_initial_to_completed_sample": interaction["host_seconds_initial_to_completed_sample"],
              "rules_context_exact_match": True, "rules_screen_exact_match": True,
              "rules_initializer_count": 1, "calculation_constructor_count": 0,
              "normal_back_to_menu": True, "logical_save_requests": 0, "flash_commits": 0,
              "changed_save_bytes": 0, "before_sha256": BASELINE, "after_sha256": BASELINE,
              "prior_reference_unchanged": True, "events": audit_events}
    (root / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PASS: normal compiled native quiz, diagnostic 3/5/4, frozen guest, original rules/Back, zero saves")


if __name__ == "__main__":
    main()
