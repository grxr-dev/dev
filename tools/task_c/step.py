"""Monitor one normal input/wait and latch the first post-marker save operation."""

import argparse
import json
from pathlib import Path
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_a"))
from probe_boot import MARKER, write_frame
from route_marker import digest, ranges
from digits import pen_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--cycles", type=int, default=67000000)
    parser.add_argument("--tap", type=int, nargs=2)
    parser.add_argument("--answer")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--finish-candidate", action="store_true")
    parser.add_argument("--savestate", action="store_true")
    args = parser.parse_args()
    assert not (args.tap and args.answer), "choose one normal input"
    root = args.out.resolve()
    session = json.loads((root / "session.json").read_text())
    assert session["marker"] and session["marker"]["transaction_complete"]
    if args.baseline:
        assert args.cycles == 0 and args.tap is None
        assert "task_c" not in session, "baseline already established"
        session["task_c"] = {"request_position": 0, "request_sequence": 0,
                             "request_count": 0, "latest_request": None, "candidate": None}
    monitor = session["task_c"]
    if monitor["candidate"] and (args.tap or args.answer or args.cycles) and not args.finish_candidate:
        raise SystemExit("Candidate latched; no further gameplay input/progression allowed")
    if args.finish_candidate:
        assert monitor["candidate"] and args.tap is None and args.answer is None, "only drain the existing operation"
    checkpoint = root / args.label
    checkpoint.mkdir(exist_ok=False)
    before = (root / "ledger.sav").read_bytes()
    ledger = bytearray(before)
    flash_events, logical_events = [], []
    sequence_before = session["sequence"]
    requests_before = monitor["request_count"]
    with socket.create_connection(("127.0.0.1", session["port"]), timeout=120) as connection, (checkpoint / "debug.jsonl").open("w") as debug:
        wire = connection.makefile("rwb")

        def request(payload, allow_error=False):
            wire.write(json.dumps(payload).encode() + b"\n")
            wire.flush()
            response = json.loads(wire.readline())
            debug.write(json.dumps({"request": payload, "response": response}) + "\n")
            debug.flush()
            if "error" in response and not allow_error:
                raise RuntimeError(response["error"])
            return response

        def frames(prefix):
            for engine in ("A", "B"):
                frame = request({"cmd": "framebuffer", "engine": engine})
                write_frame(checkpoint / f"{prefix}-{engine}.png", frame)
                width, height = frame["w"], frame["h"]
                pixels = bytes.fromhex(frame["rgb"])
                rotated = b"".join(pixels[(column * width + width - 1 - row) * 3:
                                         (column * width + width - 1 - row) * 3 + 3]
                                   for row in range(width) for column in range(height))
                write_frame(checkpoint / f"{prefix}-{engine}-book.png",
                            {"w": height, "h": width, "rgb": rotated.hex()})

        def consume():
            with (root / "requests.jsonl").open("rb") as trace:
                trace.seek(monitor["request_position"])
                for line in trace:
                    event = json.loads(line)
                    assert event["sequence"] == monitor["request_sequence"] + 1
                    monitor["request_sequence"] = event["sequence"]
                    logical_events.append(event)
                    if event["kind"] == "submit":
                        monitor["request_count"] += 1
                        monitor["latest_request"] = event
                        if not args.baseline and monitor["candidate"] is None:
                            monitor["candidate"] = {"label": args.label, "request": event,
                                                     "committed_offsets": [], "complete": False}
                monitor["request_position"] = trace.tell()
            with (root / "flash.jsonl").open("rb") as trace:
                trace.seek(session["trace_position"])
                for line in trace:
                    event = json.loads(line)
                    assert event["sequence"] == session["sequence"] + 1
                    session["sequence"] = event["sequence"]
                    old, new = bytes.fromhex(event["old_hex"]), bytes.fromhex(event["new_hex"])
                    assert len(old) == len(new) == event["length"]
                    for index, value in enumerate(new):
                        offset = (event["offset"] + index) & event["wrap_mask"]
                        assert ledger[offset] == old[index]
                        ledger[offset] = value
                        candidate = monitor["candidate"]
                        if candidate and candidate.get("request"):
                            submitted = candidate["request"]
                            if submitted["offset"] <= offset < submitted["offset"] + submitted["length"]:
                                candidate["committed_offsets"].append(offset)
                    flash_events.append(event)
                    if not args.baseline and monitor["candidate"] is None:
                        monitor["candidate"] = {"label": args.label, "unmatched_flash": event, "complete": event["last"]}
                session["trace_position"] = trace.tell()
            candidate = monitor["candidate"]
            if candidate and candidate.get("request"):
                submitted = candidate["request"]
                candidate["committed_offsets"] = sorted(set(candidate["committed_offsets"]))
                candidate["complete"] = len(candidate["committed_offsets"]) == submitted["length"]

        initial = request({"cmd": "io_state"})
        assert bytes.fromhex(request({"cmd": "cart_save"})["hex"]) == before
        frames("before")
        consume()
        if args.baseline:
            assert ledger.find(MARKER) == 0x180
            monitor["baseline_request_count"] = monitor["request_count"]
            monitor["baseline_flash_sequence"] = session["sequence"]
        current = initial["counts"]["cyc9"]
        target = current + args.cycles
        release = current + 3000000
        pressed = args.tap is not None
        if pressed:
            request({"cmd": "touch", "x": args.tap[0], "y": args.tap[1], "down": True})
        if args.answer:
            for stroke in pen_paths(args.answer):
                if monitor["candidate"]:
                    break
                for horizontal, vertical in stroke:
                    if monitor["candidate"]:
                        break
                    request({"cmd": "touch", "x": horizontal, "y": vertical, "down": True})
                    point_target = current + 2000000
                    while current < point_target and not monitor["candidate"]:
                        response = request({"cmd": "run_cycles", "arm9": min(current + 100000, point_target)})
                        if not response["reached"]:
                            response = request({"cmd": "run_rounds", "count": 2048})
                        current = response["cycles"][0]
                        consume()
                request({"cmd": "touch", "down": False})
                if not monitor["candidate"]:
                    response = request({"cmd": "run_cycles", "arm9": current + 3000000})
                    if not response["reached"]:
                        response = request({"cmd": "run_rounds", "count": 2048})
                    current = response["cycles"][0]
                    consume()
        while current < target:
            candidate = monitor["candidate"]
            if candidate and (not args.finish_candidate or candidate["complete"]):
                break
            response = request({"cmd": "run_cycles", "arm9": min(current + 100000, target)})
            if not response["reached"]:
                advanced = request({"cmd": "run_rounds", "count": 2048})
                if advanced["cycles"] == response["cycles"]:
                    raise RuntimeError("scheduler made no progress")
                current = advanced["cycles"][0]
            else:
                current = response["cycles"][0]
            consume()
            if pressed and current >= release:
                request({"cmd": "touch", "down": False})
                pressed = False
        if pressed:
            request({"cmd": "touch", "down": False})
        consume()
        final = request({"cmd": "io_state"})
        after = bytes.fromhex(request({"cmd": "cart_save"})["hex"])
        assert bytes(ledger) == after, "trace replay differs from live Flash"
        frames("after")
        state_result = request({"cmd": "state_save", "path": str(checkpoint / "checkpoint.state")}, True) if args.savestate else None
    changed, spans = ranges(before, after)
    summary = {"label": args.label, "tap": args.tap, "answer": args.answer, "requested_cycles": args.cycles,
               "initial": initial, "final": final, "save_sha256_before": digest(before),
               "save_sha256_after": digest(after), "changed_bytes": changed,
               "changed_ranges_half_open": spans, "sequence_before": sequence_before,
               "sequence_after": session["sequence"], "requests_before": requests_before,
               "requests_after": monitor["request_count"], "latest_request": monitor["latest_request"],
               "candidate": monitor["candidate"], "marker_offset": after.find(MARKER),
               "replay_matches_live": True, "live_matches_persisted": after == (root / "erased.sav").read_bytes(),
               "savestate_result": state_result}
    (checkpoint / "before.sav").write_bytes(before)
    (checkpoint / "after.sav").write_bytes(after)
    (checkpoint / "flash.jsonl").write_text("".join(json.dumps(event) + "\n" for event in flash_events))
    (checkpoint / "requests.jsonl").write_text("".join(json.dumps(event) + "\n" for event in logical_events))
    (checkpoint / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (root / "ledger.sav").write_bytes(after)
    session["checkpoints"].append(args.label)
    (root / "session.json").write_text(json.dumps(session, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in ("label", "changed_bytes", "sequence_after", "requests_after", "marker_offset", "candidate", "save_sha256_after", "savestate_result")}, indent=2))
    print("cycles:", final["counts"]["cyc9"], final["counts"]["cyc7"])


if __name__ == "__main__":
    main()
