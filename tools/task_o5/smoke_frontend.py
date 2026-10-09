"""Observe ordinary SDL startup/readback and close via the existing SDL_QUIT diagnostic."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_a"))
from probe_boot import write_frame


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=19876)
    parser.add_argument("--seconds", type=float, default=20)
    args = parser.parse_args()
    if not 5 <= args.seconds <= 60:
        raise ValueError("smoke duration must be 5..60 host seconds")
    repository = Path(__file__).resolve().parents[2]
    root = args.out.resolve()
    if not root.is_relative_to(repository / "local/task-o5"):
        raise ValueError("smoke outputs must be under local/task-o5")
    previous = json.loads((repository / "local/task-n/normal-enabled-002/session.json").read_text())
    command = list(previous["command"])
    command[0] = str(repository / "build/task-o-sdl-runner/nds_runner.exe")
    command[1] = str(root)
    command[command.index("--serve")] = "--interactive"
    command[command.index("--port") + 1] = str(args.port)
    command[command.index("--save-path") + 1] = str(root / "smoke.sav")
    if "--force-tier3" in command:
        raise ValueError("unexpected forced-interpreter launch")
    rom = Path(command[command.index("--rom") + 1])
    if hashlib.sha1(rom.read_bytes()).hexdigest() != "b8a105bacc3234dede8d4465df0869f2b922a0e2":
        raise ValueError("ROM identity mismatch")
    image = (repository / "local/task-g/session-001/04-training-menu/after.sav").read_bytes()
    if hashlib.sha256(image).hexdigest() != "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb":
        raise ValueError("save identity mismatch")
    root.mkdir(parents=True, exist_ok=False)
    for name in ("initial.sav", "smoke.sav"):
        (root / name).write_bytes(image)
    environment = os.environ.copy()
    for name in list(environment):
        if name.startswith(("NDS_TASK_", "NDS_FRONTEND_")):
            environment.pop(name)
    environment.update({"NDS_TASK_J_CUSTOM_EXERCISE_PROBE": "0", "NDS_TASK_N_DS_PRESENTATION": "0",
                        "NDS_TASK_F_RTC_PLUS_ONE_DAY": "1", "NDS_FRAME_HASH": "1",
                        "NDS_FRONTEND_MAX_FRAMES": "1800", "NDS_FRONTEND_STATS": "1",
                        "NDS_FLASH_TRACE": str(root / "flash.jsonl"),
                        "NDS_TASK_C_TRACE": str(root / "requests.jsonl")})
    for name in ("flash.jsonl", "requests.jsonl"):
        (root / name).touch()
    evidence = {"command": command, "custom_probe_enabled": False, "native_presentation_enabled": False,
                "checkpoint_restored": False, "guest_input_sent": False, "save_sha256_before": digest(root / "initial.sav"),
                "captures_source": "shared debug framebuffer, NOT an OS window screenshot", "samples": []}
    (root / "session.json").write_text(json.dumps(evidence, indent=2) + "\n")
    with (root / "stdout.log").open("wb") as stdout, (root / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, cwd=repository, env=environment, stdout=stdout, stderr=stderr,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
    evidence["pid"] = process.pid
    print(f"SDL smoke PID {process.pid}; no gameplay input", flush=True)
    connection = None
    try:
        for attempt in range(100):
            if process.poll() is not None:
                raise RuntimeError("runner exited before observation")
            try:
                connection = socket.create_connection(("127.0.0.1", args.port), timeout=2)
                connection.settimeout(15)
                break
            except OSError:
                time.sleep(0.1)
        if connection is None:
            raise RuntimeError("frontend debug server unavailable")
        wire = connection.makefile("rwb")

        def request(payload):
            wire.write(json.dumps(payload).encode() + b"\n")
            wire.flush()
            response = json.loads(wire.readline())
            if "error" in response:
                raise RuntimeError(response["error"])
            return response

        started = time.monotonic()
        for label, delay in (("initial", 2), ("settled", args.seconds)):
            time.sleep(max(0, started + delay - time.monotonic()))
            status = request({"cmd": "frontend_stats"})
            counts = request({"cmd": "event_counts"})
            metadata_command = (
                f"Get-Process -Id {process.pid} | Select-Object Id,Path,MainWindowTitle,"
                "@{Name='MainWindowHandle';Expression={$_.MainWindowHandle.ToInt64()}},Responding | ConvertTo-Json -Compress"
            )
            metadata = json.loads(subprocess.check_output(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", metadata_command], text=True))
            sample = {"label": label, "host_seconds": time.monotonic() - started,
                      "frontend_stats": status, "event_counts": counts, "process_window_metadata": metadata,
                      "frames": {}}
            for engine in ("A", "B"):
                frame = request({"cmd": "framebuffer", "engine": engine})
                write_frame(root / f"{label}-{engine}.png", frame)
                pixels = bytes.fromhex(frame["rgb"])
                sample["frames"][engine] = {"w": frame["w"], "h": frame["h"],
                    "rgb_sha256": hashlib.sha256(pixels).hexdigest(), "distinct_rgb_values": len(set(zip(pixels[0::3], pixels[1::3], pixels[2::3])))}
            evidence["samples"].append(sample)
            print(f"{label}: presented frames {status['frames']}; window {metadata['MainWindowHandle']}", flush=True)
        evidence["forced_tier3"] = request({"cmd": "force_tier3"})
        evidence["close_request"] = request({"cmd": "frontend_exit"})
        evidence["close_method"] = "existing frontend_exit -> SDL_QUIT"
        evidence["exit_code"] = process.wait(timeout=20)
    finally:
        if connection is not None:
            connection.close()
        if process.poll() is None:
            evidence["forced_cleanup"] = True
            process.terminate()
            process.wait(timeout=10)
        evidence["save_sha256_after"] = digest(root / "smoke.sav")
        evidence["changed_save_bytes"] = sum(before != after for before, after in zip(image, (root / "smoke.sav").read_bytes()))
        evidence["trace_lines"] = {name: len((root / name).read_text().splitlines()) for name in ("flash.jsonl", "requests.jsonl")}
        (root / "smoke-result.json").write_text(json.dumps(evidence, indent=2) + "\n")
    if evidence.get("forced_cleanup") or evidence.get("exit_code") != 0:
        raise RuntimeError("frontend did not close normally; inspect evidence")
    if not all(sample["frontend_stats"]["active"] and sample["process_window_metadata"]["MainWindowHandle"] for sample in evidence["samples"]):
        raise RuntimeError("frontend/window not observed")
    if evidence["samples"][1]["frontend_stats"]["frames"] <= evidence["samples"][0]["frontend_stats"]["frames"]:
        raise RuntimeError("frontend did not keep presenting")
    if evidence["save_sha256_after"] != evidence["save_sha256_before"] or any(evidence["trace_lines"].values()):
        raise RuntimeError("unexpected passive smoke save activity")
    print(json.dumps(evidence, indent=2), flush=True)


if __name__ == "__main__":
    main()
