"""Restore the verified January-2 Task F checkpoint into a new, isolated capture session."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=19855)
    args = parser.parse_args()
    source, root = args.source.resolve(), args.out.resolve()
    previous = json.loads((source.parent / "session.json").read_text())
    summary = json.loads((source / "summary.json").read_text())
    image = (source / "after.sav").read_bytes()
    assert len(image) == 262144 and image.find(b"CLEAR-RAM-CHECK") == 0x180
    assert hashlib.sha256(image).hexdigest() == summary["save_sha256_after"]
    assert summary["savestate_result"] == {"ok": True}
    assert summary["accepted_bytes"] == summary["api_operations"] == 0
    assert summary["save_sha256_after"] == "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"
    command = list(previous["command"])
    rom = Path(command[command.index("--rom") + 1])
    assert hashlib.sha1(rom.read_bytes()).hexdigest() == "b8a105bacc3234dede8d4465df0869f2b922a0e2"
    root.mkdir(parents=True, exist_ok=False)
    for name in ("erased.sav", "ledger.sav", "initial.sav"):
        (root / name).write_bytes(image)
    for name in ("flash.jsonl", "requests.jsonl"):
        (root / name).touch()
    command[1] = str(root)
    command[command.index("--port") + 1] = str(args.port)
    command[command.index("--save-path") + 1] = str(root / "erased.sav")
    environment = os.environ.copy()
    environment.pop("NDS_TASK_B_TRACE", None)
    environment["NDS_TASK_F_RTC_PLUS_ONE_DAY"] = "1"
    environment["NDS_FLASH_TRACE"] = str(root / "flash.jsonl")
    environment["NDS_TASK_C_TRACE"] = str(root / "requests.jsonl")
    with (root / "stdout.log").open("wb") as stdout, (root / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=environment,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    connection = None
    for attempt in range(100):
        if process.poll() is not None:
            raise RuntimeError("runner exited before restore; see stderr.log")
        try:
            connection = socket.create_connection(("127.0.0.1", args.port), timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    if connection is None:
        raise RuntimeError("debug server did not start")
    with connection:
        wire = connection.makefile("rwb")

        def request(payload):
            wire.write(json.dumps(payload).encode() + b"\n")
            wire.flush()
            response = json.loads(wire.readline())
            if "error" in response:
                raise RuntimeError(response["error"])
            return response

        loaded = request({"cmd": "state_load", "path": str(source / "checkpoint.state")})
        counts = request({"cmd": "io_state"})
        for field in ("cpu9", "cpu7", "cpu_stop"):
            assert counts[field] == summary["final"][field], f"restored {field} differs"
        for field in ("cyc9", "cyc7", "insn9", "insn7"):
            assert counts["counts"][field] == summary["final"]["counts"][field], f"restored {field} differs"
        rtc = request({"cmd": "rtc_state"})
        assert rtc == summary["rtc_after"], "restored RTC differs"
        actual = bytes.fromhex(request({"cmd": "cart_save"})["hex"])
        assert actual == image, "restored Flash differs from snapshot"
    session = {"pid": process.pid, "port": args.port, "command": command,
               "sequence": 0, "trace_position": 0, "marker": previous["marker"],
               "checkpoints": [], "recovery_source": str(source),
               "inherited_logical_event_count": previous["task_e"]["request_sequence"],
               "inherited_api_operation_count": sum(json.loads(line)["kind"] == "write_api"
                                                    for line in (source.parent / "requests.jsonl").read_text().splitlines())}
    (root / "session.json").write_text(json.dumps(session, indent=2) + "\n")
    evidence = {"source": str(source), "state_load": loaded, "io_state": counts, "rtc_state": rtc,
                "state_sha256": hashlib.sha256((source / "checkpoint.state").read_bytes()).hexdigest(),
                "save_sha256": hashlib.sha256(actual).hexdigest(), "marker_offset": actual.find(b"CLEAR-RAM-CHECK")}
    (root / "restore.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
