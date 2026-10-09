"""Audit the real-window Task O proof without replaying gameplay."""

import argparse
import hashlib
import json
from pathlib import Path
import struct


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.out.resolve()
    assert any(root.is_relative_to(Path(__file__).resolve().parents[2] / name) for name in ("local/task-o", "local/task-p"))
    result = json.loads((root / "result.json").read_text())
    assert result["pass"] and result["exit_code"] == 0 and not result.get("forced_cleanup")
    assert result["input_source"] in ("sdl-queue", "win32-sendinput")
    assert result["manual_input"] is False and result["answer_specific_controls"] is False
    native = rows(root / "native-probe.jsonl")
    held = [row for row in native if row["event"] == "held_sample"]
    assert held[1]["frontend_hold_presents"] > held[0]["frontend_hold_presents"]
    assert native[0]["backend"] == "compiled" and not native[0]["forced_tier3"]
    invariant = result["frozen_invariant"]
    assert all({key: row[key] for key in invariant} == invariant for row in native)
    assert (invariant["current"], invariant["requested"], invariant["selected"]) == (0x32, 0x41, 0x11)
    events = [row["event"] for row in native]
    assert events.count("intercept") == events.count("continue") == events.count("continue_original") == 1
    assert events.index("touch_release_clean") < events.index("touch_owner_released") < events.index("presentation_owner_released") < events.index("continue_original")
    release = next(row for row in native if row["event"] == "presentation_owner_released")
    assert not release["presentation_owner"] and not release["touch_owner"] and release["native_sha1"] == ""
    assert not release["native_contact"] and not release["guest_pen_down"] and release["guest_adc_x"] == 0 and release["guest_adc_y"] == 4095
    inputs = rows(root / "frontend-input.jsonl")
    custom = [row for row in inputs if row["event"] == "frontend_touch" and row["owner"]]
    assert len(custom) == 6
    assert [(row["ds_x"], row["ds_y"]) for row in custom if row["down"]] == [(54, 116), (128, 116), (128, 166)]
    assert all(row["consumed"] and row["guest_after"] == row["guest_before"] for row in custom)
    assert [row["down"] for row in custom] == [True, False] * 3
    for touch in custom:
        event = next(row for row in inputs if row["event"] == "frontend_button" and row["sequence"] == touch["sequence"])
        assert event["held"] and (event["client_x"], event["client_y"]) == (touch["logical_x"] * 2, touch["logical_y"] * 2)
    if result["input_source"] == "sdl-queue":
        queued = [row for row in inputs if row["event"] == "sdl_queue_button"]
        assert [row["control_sequence"] for row in queued] == list(range(1, 11))
        assert len([row for row in inputs if row["event"] == "frontend_button"]) == 10
    back = [row for row in inputs if row["event"] == "frontend_touch" and row["sequence"] in (9, 10)]
    assert len(back) == 2 and all(not row["owner"] and row["guest_after"] == row["guest_before"] + 1 for row in back)
    entries = rows(root / "entries.jsonl")
    assert sum(row["kind"] == "lifecycle" and row["r0"] == 0x41 for row in entries) == 1
    assert sum(row["kind"] == "rules_initializer" and row["r1"] == 0x41 for row in entries) == 1
    assert not any(row["kind"] in ("calculation_constructor", "write_api") for row in entries)
    phases = {}
    top_hashes = set()
    for name in ("initial", "initial-later", "incorrect", "correct"):
        capture = next(item["chosen"] for item in result["captures"] if item["label"] == name)
        assert capture["method"] == "print" and capture["matches_readback"]
        bitmap = Path(capture["path"]).read_bytes()
        offset = struct.unpack_from("<I", bitmap, 10)[0]
        assert struct.unpack_from("<ii", bitmap, 18) == (512, -768)
        pixels = bitmap[offset:]
        for row in range(384, 768, 2):
            first = pixels[row * 2048:(row + 1) * 2048]
            second = pixels[(row + 1) * 2048:(row + 2) * 2048]
            assert first == second
            assert all(first[column:column + 4] == first[column + 4:column + 8] for column in range(0, 2048, 8))
        phases[name] = capture["bottom_rgb_sha1"]
        top_hashes.add(capture["top_rgb_sha256"])
    assert len(top_hashes) == 1 and len(set(phases.values())) == 3
    before = (root / "initial.sav").read_bytes()
    after = (root / "session.sav").read_bytes()
    assert before == after and len(after) == 262144
    assert hashlib.sha256(after).hexdigest() == "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"
    assert (root / "flash.jsonl").stat().st_size == (root / "requests.jsonl").stat().st_size == 0
    audit = {"pass": True, "input_source": result["input_source"], "physical_win32_input_proven": result["input_source"] == "win32-sendinput",
        "actual_window_capture": "PrintWindow client", "native_window_sha1": phases, "integer_scale_exact": True,
        "guest_invariant": invariant, "held_present_counts": [row["frontend_hold_presents"] for row in held],
        "consumed_custom_events": len(custom), "custom_guest_deliveries": 0, "back_guest_deliveries": 2,
        "rules_initializer_count": 1, "calculation_constructor_count": 0, "logical_save_requests": 0,
        "flash_commits": 0, "changed_save_bytes": 0}
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
