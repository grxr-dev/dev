"""Audit raw DS touch ownership, frozen guest, clean handoff, original rules/Back and zero saves."""

import argparse
import hashlib
import json
from pathlib import Path

BASELINE = "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[2]
    root = args.out.resolve()
    assert root.is_relative_to(project / "local/task-m")
    reference = project / "local/task-k/normal-disabled-001"
    for filename, digest in read(project / "local/task-m/reference-integrity.json").items():
        path = project / "local/task-g/session-001/04-training-menu/checkpoint.state" if filename == "checkpoint.state" else reference / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    restored = read(root / "restore.json")
    for key in ("source", "state_sha256", "save_sha256", "io_state", "rtc_state", "selector_after"):
        assert restored[key] == read(reference / "restore.json")[key]
    assert restored["save_sha256"] == BASELINE and not restored["selector_after"]["forced_tier3"]
    assert "--force-tier3" not in read(root / "session.json")["command"]
    events = rows(root / "native-probe.jsonl")
    assert [row["sequence"] for row in events] == list(range(1, 35))
    assert events[0]["event"] == "boundary_context" and events[1]["event"] == "intercept"
    assert [row["event"] for row in events[-4:]] == ["continue", "touch_release_clean", "touch_owner_released", "continue_original"]
    invariant_keys = ("pc", "current", "requested", "selected", "cpu_cycles", "system_cycles", "cycles7",
                      "insn9", "insn7", "cpsr", "terminal", "flash_sha1", "r", "backend", "forced_tier3")
    invariant = {key: events[0][key] for key in invariant_keys}
    assert invariant == {key: rows(reference / "native-probe.jsonl")[0][key] for key in invariant_keys}
    assert all({key: row[key] for key in invariant_keys} == invariant for row in events)
    assert invariant["backend"] == "compiled" and not invariant["forced_tier3"]
    assert all(not row["guest_pen_down"] and row["guest_adc_x"] == 0 and row["guest_adc_y"] == 4095
               and row["guest_touch_deliveries"] == 2 for row in events)
    assert all(row["touch_owner"] for row in events[2:-2])
    assert not any(row["source"] == "native_ui" for row in events)
    assert not any(row["source"] == "diagnostic" and row["action"] != "sample" for row in events)
    touches = [row for row in events if row["event"] == "touch_consumed"]
    assert len(touches) == 12 and touches == read(root / "touch-inputs.json")
    expected_taps = [(54, 116, 3), (128, 166, 1), (202, 116, 5), (128, 166, 1), (128, 116, 4), (128, 166, 1)]
    for index, (x, y, target) in enumerate(expected_taps):
        for down, event in zip((True, False), touches[index * 2:index * 2 + 2]):
            assert (event["touch_x"], event["touch_y"], event["touch_target"], event["touch_down"]) == (x, y, target, down)
            assert event["source"] == "ds_touch" and event["action"] == "touch"
            assert event["touch_owner"] and event["consumed"] and event["event_guest_deliveries"] == 0
            assert event["native_contact"] == down
    assert [row["touch_events"] for row in touches] == list(range(1, 13))
    choices = [row for row in events if row["event"] == "choose"]
    assert [row["answer"] for row in choices] == [3, 5, 4]
    for index, event in enumerate(choices):
        assert event["source"] == "ds_touch" and not event["touch_down"]
        assert event["answers"] == [3, 5, 4][:index + 1] and event["attempts"] == index + 1
        assert event["completed"] == event["continue_available"] == (index == 2)
    rejected = [row for row in events if row["event"] == "control_rejected"]
    assert len(rejected) == 2 and [row["attempts"] for row in rejected] == [1, 2]
    assert all(row["source"] == "ds_touch" and row["rejection"] == "not_completed" and not row["completed"] for row in rejected)
    assert len([row for row in events if row["event"] == "continue"]) == 1
    assert events[-4]["source"] == "ds_touch" and events[-4]["answers"] == [3, 5, 4]
    assert not events[-3]["native_contact"] and not events[-2]["touch_owner"]
    proof = read(root / "interaction-proof.json")
    assert proof["invariants_identical"] and not proof["answer_specific_commands_used"] and not proof["manual_input"]
    assert proof["host_seconds_initial_to_completed_sample"] >= 6
    assert len(proof["entries_before_continue"]) == 1
    menu, rules, settled, returned = [read(root / f"{name}-context.json") for name in ("menu", "rules", "rules-settled", "returned-menu")]
    stripped_rules = {key: value for key, value in rules.items() if key != "touch"}
    assert stripped_rules == read(reference / "rules-context.json")
    clean = {"adc_x": 0, "adc_y": 4095, "down": False, "owned": False}
    for context, deliveries in ((menu, 0), (rules, 2), (settled, 2), (returned, 4)):
        assert context["touch"] == dict(clean, guest_deliveries=deliveries)
        assert not context["dispatch"]["forced_tier3"]
        assert context["dispatch"]["forced_tier3_misses"] == restored["selector_after"]["forced_tier3_misses"]
        assert context["globals"]["calculation_object"] == 0
    assert rules["globals"] == settled["globals"]
    assert rules["globals"]["current"] == rules["globals"]["requested"] == 0x41
    assert returned["globals"]["current"] == returned["globals"]["requested"] == 0x32
    for filename in ("after-A-book.png", "after-B-book.png", "after.sav"):
        assert (root / "01-select-x20" / filename).read_bytes() == (reference / "01-select-x20" / filename).read_bytes()
    assert (root / "01-select-x20/after-B-book.png").read_bytes() == (root / "02-rules-no-input/after-B-book.png").read_bytes()
    entries = rows(root / "entries.jsonl")
    assert [row["kind"] for row in entries] == ["lifecycle", "rules_initializer", "lifecycle"]
    assert entries[0]["backend"] == entries[2]["backend"] == "compiled"
    assert entries[0]["r0"] == 0x41 and entries[2]["r0"] == 0x32
    assert (root / "requests.jsonl").stat().st_size == (root / "flash.jsonl").stat().st_size == 0
    for path in sorted(root.glob("*/summary.json")):
        summary = read(path)
        assert summary["api_operations"] == summary["commit_events"] == summary["accepted_bytes"] == summary["changed_bytes"] == 0
        assert summary["save_sha256_before"] == summary["save_sha256_after"] == BASELINE
        assert summary["replay_matches_live"] and summary["live_matches_disk"]
        assert summary["answer"] is None and not summary["strokes"]
        assert hashlib.sha256((path.parent / "after.sav").read_bytes()).hexdigest() == BASELINE
    assert read(root / "01-select-x20/summary.json")["tap"] == [166, 75]
    assert read(root / "02-rules-no-input/summary.json")["tap"] is None
    assert read(root / "03-normal-back/summary.json")["tap"] == [240, 32]
    compact_keys = ("sequence", "event", "source", "action", "action_sequence", "phase", "attempts", "answers",
                    "completed", "continue_available", "rejection", "touch_x", "touch_y", "touch_down", "touch_target",
                    "touch_events", "consumed", "touch_owner", "native_contact", "guest_pen_down", "guest_adc_x", "guest_adc_y",
                    "guest_touch_deliveries", "event_guest_deliveries", "current", "requested", "selected", "cpu_cycles", "cycles7",
                    "insn9", "insn7", "flash_sha1", "backend")
    audit_events = [{key: event[key] for key in compact_keys} for event in events]
    for label, context in (("rules_reached", rules), ("rules_no_input_settled", settled), ("normal_back_menu_restored", returned)):
        audit_events.append({"sequence": len(audit_events) + 1, "event": label, "kind": "derived_checkpoint",
                             "globals": context["globals"], "touch": context["touch"], "flash_sha256": BASELINE})
    result = {"pass": True, "authoritative_root": str(root), "ordinary_shared_touch_setter": "nds_set_touch",
              "native_touch_events": 12, "native_taps": 6, "custom_event_guest_deliveries": 0,
              "answers": [3, 5, 4], "premature_continue_rejections": 2, "accepted_continue_count": 1,
              "guest_invariant": invariant, "normal_compiled_boundary": True, "rules_context_exact_match": True,
              "rules_ui_exact_match": True, "no_input_settle_cycles_requested": 30000000,
              "no_stale_touch": True, "normal_back_to_menu": True, "rules_initializer_count": 1,
              "calculation_constructor_count": 0, "logical_save_requests": 0, "flash_commits": 0,
              "changed_save_bytes": 0, "before_sha256": BASELINE, "after_sha256": BASELINE,
              "host_seconds_initial_to_completed_sample": proof["host_seconds_initial_to_completed_sample"],
              "prior_reference_unchanged": True, "events": audit_events}
    (root / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PASS: DS touch 3/reject/5/reject/4/Continue; exclusive ownership, clean resume/rules/Back, zero saves")


if __name__ == "__main__":
    main()
