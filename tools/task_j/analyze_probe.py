"""Verify the bounded native-hold, original continuation, normal return and zero-save proof."""

import argparse
import hashlib
import json
from pathlib import Path


BASELINE = "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disabled", type=Path, required=True)
    parser.add_argument("--enabled", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reference, native = args.disabled, args.enabled
    left = json.loads((reference / "restore.json").read_text())
    right = json.loads((native / "restore.json").read_text())
    for key in ("state_sha256", "save_sha256", "io_state", "rtc_state"):
        assert left[key] == right[key]
    assert left["save_sha256"] == BASELINE
    disabled = records(reference / "native-probe.jsonl")
    enabled = records(native / "native-probe.jsonl")
    assert [row["event"] for row in disabled] == ["boundary_context", "boundary_disabled"]
    assert [row["event"] for row in enabled] == ["boundary_context", "intercept", "panel_active",
                                                 "held_sample", "held_sample", "continue_original"]
    keys = ("pc", "current", "requested", "selected", "cpu_cycles", "system_cycles", "cycles7",
            "insn9", "insn7", "cpsr", "terminal", "flash_sha1", "r")
    initial = {key: disabled[0][key] for key in keys}
    assert all({key: row[key] for key in keys} == initial for row in disabled + enabled)
    assert initial["pc"] == 0x0204D790
    assert (initial["current"], initial["requested"], initial["selected"]) == (0x32, 0x41, 0x11)
    assert initial["r"][0] == 0x41 and initial["r"][14] == 0x02050268
    assert not initial["terminal"]
    hold = json.loads((native / "hold-proof.json").read_text())
    assert hold["host_hold_between_samples_seconds_minimum"] >= 6 and hold["invariants_identical"]
    before = json.loads((reference / "rules-context.json").read_text())
    after = json.loads((native / "rules-context.json").read_text())
    assert before == after
    assert after["globals"]["current"] == after["globals"]["requested"] == 0x41
    assert after["globals"]["selected"] == 0x11 and after["globals"]["calculation_object"] == 0
    returned = json.loads((native / "returned-menu-context.json").read_text())
    assert returned["globals"]["current"] == returned["globals"]["requested"] == 0x32
    assert returned["globals"]["calculation_object"] == 0
    for filename in ("after.sav", "after-A-book.png", "after-B-book.png"):
        assert (reference / "01-select-x20" / filename).read_bytes() == (native / "01-select-x20" / filename).read_bytes()
    phases = {}
    for root in (reference, native):
        assert (root / "requests.jsonl").stat().st_size == (root / "flash.jsonl").stat().st_size == 0
        summaries = []
        for path in sorted(root.glob("*/summary.json")):
            summary = json.loads(path.read_text())
            assert summary["api_operations"] == summary["accepted_bytes"] == summary["changed_bytes"] == 0
            assert summary["answer"] is None and not summary["strokes"]
            assert summary["save_sha256_before"] == summary["save_sha256_after"] == BASELINE
            assert hashlib.sha256((path.parent / "after.sav").read_bytes()).hexdigest() == BASELINE
            assert summary["replay_matches_live"] and summary["live_matches_disk"]
            summaries.append(summary["label"])
        calls = records(root / "calls.jsonl")
        assert len(calls) < 6000
        assert sum(row["target"] == 0x0204D790 and row["r"][0] == 0x41 for row in calls) == 1
        assert sum(row["target"] == 0x020610B4 and row["r"][1] == 0x41 for row in calls) == 1
        assert not any(row["target"] == 0x02027A28 for row in calls)
        phases[root.name] = summaries
    result = {"pass": True, "baseline_sha256": BASELINE, "boundary": initial,
              "native_events": [row["event"] for row in enabled], "hold": hold,
              "rules_context_exact_match": True, "rules_images_exact_match": True,
              "normal_back_to_menu": True, "logical_save_operations": 0, "flash_commits": 0,
              "changed_bytes": 0, "rules_initializer_calls": 1, "calculation_constructor_calls": 0,
              "phases": phases, "execution_path": "forced Tier-3 guest, synchronous native C++ state"}
    result["host_panel_to_continue_seconds_from_file_timestamps"] = (
        (native / "native-probe.jsonl").stat().st_mtime_ns -
        (native / "native-panel.bmp").stat().st_mtime_ns) / 1e9
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("PASS: real native hold, exact original continuation, normal Back, zero save activity")


if __name__ == "__main__":
    main()
