"""Audit shared native presentation, immutable measured guest video, touch ownership and clean original return."""

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
    assert root.is_relative_to(project / "local/task-n")
    reference = project / "local/task-k/normal-disabled-001"
    previous = project / "local/task-m/normal-enabled-001"
    for filename, digest in read(project / "local/task-n/reference-integrity.json").items():
        path = project / "local/task-g/session-001/04-training-menu/checkpoint.state" if filename == "checkpoint.state" else reference / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    restored = read(root / "restore.json")
    for key in ("source", "state_sha256", "save_sha256", "io_state", "rtc_state", "selector_after"):
        assert restored[key] == read(reference / "restore.json")[key]
    assert restored["save_sha256"] == BASELINE and not restored["selector_after"]["forced_tier3"]
    assert "--force-tier3" not in read(root / "session.json")["command"]
    events = rows(root / "native-probe.jsonl")
    expected = ["boundary_context", "intercept", "panel_active", "capture_complete", "touch_consumed", "touch_consumed",
                "choose", "incorrect_result", "capture_complete", "touch_consumed", "touch_consumed", "choose", "correct_result",
                "capture_complete", "held_sample", "touch_consumed", "touch_consumed", "continue", "touch_release_clean",
                "touch_owner_released", "presentation_owner_released", "capture_complete", "continue_original"]
    assert [event["event"] for event in events] == expected
    assert [event["sequence"] for event in events] == list(range(1, 24))
    keys = ("pc", "current", "requested", "selected", "cpu_cycles", "system_cycles", "cycles7", "insn9", "insn7",
            "cpsr", "terminal", "flash_sha1", "r", "backend", "forced_tier3", "guest_top_sha1", "guest_bottom_sha1", "video_sha1",
            "guest_adc_x", "guest_adc_y", "guest_pen_down", "guest_touch_deliveries")
    invariant = {key: events[0][key] for key in keys}
    assert all({key: event[key] for key in keys} == invariant for event in events)
    assert invariant["backend"] == "compiled" and not invariant["forced_tier3"]
    assert (invariant["current"], invariant["requested"], invariant["selected"]) == (0x32, 0x41, 0x11)
    assert invariant["guest_adc_x"] == 0 and invariant["guest_adc_y"] == 4095 and not invariant["guest_pen_down"]
    assert invariant["guest_touch_deliveries"] == 2
    assert all(event["presentation_owner"] and event["bottom_source"] == "native" for event in events[2:20])
    assert all(not event["presentation_owner"] and event["bottom_source"] == "guest" for event in events[20:])
    assert all(event["touch_owner"] for event in events[2:19]) and not any(event["touch_owner"] for event in events[19:])
    assert all(event["top_source"] == "guest" and not event["popup"] for event in events)
    assert not list(root.glob("native-panel.bmp*"))
    assert all(event["surface_width"] == 256 and event["surface_height"] == 192 for event in events)
    assert all(event["native_sha1"] == event["presented_bottom_sha1"] for event in events[2:20])
    assert all(event["native_sha1"] == "" and event["presented_bottom_sha1"] == invariant["guest_bottom_sha1"] for event in events[20:])
    assert not any(event["source"] == "native_ui" for event in events)
    assert all(event["action"] in ("capture", "sample") for event in events if event["source"] == "diagnostic")
    captures = [event for event in events if event["event"] == "capture_complete"]
    assert [event["capture"] for event in captures] == ["initial", "incorrect", "correct", "handoff"]
    capture_hashes = {}
    for event in captures:
        name = event["capture"]
        for engine in ("A", "B"):
            frame = read(root / f"surface-{name}-{engine}.json")
            assert (frame["w"], frame["h"]) == (256, 192)
            rgb = bytes.fromhex(frame["rgb"])
            assert len(rgb) == 256 * 192 * 3
            digest = hashlib.sha1(rgb).hexdigest()
            if engine == "A":
                assert digest == invariant["guest_top_sha1"] and frame["source"] == "guest" and not frame["presentation_owned"]
            else:
                assert digest == event["presented_bottom_sha1"]
                assert frame["presentation_owned"] == (name != "handoff")
                assert frame["source"] == ("guest" if name == "handoff" else "native")
                capture_hashes[name] = {"native_rgb_sha1": event["native_sha1"], "captured_rgb_sha1": digest}
    assert len({capture_hashes[name]["native_rgb_sha1"] for name in ("initial", "incorrect", "correct")}) == 3
    touches = [event for event in events if event["event"] == "touch_consumed"]
    assert touches == read(root / "touch-inputs.json") and len(touches) == 6
    for index, (x, y, target) in enumerate(((54, 116, 3), (128, 116, 4), (128, 166, 1))):
        for down, event in zip((True, False), touches[index * 2:index * 2 + 2]):
            assert (event["touch_x"], event["touch_y"], event["touch_target"], event["touch_down"]) == (x, y, target, down)
            assert event["source"] == "ds_touch" and event["consumed"] and event["event_guest_deliveries"] == 0
            assert event["native_contact"] == down
    assert [event["answer"] for event in events if event["event"] == "choose"] == [3, 4]
    assert events[7]["attempts"] == 1 and not events[7]["completed"]
    assert events[12]["attempts"] == 2 and events[12]["completed"]
    assert events[14]["continue_available"] and not events[18]["native_contact"]
    proof = read(root / "interaction-proof.json")
    assert proof["invariants_identical"] and not proof["answer_specific_commands_used"] and not proof["popup_required"]
    assert proof["host_seconds_initial_to_completed_sample"] >= 6 and len(proof["entries_before_continue"]) == 1
    menu, rules, settled, returned = [read(root / f"{name}-context.json") for name in ("menu", "rules", "rules-settled", "returned-menu")]
    assert rules == read(previous / "rules-context.json")
    assert settled == read(previous / "rules-settled-context.json")
    assert returned == read(previous / "returned-menu-context.json")
    assert rules["globals"]["current"] == rules["globals"]["requested"] == 0x41
    assert returned["globals"]["current"] == returned["globals"]["requested"] == 0x32
    for context, count in ((menu, 0), (rules, 2), (settled, 2), (returned, 4)):
        assert context["touch"] == {"adc_x": 0, "adc_y": 4095, "down": False, "owned": False, "guest_deliveries": count}
        assert context["globals"]["calculation_object"] == 0 and not context["dispatch"]["forced_tier3"]
    for phase in ("00-menu", "01-select-x20", "02-rules-no-input", "03-normal-back"):
        for engine in ("A", "B"):
            assert (root / phase / f"after-{engine}-book.png").read_bytes() == (previous / phase / f"after-{engine}-book.png").read_bytes()
        summary = read(root / phase / "summary.json")
        assert summary["save_sha256_before"] == summary["save_sha256_after"] == BASELINE
        assert summary["api_operations"] == summary["commit_events"] == summary["accepted_bytes"] == summary["changed_bytes"] == 0
        assert summary["answer"] is None and not summary["strokes"] and summary["replay_matches_live"] and summary["live_matches_disk"]
        for record in rows(root / phase / "debug.jsonl"):
            if record["request"]["cmd"] == "framebuffer":
                assert record["response"]["source"] == "guest" and not record["response"]["presentation_owned"]
    entries = rows(root / "entries.jsonl")
    assert [event["kind"] for event in entries] == ["lifecycle", "rules_initializer", "lifecycle"]
    assert entries[0]["backend"] == entries[2]["backend"] == "compiled"
    assert (root / "requests.jsonl").stat().st_size == (root / "flash.jsonl").stat().st_size == 0
    assert read(root / "01-select-x20/summary.json")["tap"] == [166, 75]
    assert read(root / "02-rules-no-input/summary.json")["tap"] is None
    assert read(root / "03-normal-back/summary.json")["tap"] == [240, 32]
    result = {"pass": True, "authoritative_root": str(root), "surface_dimensions": [256, 192],
              "capture_path": "debug_framebuffer_response -> nds_gpu2d_presented_framebuffer",
              "phase_hashes": capture_hashes, "guest_invariant": invariant, "measured_video_bytes": 675840,
              "guest_video_unchanged": True, "popup_used": False, "answers": [3, 4], "custom_touch_events": 6,
              "custom_guest_deliveries": 0, "continue_count": 1, "owners_removed_before_resume": True,
              "native_surface_destroyed_before_resume": True, "original_rules_exact_match": True,
              "normal_back_to_menu": True, "rules_initializer_count": 1, "calculation_constructor_count": 0,
              "logical_save_requests": 0, "flash_commits": 0, "changed_save_bytes": 0,
              "before_sha256": BASELINE, "after_sha256": BASELINE, "events": events,
              "host_seconds_initial_to_completed_sample": proof["host_seconds_initial_to_completed_sample"]}
    (root / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("pass", "phase_hashes", "guest_invariant", "host_seconds_initial_to_completed_sample")}, indent=2))


if __name__ == "__main__":
    main()
