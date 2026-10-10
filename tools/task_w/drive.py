"""Frozen Task W glyph through ordinary SDL input; label is offline metadata only."""
from corpus import load, EXPECTED

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_a"))
from probe_boot import write_frame

H0 = "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines(keepends=True) if line.endswith("\n")]


def wait_for(predicate, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.05)
    raise TimeoutError("expected observation did not arrive")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=19878)
    parser.add_argument("--observe-only", action="store_true")
    parser.add_argument("--input-source", choices=("sdl-queue",), default="sdl-queue")
    parser.add_argument("--brainage-host", action="store_true", default=True)
    parser.add_argument("--disabled-control", action="store_true")
    parser.add_argument("--freehand", action="store_true", default=True)
    parser.add_argument("--sample", type=int, choices=range(10), required=True)
    parser.add_argument("--visual", action="store_true")
    parser.add_argument("--handoff-visual", action="store_true")
    parser.add_argument("--legacy-v", action="store_true")
    args = parser.parse_args()
    sample = load()["samples"][args.sample]
    gesture = sample["strokes"]
    exercise_id = "digit-recognition-probe" if args.legacy_v else "digit-entry-probe"
    if args.legacy_v: assert args.sample==4
    visual = args.visual or args.handoff_visual
    if args.disabled_control and not args.brainage_host:
        parser.error("--disabled-control requires --brainage-host")
    if args.disabled_control: args.freehand = False
    if args.freehand and (not args.brainage_host or args.input_source != "sdl-queue" or args.disabled_control):
        parser.error("--freehand requires enabled --brainage-host and SDL-queue input")
    repository = Path(__file__).resolve().parents[2]
    root = args.out.resolve()
    assert root.is_relative_to(repository / "local/task-w")
    source = repository / "local/task-g/session-001/04-training-menu"
    initial = (source / "after.sav").read_bytes()
    assert len(initial) == 262144 and digest(initial) == H0
    assert digest((source / "checkpoint.state").read_bytes()) == "1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36"
    command = list(json.loads((repository / "local/task-n/normal-enabled-002/session.json").read_text())["command"])
    command[0] = str(repository / "build/task-o-sdl-runner/nds_runner.exe")
    command[1] = str(root)
    command[command.index("--serve")] = "--interactive"
    command[command.index("--port") + 1] = str(args.port)
    command[command.index("--save-path") + 1] = str(root / "session.sav")
    assert "--force-tier3" not in command
    assert hashlib.sha1(Path(command[command.index("--rom") + 1]).read_bytes()).hexdigest() == "b8a105bacc3234dede8d4465df0869f2b922a0e2"
    root.mkdir(parents=True, exist_ok=False)
    (root / "initial.sav").write_bytes(initial)
    (root / "session.sav").write_bytes(initial)
    environment = os.environ.copy()
    for name in list(environment):
        if name.startswith(("NDS_TASK_", "NDS_FRONTEND_", "NDS_BRAINAGE_")):
            environment.pop(name)
    environment.update({"NDS_TASK_J_CUSTOM_EXERCISE_PROBE": "1", "NDS_TASK_N_DS_PRESENTATION": "1",
        "NDS_TASK_F_RTC_PLUS_ONE_DAY": "1", "NDS_TASK_O_START_STATE": str(source / "checkpoint.state"),
        "NDS_TASK_J_CONTROL": str(root / "native-control.txt"), "NDS_TASK_N_CAPTURE_ROOT": str(root),
        "NDS_TASK_J_TRACE": str(root / "native-probe.jsonl"), "NDS_TASK_K_TRACE": str(root / "entries.jsonl"),
        "NDS_TASK_O_FRONTEND_TRACE": str(root / "frontend-input.jsonl"),
        "NDS_TASK_V_TRACE": str(root / "service.jsonl"),
        "NDS_TASK_C_TRACE": str(root / "requests.jsonl"), "NDS_FLASH_TRACE": str(root / "flash.jsonl")})
    if args.brainage_host:
        environment["NDS_SDL_RENDER_DRIVER"] = "software"
        environment.pop("NDS_TASK_J_CUSTOM_EXERCISE_PROBE", None)
        environment.pop("NDS_TASK_N_DS_PRESENTATION", None)
        if not args.disabled_control:
            environment.update({"NDS_BRAINAGE_CUSTOM_EXERCISE": "1", "NDS_BRAINAGE_NATIVE_PRESENTATION": "1"})
            if args.freehand:
                environment["NDS_BRAINAGE_CUSTOM_EXERCISE_ID"] = exercise_id
        else:
            environment.pop("NDS_BRAINAGE_CUSTOM_EXERCISE", None)
            environment.pop("NDS_BRAINAGE_NATIVE_PRESENTATION", None)
    queue_token = uuid.uuid4().hex
    queue_sequence = 0
    if args.input_source == "sdl-queue":
        environment.update({"NDS_TASK_O_WINDOW_CONTROL": str(root / "window-control.txt"), "NDS_TASK_O_CONTROL_TOKEN": queue_token})
    for name in ("native-probe.jsonl", "entries.jsonl", "requests.jsonl", "flash.jsonl", "frontend-input.jsonl"):
        (root / name).touch()
    evidence = {"command": command, "input_source": args.input_source, "manual_input": False,
        "answer_specific_controls": False, "checkpoint": str(source / "checkpoint.state"), "samples": [], "window_actions": [], "captures": []}
    evidence.update({"target_label":sample["label"],"corpus_sha256":EXPECTED,"strokes":gesture,"visual":visual,"legacy_v":args.legacy_v})
    evidence["activation"] = {name: environment[name] for name in ("NDS_BRAINAGE_CUSTOM_EXERCISE", "NDS_BRAINAGE_NATIVE_PRESENTATION", "NDS_BRAINAGE_CUSTOM_EXERCISE_ID", "NDS_TASK_J_CUSTOM_EXERCISE_PROBE", "NDS_TASK_N_DS_PRESENTATION") if name in environment}
    evidence["sdl_render_driver"] = environment.get("NDS_SDL_RENDER_DRIVER", "default")
    (root / "session.json").write_text(json.dumps(evidence, indent=2) + "\n")
    with (root / "stdout.log").open("wb") as stdout, (root / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, cwd=repository, env=environment, stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
    evidence["pid"] = process.pid
    print(f"Task W sample {args.sample} SDL PID {process.pid}", flush=True)
    connection = None

    def helper(action, *arguments):
        result = subprocess.run([str(repository / "build/task-o-tools/window_probe.exe"), action, str(process.pid), command[0], *map(str, arguments)], capture_output=True, text=True, timeout=10)
        if result.returncode:
            raise RuntimeError(f"Win32 {action}: {result.stderr.strip()}")
        metadata = json.loads(result.stdout)
        metadata["host_monotonic"] = time.monotonic()
        evidence["window_actions"].append(metadata)
        return metadata

    def request(payload):
        wire.write(json.dumps(payload).encode() + b"\n")
        wire.flush()
        line = wire.readline()
        if not line:
            raise RuntimeError("runner debug connection closed")
        response = json.loads(line)
        assert "error" not in response, response
        return response

    def context(label):
        state = {"label": label, "globals": {}}
        for name, address in (("current", 0x020DA464), ("requested", 0x020DA3EC), ("selected", 0x020DA3F0), ("menu", 0x020DA420)):
            state["globals"][name] = int.from_bytes(bytes.fromhex(request({"cmd": "read_mem", "addr": address, "len": 4})["hex"]), "little")
        state["force_tier3"] = request({"cmd": "force_tier3"})
        state["counts"] = request({"cmd": "event_counts"})
        state["touch"] = request({"cmd": "touch_state"})
        state["frontend"] = request({"cmd": "frontend_stats"})
        image = bytes.fromhex(request({"cmd": "cart_save"})["hex"])
        state["save_sha256"] = digest(image)
        (root / f"{label}.sav").write_bytes(image)
        assert digest(image) == H0 and not (root / "requests.jsonl").stat().st_size and not (root / "flash.jsonl").stat().st_size
        evidence["samples"].append(state)
        return state

    def control(action, name=None):
        assert action in ("sample", "capture")
        state = rows(root / "native-probe.jsonl")[-1]
        number = state["control_sequence"] + 1
        temporary = root / "native-control.next"
        temporary.write_text(f"{state['session']} {number} {action}{' ' + name if name else ''}\n")
        temporary.replace(root / "native-control.txt")
        terminal = "held_sample" if action == "sample" else "capture_complete"
        result = wait_for(lambda: next((row for row in rows(root / "native-probe.jsonl") if row["event"] == terminal and row["action_sequence"] == number), None))
        evidence["samples"].append(result)
        return result

    def capture(label, expected=None):
        trials = []
        for attempt, method in enumerate(("print",) * 12 + ("screen",)):
            suffix = method if attempt == 0 else f"{method}-{attempt}"
            output = root / f"window-{label}-{suffix}.bmp"
            metadata = helper("capture", output, method)
            bitmap = output.read_bytes()
            offset = struct.unpack_from("<I", bitmap, 10)[0]
            width, height = struct.unpack_from("<ii", bitmap, 18)
            assert (width, height) == (512, -768), (width, height)
            bgra = bitmap[offset:]
            image = bytearray(width * -height * 3)
            image[0::3], image[1::3], image[2::3] = bgra[2::4], bgra[1::4], bgra[0::4]
            bottom = image[384 * width * 3:]
            pixels = b"".join(bottom[(row * 2 * width + column * 2) * 3:(row * 2 * width + column * 2) * 3 + 3] for row in range(192) for column in range(256))
            measured = {"label": label, "method": method, "path": str(output), "window": metadata,
                "full_rgb_sha256": digest(image), "bottom_rgb_sha1": hashlib.sha1(pixels).hexdigest(),
                "bottom_rgb_sha256": digest(pixels), "distinct_colors": len(set(zip(pixels[0::3], pixels[1::3], pixels[2::3]))),
                "top_rgb_sha256": digest(image[:384 * width * 3])}
            measured["matches_readback"] = expected is not None and measured["bottom_rgb_sha1"] == expected
            trials.append(measured)
            if measured["matches_readback"] or (expected is None and measured["distinct_colors"] > 8):
                write_frame(root / f"window-{label}-bottom.png", {"w": 256, "h": 192, "rgb": pixels.hex()})
                evidence["captures"].append({"label": label, "trials": trials, "chosen": measured})
                return measured
            if method == "print":
                time.sleep(0.25)
        raise RuntimeError("actual window pixels do not match expected presentation")

    def click(ds_x, ds_y, label):
        nonlocal queue_sequence
        if args.input_source == "sdl-queue":
            metadata = helper("observe")
            assert metadata["client"] == [512, 768]
            client_x, client_y = ds_x * 2, (192 + ds_y) * 2
            metadata.update({"label": label, "source": "sdl_queue", "client_point": [client_x, client_y],
                "screen_point": [metadata["origin"][0] + client_x, metadata["origin"][1] + client_y],
                "screen_point_used_for_OS_input": False, "expected_ds": [ds_x, ds_y]})
            for down in (1, 0):
                queue_sequence += 1
                temporary = root / "window-control.next"
                temporary.write_text(f"{queue_token} {queue_sequence} {down} {client_x} {client_y}\n")
                temporary.replace(root / "window-control.txt")
                wait_for(lambda: any(row["event"] == "sdl_queue_button" and row["control_sequence"] == queue_sequence for row in rows(root / "frontend-input.jsonl")))
                time.sleep(0.6 if label in ("normal_back","select_x20") else 0.12)
            return metadata
        metadata = helper("click", ds_x * 2, (192 + ds_y) * 2)
        metadata.update({"label": label, "expected_ds": [ds_x, ds_y]})
        return metadata

    def stroke(points, index):
        nonlocal queue_sequence
        events = [(1, points[0]), *[(2, point) for point in points[1:]], (0, points[-1])]
        for event_index, (kind, point) in enumerate(events):
            metadata = helper("observe")
            assert metadata["client"] == [512, 768]
            client = (point[0] * 2, (192 + point[1]) * 2)
            queue_sequence += 1
            temporary = root / "window-control.next"
            temporary.write_text(f"{queue_token} {queue_sequence} {kind} {client[0]} {client[1]}\n")
            temporary.replace(root / "window-control.txt")
            event_name = "sdl_queue_motion" if kind == 2 else "sdl_queue_button"
            wait_for(lambda: any(row["event"] == event_name and row["control_sequence"] == queue_sequence for row in rows(root / "frontend-input.jsonl")))
            time.sleep(0.12)
            sample = control("sample")
            metrics = sample["exercise_metrics"]
            assert sample["exercise_id"] == exercise_id and sample["native_contact"] == (kind != 0)
            assert metrics["completed_strokes"] == (index if kind == 0 else index - 1)
            assert metrics["point_count"] == sum(len(s) for s in gesture[:index-1]) + min(event_index + 1, len(points))
            assert metrics["current_points"] == (0 if kind == 0 else event_index + 1)
            evidence.setdefault("drawing_events", []).append({"stroke": index, "kind": "motion" if kind == 2 else "down" if kind else "up",
                "control_sequence": queue_sequence, "client": client, "requested_ds": point, "source": "sdl-queue", "metrics": metrics})

    try:
        def connect():
            if process.poll() is not None:
                raise RuntimeError("runner exited during startup; inspect stderr")
            try:
                return socket.create_connection(("127.0.0.1", args.port), timeout=1)
            except OSError:
                return None
        connection = wait_for(connect)
        connection.settimeout(15)
        wire = connection.makefile("rwb")
        time.sleep(1)
        helper("observe")
        if args.brainage_host:
            helper("expose")
        if not args.observe_only and args.input_source == "win32-sendinput":
            helper("place")
        menu = context("menu")
        assert menu["globals"]["current"] == menu["globals"]["requested"] == 0x32
        assert not menu["force_tier3"]["forced_tier3"]
        if args.brainage_host:
            time.sleep(2)
            frame = request({"cmd": "framebuffer", "engine": "B"})
            write_frame(root / "menu-readback.png", frame)
            evidence["menu_readback_sha1"] = hashlib.sha1(bytes.fromhex(frame["rgb"])).hexdigest()
        else:
            capture("menu")
        if args.observe_only:
            evidence["close"] = request({"cmd": "frontend_exit"})
            evidence["exit_code"] = process.wait(timeout=20)
            assert evidence["exit_code"] == 0
            evidence["observe_only"] = True
            return
        click(166, 75, "select_x20")
        if args.disabled_control:
            wait_for(lambda: int.from_bytes(bytes.fromhex(request({"cmd":"read_mem","addr":0x020DA464,"len":4})["hex"]),"little")==0x41, seconds=60)
            rules = context("disabled-rules")
            assert rules["globals"]["current"] == rules["globals"]["requested"] == 0x41
            frame = request({"cmd": "framebuffer", "engine": "B"})
            capture("disabled-rules", hashlib.sha1(bytes.fromhex(frame["rgb"])).hexdigest())
            native = rows(root / "native-probe.jsonl")
            assert any(row["event"] == "boundary_disabled" for row in native)
            assert not any(row["event"] == "intercept" or row["exercise_present"] or row["render_count"] or row["touch_owner"] or row["frontend_hold_presents"] for row in native)
            evidence["close"] = request({"cmd": "frontend_exit"})
            evidence["exit_code"] = process.wait(timeout=20)
            assert evidence["exit_code"] == 0
            evidence["disabled_control_pass"] = True
            return
        wait_for(lambda: any(row["event"] == "panel_active" for row in rows(root / "native-probe.jsonl")))
        initial = control("capture", "initial") if visual else control("sample")
        if visual: capture("initial", initial["native_sha1"])
        for index, points in enumerate(gesture, 1):
            stroke(points, index)
            phase=control("capture", f"stroke{index}") if visual else control("sample")
            if visual: capture(f"stroke{index}", phase["native_sha1"])
            assert phase["exercise_metrics"]["recognition_success"] and not phase["exercise_metrics"]["recognition_error"]
            assert not phase["native_contact"]
            if not args.legacy_v: assert phase["continue_available"]
            evidence.setdefault("stroke_results",[]).append({"stroke":index-1,"phase":phase["phase"],**phase["exercise_metrics"]})
        completed = control("sample")
        assert completed["completed"] and completed["continue_available"]
        frozen_keys = ("current", "requested", "selected", "cpu_cycles", "system_cycles", "cycles7", "insn9", "insn7", "r", "flash_sha1", "guest_top_sha1", "guest_bottom_sha1", "video_sha1", "guest_touch_deliveries")
        invariant = {key: initial[key] for key in frozen_keys}
        assert all({key: row[key] for key in frozen_keys} == invariant for row in rows(root / "native-probe.jsonl"))
        assert initial["backend"] == "compiled" and not initial["forced_tier3"]
        evidence["frozen_invariant"] = invariant
        entries = rows(root / "entries.jsonl")
        assert len(entries) == 1 and entries[0]["kind"] == "lifecycle", entries
        click(128, 166, "continue")
        wait_for(lambda: any(row["event"] == "continue_original" for row in rows(root / "native-probe.jsonl")))
        wait_for(lambda: int.from_bytes(bytes.fromhex(request({"cmd":"read_mem","addr":0x020DA464,"len":4})["hex"]),"little")==0x41,seconds=60)
        rules = context("rules")
        assert (rules["globals"]["current"], rules["globals"]["requested"], rules["globals"]["selected"]) == (0x41,0x41,0x11)
        entries=rows(root / "entries.jsonl")
        evidence["rules_entries"]=entries
        assert sum(row["kind"]=="rules_initializer" for row in entries)==1
        assert not any(row["kind"]=="calculation_constructor" for row in entries)
        if args.handoff_visual:
            def visible_guest():
                image=request({"cmd":"framebuffer","engine":"B"});data=bytes.fromhex(image["rgb"])
                return image if len(set(zip(data[0::3],data[1::3],data[2::3])))>8 else None
            frame=wait_for(visible_guest,seconds=60)
            capture("rules",hashlib.sha1(bytes.fromhex(frame["rgb"])).hexdigest())
            time.sleep(1)
            click(240,32,"normal_back")
            wait_for(lambda: int.from_bytes(bytes.fromhex(request({"cmd":"read_mem","addr":0x020DA464,"len":4})["hex"]),"little")==0x32,seconds=45)
            returned=context("returned-menu")
            assert returned["globals"]["current"]==returned["globals"]["requested"]==0x32
            wait_for(visible_guest,seconds=45);time.sleep(2)
            frame=request({"cmd":"framebuffer","engine":"B"})
            capture("returned-menu",hashlib.sha1(bytes.fromhex(frame["rgb"])).hexdigest())
        evidence["close"] = request({"cmd": "frontend_exit"})
        evidence["exit_code"] = process.wait(timeout=20)
        assert evidence["exit_code"] == 0
        evidence["pass"] = True
    except Exception as error:
        evidence["failure"] = str(error)
        raise
    finally:
        if connection is not None:
            connection.close()
        if process.poll() is None:
            evidence["forced_cleanup"] = True
            process.terminate()
            process.wait(timeout=10)
        final = (root / "session.sav").read_bytes()
        evidence["final_sha256"] = digest(final)
        evidence["changed_bytes"] = sum(before != after for before, after in zip((root / "initial.sav").read_bytes(), final))
        evidence["trace_lines"] = {name: len(rows(root / name)) for name in ("flash.jsonl", "requests.jsonl")}
        (root / "result.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"PASS: frozen SDL input, isolated service, clean handoff; visual captures={len(evidence['captures'])}", flush=True)


if __name__ == "__main__":
    main()
