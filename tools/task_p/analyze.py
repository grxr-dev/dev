"""Audit the bounded SDL host run and its exercise-contract lifecycle, without replay."""

import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    root = args.out.resolve()
    assert root.is_relative_to(repository / "local/task-p")
    subprocess.run(["python", str(repository / "tools/task_o/analyze.py"), "--out", str(root)], check=True)
    result = json.loads((root / "result.json").read_text())
    assert result["activation"] == {"NDS_BRAINAGE_CUSTOM_EXERCISE": "1", "NDS_BRAINAGE_NATIVE_PRESENTATION": "1"}
    native = [json.loads(line) for line in (root / "native-probe.jsonl").read_text().splitlines()]
    events = [row["event"] for row in native]
    lifetime = ("host_entered", "exercise_instantiated", "exercise_begin", "panel_active", "continue",
                "touch_release_clean", "touch_owner_released", "presentation_owner_released",
                "exercise_end", "exercise_destroyed", "host_cleanup", "continue_original")
    assert all(events.count(event) == 1 for event in lifetime)
    assert [events.index(event) for event in lifetime] == sorted(events.index(event) for event in lifetime)
    created = next(row for row in native if row["event"] == "exercise_instantiated")
    assert created["exercise_id"] == "arithmetic-2plus2" and created["exercise_present"]
    rendered = [row for row in native if row["event"] == "exercise_render"]
    assert [row["render_count"] for row in rendered] == [1, 2, 3]
    assert [row["phase"] for row in rendered] == ["question", "incorrect", "completed"]
    assert all(row["begin_count"] == 1 for row in rendered)
    touches = [row for row in native if row["event"] == "exercise_touch"]
    assert [row["exercise_touch_count"] for row in touches] == list(range(1, 7))
    assert all(row["source"] == "ds_touch" and row["event_guest_deliveries"] == 0 for row in touches)
    assert [row["answers"] for row in touches if not row["touch_down"]] == [[3], [3, 4], [3, 4]]
    queries = [row for row in native if row["event"] == "host_can_continue"]
    assert len(queries) == 6 and queries[-1]["status_queries"] == 12
    assert not queries[1]["continue_available"] and queries[3]["continue_available"]
    destroyed = next(row for row in native if row["event"] == "exercise_destroyed")
    assert not destroyed["exercise_present"] and not destroyed["touch_owner"] and not destroyed["presentation_owner"]
    assert destroyed["native_sha1"] == "" and not destroyed["guest_pen_down"]
    assert not any(row["source"] == "diagnostic" and row["action"] in ("choose", "continue", "touch") for row in native)
    host = (repository / "tools/brainage_custom/bc_host.h").read_text()
    assert "launch_exercise()" in host and "hold.exercise->touch" in host and "hold.exercise->render" in host
    assert all(token not in host for token in ("2 + 2", "ArithmeticQuiz", "value == 4", "answer == 4", "x >= 24"))
    for name in ("bc_contract.h", "bc_quiz.h", "bc_surface.h", "bc_catalog.h"):
        source = (repository / "tools/brainage_custom" / name).read_text()
        assert all(token not in source for token in ("0x020", "g_cpu", "nds_set_touch", "SDL_", "flash_digest")), name
    audit = {"pass": True, "exercise_id": created["exercise_id"], "stable_activation_only": True,
             "begin_count": 1, "render_count": 3, "exercise_touch_count": 6, "host_status_queries": 12,
             "input_source": result["input_source"], "sdl_render_driver": result["sdl_render_driver"],
             "lifetime_order": list(lifetime), "local_answers": [3, 4], "host_answer_logic": False,
             "exercise_destroyed_before_resume": True, "source_separation_checks": True,
             "diagnostic_answers_used": False}
    (root / "contract-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    compact = [{key: row[key] for key in ("sequence", "event", "exercise_id", "exercise_present", "begin_count",
               "render_count", "exercise_touch_count", "status_queries", "phase", "answers", "current", "requested",
               "selected", "cpu_cycles", "cycles7", "insn9", "insn7", "frontend_hold_presents", "flash_sha1")}
               for row in native if row["event"] in lifetime or row["event"] in ("exercise_render", "exercise_touch", "host_can_continue", "held_sample")]
    (root / "contract-events.json").write_text(json.dumps(compact, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
