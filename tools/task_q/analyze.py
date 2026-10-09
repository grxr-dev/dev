"""Audit continuous frontend strokes, real-window interpolation and unchanged guest/host safety."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    root = args.out.resolve()
    assert root.is_relative_to(repository / "local/task-q")
    result = json.loads((root / "result.json").read_text())
    assert result["pass"] and result["exit_code"] == 0 and not result.get("forced_cleanup")
    assert result["input_source"] == "sdl-queue" and not result["manual_input"] and not result["answer_specific_controls"]
    assert result["activation"] == {"NDS_BRAINAGE_CUSTOM_EXERCISE": "1", "NDS_BRAINAGE_NATIVE_PRESENTATION": "1", "NDS_BRAINAGE_CUSTOM_EXERCISE_ID": "freehand-canvas"}
    native = rows(root / "native-probe.jsonl")
    events = [row["event"] for row in native]
    assert events.count("intercept") == events.count("continue") == events.count("continue_original") == 1
    invariant = result["frozen_invariant"]
    assert all({key: row[key] for key in invariant} == invariant for row in native)
    assert native[0]["backend"] == "compiled" and not native[0]["forced_tier3"]
    assert (invariant["current"], invariant["requested"], invariant["selected"]) == (0x32, 0x41, 0x11)
    inputs = rows(root / "frontend-input.jsonl")
    queued = [row for row in inputs if row["event"] in ("sdl_queue_button", "sdl_queue_motion")]
    assert [row["control_sequence"] for row in queued] == list(range(1, 21))
    frontend = [row for row in inputs if row["event"] in ("frontend_button", "frontend_motion")]
    assert [row["sequence"] for row in frontend] == list(range(1, 21))
    custom = [row for row in inputs if row["event"] == "frontend_touch" and row["owner"]]
    assert len(custom) == 16 and all(row["consumed"] and row["guest_before"] == row["guest_after"] for row in custom)
    exercise = [row for row in native if row["event"] == "exercise_touch"]
    assert len(exercise) == 16 and all(row["exercise_id"] == "freehand-canvas" and row["source"] == "ds_touch" for row in exercise)
    assert all(row["event_guest_deliveries"] == 0 for row in exercise)
    assert not any(row["source"] == "diagnostic" and row["action"] in ("choose", "continue", "touch") for row in native)
    gestures = (((64,48), (96,72), (128,96), (160,120), (192,132)),
                ((192,48), (160,72), (128,96), (96,120), (64,132)))
    provenance = []
    for stroke_index, start in enumerate((0, 8)):
        for point_index, point in enumerate((*gestures[stroke_index], (0,0))):
            touch = custom[start + point_index]
            entry = next(row for row in frontend if row["sequence"] == touch["sequence"])
            queue = next(row for row in queued if row["control_sequence"] == touch["sequence"])
            assert (touch["ds_x"], touch["ds_y"]) == point and touch["down"] == (point_index < 5)
            assert entry["held"] and entry["event"] == ("frontend_motion" if 1 <= point_index <= 4 else "frontend_button")
            raw_point = gestures[stroke_index][min(point_index, 4)]
            assert (entry["client_x"], entry["client_y"]) == (2 * raw_point[0], 2 * (192 + raw_point[1]))
            assert (queue["client_x"], queue["client_y"]) == (entry["client_x"], entry["client_y"])
            assert (touch["logical_x"], touch["logical_y"]) == raw_point[:1] + (192 + raw_point[1],)
            state = exercise[start + point_index]
            assert state["native_contact"] == (point_index < 5)
            assert state["exercise_metrics"]["completed_strokes"] == stroke_index + (point_index == 5)
            assert state["exercise_metrics"]["point_count"] == stroke_index * 5 + min(point_index + 1, 5)
            provenance.append({"stroke": stroke_index + 1, "kind": "down" if point_index == 0 else "up" if point_index == 5 else "motion",
                "frontend_sequence": touch["sequence"], "queued_event": queue["event"], "client": [entry["client_x"], entry["client_y"]],
                "logical": [touch["logical_x"], touch["logical_y"]], "mapped_ds": list(point), "consumed": True,
                "guest_deliveries": 0, "exercise_metrics": state["exercise_metrics"]})
    premature = exercise[7]
    assert premature["exercise_metrics"]["completed_strokes"] == 1 and premature["exercise_metrics"]["point_count"] == 5
    assert not premature["continue_available"] and not premature["native_contact"]
    assert any(row["event"] == "control_rejected" and row["source"] == "ds_touch" for row in native)
    assert exercise[13]["continue_available"] and exercise[13]["exercise_metrics"]["completed_strokes"] == 2
    assert exercise[13]["exercise_metrics"]["point_count"] == 10 and not exercise[13]["native_contact"]
    pixel_samples = {"stroke1": ((80,60), (112,84), (144,108), (176,126)),
                     "stroke2": ((176,60), (144,84), (112,108), (80,126))}
    surface_hashes = {}
    top_hashes, windows = set(), set()
    pixel_evidence = []
    for label in ("initial", "initial-later", "stroke1", "stroke2", "rules"):
        capture = next(item["chosen"] for item in result["captures"] if item["label"] == label)
        assert capture["method"] == "print" and capture["matches_readback"]
        bitmap = Path(capture["path"]).read_bytes()
        offset = struct.unpack_from("<I", bitmap, 10)[0]
        assert struct.unpack_from("<ii", bitmap, 18) == (512, -768)
        pixels = bitmap[offset:]
        windows.add(capture["window"]["hwnd"])
        surface_hashes[label] = capture["bottom_rgb_sha1"]
        if label != "rules":
            top_hashes.add(capture["top_rgb_sha256"])
            for row in range(384, 768, 2):
                first = pixels[row * 2048:(row + 1) * 2048]
                assert first == pixels[(row + 1) * 2048:(row + 2) * 2048]
                assert all(first[column:column + 4] == first[column + 4:column + 8] for column in range(0, 2048, 8))
        for point in pixel_samples.get(label, ()):
            assert point not in gestures[0] + gestures[1]
            position = ((192 + point[1]) * 2 * 512 + point[0] * 2) * 4
            assert pixels[position:position + 3] == bytes((0x3f, 0x28, 0x15))
            pixel_evidence.append({"phase": label, "ds": point, "rgb": "15283f", "sampled_input_point": False})
    assert len(windows) == len(top_hashes) == 1
    assert surface_hashes["initial"] == surface_hashes["initial-later"] and len(set(surface_hashes.values())) == 4
    lifetime = ("touch_release_clean", "touch_owner_released", "presentation_owner_released", "exercise_end", "exercise_destroyed", "host_cleanup", "continue_original")
    assert [events.index(event) for event in lifetime] == sorted(events.index(event) for event in lifetime)
    destroyed = next(row for row in native if row["event"] == "exercise_destroyed")
    assert not destroyed["exercise_present"] and not destroyed["touch_owner"] and not destroyed["presentation_owner"]
    assert destroyed["native_sha1"] == "" and not destroyed["guest_pen_down"] and not destroyed["native_contact"]
    assert destroyed["exercise_metrics"]["point_count"] == 10
    entries = rows(root / "entries.jsonl")
    assert sum(row["kind"] == "lifecycle" and row["r0"] == 0x41 for row in entries) == 1
    assert sum(row["kind"] == "rules_initializer" for row in entries) == 1
    assert not any(row["kind"] in ("calculation_constructor", "write_api") for row in entries)
    back = [row for row in inputs if row["event"] == "frontend_touch" and row["sequence"] in (19, 20)]
    assert len(back) == 2 and all(not row["owner"] and row["guest_after"] == row["guest_before"] + 1 for row in back)
    before = (root / "initial.sav").read_bytes()
    assert before == (root / "session.sav").read_bytes() and len(before) == 262144
    assert hashlib.sha256(before).hexdigest() == "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"
    assert (root / "flash.jsonl").stat().st_size == (root / "requests.jsonl").stat().st_size == 0
    host = repository / "tools/brainage_custom/bc_host.h"
    original = subprocess.check_output(["git", "show", "e0c95fe472f4645f01c9d908a11e0ec53c1b2389:tools/brainage_custom/bc_host.h"], cwd=repository)
    assert host.read_text().replace("\r\n", "\n") == original.decode().replace("\r\n", "\n")
    held = [row["frontend_hold_presents"] for row in native if row["event"] == "held_sample"]
    assert held[-1] > held[0]
    audit = {"pass": True, "exercise_id": "freehand-canvas", "host_unchanged": True, "source": "sdl-queue",
        "initial_downs": 2, "motions": 8, "drawing_releases": 2, "completed_strokes": 2, "points": 10,
        "premature_continue_rejected": True, "custom_touch_events": 16, "custom_guest_deliveries": 0,
        "held_present_counts": held, "guest_invariant": invariant, "window_bottom_hashes": surface_hashes,
        "interpolated_pixels": pixel_evidence, "rules_initializer_count": 1, "calculation_constructor_count": 0,
        "logical_save_requests": 0, "flash_commits": 0, "changed_bytes": 0}
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (root / "stroke-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
