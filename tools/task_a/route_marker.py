"""Single-session, one-action checkpoints for the Task A.5 marker route."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time

from probe_boot import MARKER, ROM_SHA1, write_frame


def digest(data):
    return hashlib.sha256(data).hexdigest()


def ranges(before, after):
    changed = [offset for offset, values in enumerate(zip(before, after)) if values[0] != values[1]]
    spans = []
    for offset in changed:
        if spans and spans[-1][1] == offset:
            spans[-1][1] += 1
        else:
            spans.append([offset, offset + 1])
    return len(changed), spans


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--runner", type=Path)
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--config", type=Path, default=Path("config/brainage_task_a.toml"))
    parser.add_argument("--port", type=int, default=19853)
    parser.add_argument("--cycles", type=int, default=67000000)
    parser.add_argument("--tap", nargs=2, type=int)
    parser.add_argument("--key-mask", type=int)
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--savestate", action="store_true")
    parser.add_argument("--force-tier3", action="store_true")
    args = parser.parse_args()
    root = args.out.resolve()
    session_path = root / "session.json"
    if args.start:
        if not args.rom or not args.runner:
            parser.error("--start requires --rom and --runner")
        assert hashlib.sha1(args.rom.read_bytes()).hexdigest() == ROM_SHA1, "ROM SHA-1 mismatch"
        root.mkdir(parents=True, exist_ok=False)
        (root / "erased.sav").write_bytes(b"\xff" * 262144)
        (root / "ledger.sav").write_bytes(b"\xff" * 262144)
        environment = os.environ.copy()
        environment["NDS_FLASH_TRACE"] = str(root / "flash.jsonl")
        command = [str(args.runner.resolve()), str(root), "--serve", "--port", str(args.port),
                   "--rom", str(args.rom.resolve()), "--config", str(args.config.resolve()),
                   "--save-path", str(root / "erased.sav"), "--boot", "direct", "--freebios",
                   "--generated-firmware", "--identity-mac", "02:00:00:00:00:01",
                   "--diagnostics", "off", "--no-coverage-manifest", "--network", "off"]
        if args.force_tier3:
            command.append("--force-tier3")
        with (root / "stdout.log").open("wb") as stdout, (root / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(command, env=environment, stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        session = {"pid": process.pid, "port": args.port, "command": command, "sequence": 0,
                   "trace_position": 0, "checkpoints": [], "marker": None}
        session_path.write_text(json.dumps(session, indent=2))
    else:
        session = json.loads(session_path.read_text())
    if session["marker"] and args.cycles and not args.stop:
        raise SystemExit("Marker already found: no further progression allowed")
    checkpoint = root / args.label
    checkpoint.mkdir(exist_ok=False)
    before = (root / "ledger.sav").read_bytes()
    ledger = bytearray(before)
    events = []
    connection = None
    for attempt in range(100):
        try:
            connection = socket.create_connection(("127.0.0.1", session["port"]), timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    if connection is None:
        raise RuntimeError("debug server did not start")
    with connection, (checkpoint / "debug.jsonl").open("w") as debug:
        connection.settimeout(120)
        wire = connection.makefile("rwb")

        def request(payload, allow_error=False):
            wire.write(json.dumps(payload).encode() + b"\n")
            wire.flush()
            line = wire.readline()
            if not line:
                raise RuntimeError("debug connection closed")
            response = json.loads(line)
            debug.write(json.dumps({"request": payload, "response": response}) + "\n")
            debug.flush()
            if "error" in response and not allow_error:
                raise RuntimeError(response["error"])
            return response

        def consume_trace():
            if not (root / "flash.jsonl").exists():
                return
            with (root / "flash.jsonl").open("rb") as trace:
                trace.seek(session["trace_position"])
                for line in trace:
                    event = json.loads(line)
                    assert event["sequence"] == session["sequence"] + 1
                    old = bytes.fromhex(event["old_hex"])
                    new = bytes.fromhex(event["new_hex"])
                    assert len(old) == len(new) == event["length"]
                    for index, value in enumerate(new):
                        offset = (event["offset"] + index) & event["wrap_mask"]
                        assert ledger[offset] == old[index], f"old-byte mismatch: {offset:#x}"
                        ledger[offset] = value
                    events.append(event)
                    session["sequence"] = event["sequence"]
                    if session["marker"] is None and ledger.find(MARKER) >= 0:
                        session["marker"] = {"offset": ledger.find(MARKER), "first_event": event,
                                             "checkpoint": args.label, "transaction_complete": False}
                    if session["marker"] and event["transaction"] == session["marker"]["first_event"]["transaction"] and event["last"]:
                        session["marker"]["transaction_complete"] = True
                session["trace_position"] = trace.tell()

        initial = request({"cmd": "io_state"})
        start_cycles = initial["counts"]["cyc9"]
        target = start_cycles + args.cycles
        press_end = start_cycles + 3000000
        if args.tap:
            request({"cmd": "touch", "x": args.tap[0], "y": args.tap[1], "down": True})
        if args.key_mask is not None:
            request({"cmd": "keys", "mask": args.key_mask})
        pressed = bool(args.tap or args.key_mask is not None)
        current = start_cycles
        while current < target and not (session["marker"] and session["marker"]["transaction_complete"]):
            response = request({"cmd": "run_cycles", "arm9": min(current + 1000000, target)})
            if not response["reached"]:
                advanced = request({"cmd": "run_rounds", "count": 65536})
                if advanced["cycles"][0] == response["cycles"][0]:
                    raise RuntimeError("scheduler made no progress")
                current = advanced["cycles"][0]
            else:
                current = response["cycles"][0]
            consume_trace()
            if pressed and current >= press_end:
                request({"cmd": "touch", "down": False})
                request({"cmd": "keys", "mask": 1023})
                pressed = False
        if pressed:
            request({"cmd": "touch", "down": False})
            request({"cmd": "keys", "mask": 1023})
        consume_trace()
        final = request({"cmd": "io_state"})
        for engine in ("A", "B"):
            frame = request({"cmd": "framebuffer", "engine": engine})
            write_frame(checkpoint / f"engine-{engine}.png", frame)
        state_result = request({"cmd": "state_save", "path": str(checkpoint / "checkpoint.state")},
                               allow_error=True) if args.savestate else None
    after = bytes(ledger)
    count, spans = ranges(before, after)
    persisted = (root / "erased.sav").read_bytes()
    summary = {"label": args.label, "action": {"tap": args.tap, "key_mask": args.key_mask,
               "requested_cycles": args.cycles}, "initial": initial, "final": final,
               "save_sha256_before": digest(before), "save_sha256_after": digest(after),
               "changed_bytes": count, "changed_ranges_half_open": spans,
               "sequence_before": events[0]["sequence"] - 1 if events else session["sequence"],
               "sequence_after": session["sequence"], "marker_offset": after.find(MARKER),
               "marker": session["marker"], "replay_matches_persisted": after == persisted,
               "savestate_result": state_result}
    (checkpoint / "before.sav").write_bytes(before)
    (checkpoint / "after.sav").write_bytes(after)
    (checkpoint / "transition.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events))
    (checkpoint / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (root / "ledger.sav").write_bytes(after)
    session["checkpoints"].append(args.label)
    session_path.write_text(json.dumps(session, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in ("label", "save_sha256_before", "save_sha256_after",
          "changed_bytes", "sequence_before", "sequence_after", "marker_offset", "replay_matches_persisted")}, indent=2))
    print("cycles:", final["counts"]["cyc9"], final["counts"]["cyc7"])
    if args.stop:
        if os.name == "nt":
            import ctypes
            handle = ctypes.windll.kernel32.OpenProcess(1, False, session["pid"])
            if not handle:
                raise RuntimeError("cannot open this session's runner process")
            ctypes.windll.kernel32.TerminateProcess(handle, 0)
            ctypes.windll.kernel32.CloseHandle(handle)
        else:
            import signal
            os.kill(session["pid"], signal.SIGTERM)


if __name__ == "__main__":
    main()
