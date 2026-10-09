"""Capture one bounded Task E tap/wait without Task D's first-page stop."""

import argparse
import json
from pathlib import Path
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_a"))
from probe_boot import write_frame
from route_marker import digest, ranges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--cycles", type=int, default=200000000)
    parser.add_argument("--tap", type=int, nargs=2)
    parser.add_argument("--savestate", action="store_true")
    args = parser.parse_args()
    assert args.cycles >= 0
    root = args.out.resolve()
    session = json.loads((root / "session.json").read_text())
    monitor = session.setdefault("task_e", {"request_position": 0, "request_sequence": 0,
                                           "flash_position": 0, "flash_sequence": 0, "tap_count": 0})
    if args.tap:
        assert monitor["tap_count"] == 0, "only one Task E tap per capture session"
        assert 0 <= args.tap[0] <= 255 and 0 <= args.tap[1] <= 191
    checkpoint = root / args.label
    checkpoint.mkdir(exist_ok=False)
    before = (root / "ledger.sav").read_bytes()
    ledger = bytearray(before)
    logical_events, flash_events = [], []
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
            for name, position, sequence, events in (
                ("requests.jsonl", "request_position", "request_sequence", logical_events),
                ("flash.jsonl", "flash_position", "flash_sequence", flash_events),
            ):
                with (root / name).open("rb") as trace:
                    trace.seek(monitor[position])
                    for line in trace:
                        event = json.loads(line)
                        assert event["sequence"] == monitor[sequence] + 1
                        monitor[sequence] = event["sequence"]
                        events.append(event)
                        if name == "flash.jsonl":
                            old, new = bytes.fromhex(event["old_hex"]), bytes.fromhex(event["new_hex"])
                            assert len(old) == len(new) == event["length"]
                            for index, value in enumerate(new):
                                offset = (event["offset"] + index) & event["wrap_mask"]
                                assert ledger[offset] == old[index], "Flash old byte differs from replay"
                                ledger[offset] = value
                    monitor[position] = trace.tell()

        initial = request({"cmd": "io_state"})
        assert bytes.fromhex(request({"cmd": "cart_save"})["hex"]) == before
        frames("before")
        consume()
        current = initial["counts"]["cyc9"]
        target, release = current + args.cycles, current + 3000000
        pressed = args.tap is not None
        if pressed:
            monitor["tap_count"] += 1
            request({"cmd": "touch", "x": args.tap[0], "y": args.tap[1], "down": True})
        while current < target:
            response = request({"cmd": "run_cycles", "arm9": min(current + 1000000, target)})
            if not response["reached"]:
                advanced = request({"cmd": "run_rounds", "count": 2048})
                if advanced["cycles"] == response["cycles"]:
                    raise RuntimeError("scheduler made no progress")
                response = advanced
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
        assert bytes(ledger) == after, "Flash replay differs from live image"
        save_info = request({"cmd": "cart_save_info"})
        shared = request({"cmd": "read_mem", "cpu": 9, "addr": 0x020d4ce0, "len": 32})
        frames("after")
        state_result = request({"cmd": "state_save", "path": str(checkpoint / "checkpoint.state")}, True) if args.savestate else None
    changed, spans = ranges(before, after)
    event_times = [event["system_cycles"] for event in logical_events]
    event_times += [event["byte_origin"]["system_cycles"] for event in flash_events]
    summary = {"label": args.label, "tap": args.tap, "requested_cycles": args.cycles,
               "initial": initial, "final": final, "save_sha256_before": digest(before),
               "save_sha256_after": digest(after), "changed_bytes": changed,
               "changed_ranges_half_open": spans, "api_operations": sum(event["kind"] == "write_api" for event in logical_events),
               "submissions": sum(event["kind"] == "submit" for event in logical_events),
               "commit_events": len(flash_events), "accepted_bytes": sum(event["length"] for event in flash_events),
               "changed_byte_commits": sum(event["changed_bytes"] for event in flash_events),
               "transactions": sorted({event["transaction"] for event in flash_events}),
               "last_event_system_cycle": max(event_times) if event_times else None,
               "marker_offset": after.find(b"CLEAR-RAM-CHECK"), "save_info": save_info,
               "shared_request": shared, "replay_matches_live": True,
               "live_matches_disk": after == (root / "erased.sav").read_bytes(), "savestate_result": state_result}
    (checkpoint / "before.sav").write_bytes(before)
    (checkpoint / "after.sav").write_bytes(after)
    (checkpoint / "flash.jsonl").write_text("".join(json.dumps(event) + "\n" for event in flash_events))
    (checkpoint / "requests.jsonl").write_text("".join(json.dumps(event) + "\n" for event in logical_events))
    (checkpoint / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (root / "ledger.sav").write_bytes(after)
    session["checkpoints"].append(args.label)
    (root / "session.json").write_text(json.dumps(session, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in ("label", "api_operations", "submissions", "accepted_bytes", "changed_bytes", "save_sha256_after", "last_event_system_cycle", "savestate_result")}, indent=2))
    print("cycles:", final["counts"]["cyc9"], final["counts"]["cyc7"])


if __name__ == "__main__":
    main()
