"""Validate compiled launch interception, frozen state, exact continuation, normal Back and forced regression."""

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
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    assert root.is_relative_to(Path(__file__).resolve().parents[2] / "local/task-k")
    disabled, enabled, forced = (root / name for name in
        ("normal-disabled-001", "normal-enabled-001", "forced-regression-001"))
    restorations = [read(path / "restore.json") for path in (disabled, enabled, forced)]
    for key in ("source", "state_sha256", "save_sha256", "io_state", "rtc_state"):
        assert len({json.dumps(row[key], sort_keys=True) for row in restorations}) == 1
    assert restorations[0]["save_sha256"] == BASELINE
    for index, path in enumerate((disabled, enabled, forced)):
        restoration = restorations[index]
        assert restoration["selector_after"]["forced_tier3"] == (index == 2)
        command = read(path / "session.json")["command"]
        assert ("--force-tier3" in command) == (index == 2)
    events = [records(path / "native-probe.jsonl") for path in (disabled, enabled, forced)]
    assert [row["event"] for row in events[0]] == ["boundary_context", "boundary_disabled"]
    assert [row["event"] for row in events[1]] == ["boundary_context", "intercept", "panel_active",
                                                "held_sample", "held_sample", "continue_original"]
    assert [row["event"] for row in events[2]] == ["boundary_context", "intercept", "panel_active",
                                                "held_sample", "continue_original"]
    invariant_keys = ("pc", "current", "requested", "selected", "cpu_cycles", "system_cycles", "cycles7",
                      "insn9", "insn7", "cpsr", "terminal", "flash_sha1", "r")
    invariant = {key: events[0][0][key] for key in invariant_keys}
    for index, rows in enumerate(events):
        assert all({key: row[key] for key in invariant_keys} == invariant for row in rows)
        assert all(row["backend"] == ("tier3" if index == 2 else "compiled") for row in rows)
        assert all(row["forced_tier3"] == (index == 2) for row in rows)
    assert (invariant["pc"], invariant["current"], invariant["requested"], invariant["selected"]) == (0x0204D790, 0x32, 0x41, 0x11)
    assert invariant["r"][0] == 0x41 and invariant["r"][14] == 0x02050268 and not invariant["terminal"]
    hold = read(enabled / "hold-proof.json")
    assert hold["host_hold_between_samples_seconds_minimum"] >= 6 and hold["invariants_identical"]
    assert len(hold["entries_during_hold"]) == 1
    contexts = [read(path / "rules-context.json") for path in (disabled, enabled, forced)]
    assert contexts[0] == contexts[1]
    assert contexts[0]["globals"] == contexts[2]["globals"]
    assert contexts[0]["scene_object_hex"] == contexts[2]["scene_object_hex"]
    assert contexts[0]["globals"]["current"] == contexts[0]["globals"]["requested"] == 0x41
    assert contexts[0]["globals"]["selected"] == 0x11
    assert contexts[0]["globals"]["calculation_object"] == 0
    returned = read(enabled / "returned-menu-context.json")
    assert returned["globals"]["current"] == returned["globals"]["requested"] == 0x32
    assert returned["globals"]["calculation_object"] == 0
    for filename in ("after.sav", "after-A-book.png", "after-B-book.png"):
        assert len({(path / "01-select-x20" / filename).read_bytes() for path in (disabled, enabled, forced)}) == 1
    phases = {}
    for index, path in enumerate((disabled, enabled, forced)):
        entries = records(path / "entries.jsonl")
        assert sum(row["kind"] == "lifecycle" and row["r0"] == 0x41 for row in entries) == 1
        assert sum(row["kind"] == "rules_initializer" and row["r1"] == 0x41 for row in entries) == 1
        assert not any(row["kind"] in ("calculation_constructor", "write_api") for row in entries)
        assert all(row["forced_tier3"] == (index == 2) for row in entries)
        assert entries[0]["backend"] == ("tier3" if index == 2 else "compiled")
        assert (path / "requests.jsonl").stat().st_size == (path / "flash.jsonl").stat().st_size == 0
        phases[path.name] = []
        for summary_path in sorted(path.glob("*/summary.json")):
            summary = read(summary_path)
            assert summary["api_operations"] == summary["commit_events"] == summary["accepted_bytes"] == summary["changed_bytes"] == 0
            assert summary["answer"] is None and not summary["strokes"]
            assert summary["save_sha256_before"] == summary["save_sha256_after"] == BASELINE
            assert hashlib.sha256((summary_path.parent / "after.sav").read_bytes()).hexdigest() == BASELINE
            assert summary["replay_matches_live"] and summary["live_matches_disk"]
            if index < 2:
                stats = read(path / "rules-context.json")["dispatch"]
                assert not stats["forced_tier3"]
                assert stats["forced_tier3_misses"] == restorations[index]["selector_after"]["forced_tier3_misses"]
            phases[path.name].append(summary["label"])
    result = {"pass": True, "baseline_sha256": BASELINE, "same_checkpoint": True,
              "target_backend": "compiled", "normal_selector_off": True,
              "boundary": invariant, "hold": hold, "normal_rules_context_exact_match": True,
              "normal_rules_images_exact_match": True, "rules_initializer_backend": "tier3",
              "normal_back_to_menu": True, "forced_regression_pass": True,
              "logical_save_operations": 0, "flash_commits": 0, "changed_bytes": 0,
              "rules_transition_count": 1, "rules_initializer_count": 1,
              "calculation_constructor_count": 0, "phases": phases,
              "host_panel_to_continue_seconds_from_file_timestamps":
                  ((enabled / "native-probe.jsonl").stat().st_mtime_ns -
                   (enabled / "native-panel.bmp").stat().st_mtime_ns) / 1e9,
              "normal_control_channel_final_token": (enabled / "native-control.txt").read_text().strip()}
    (root / "proof-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PASS: actual compiled lifecycle, frozen native state, exact continuation, Back, zero saves, Tier-3 regression")


if __name__ == "__main__":
    main()
