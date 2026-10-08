"""Boot an erased Flash image and stop after the marker's completed SPI transfer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import struct
import time
import zlib

ROM_SHA1 = "b8a105bacc3234dede8d4465df0869f2b922a0e2"
MARKER = b"CLEAR-RAM-CHECK"


def write_frame(path: Path, frame: dict) -> None:
    width, height = frame["w"], frame["h"]
    rgb = bytes.fromhex(frame["rgb"])
    if len(rgb) != width * height * 3:
        raise RuntimeError("framebuffer size mismatch")
    scanlines = b"".join(b"\0" + rgb[row * width * 3:(row + 1) * width * 3] for row in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b""))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/brainage_task_a.toml"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=19852)
    parser.add_argument("--force-tier3", action="store_true")
    parser.add_argument("--checkpoint", action="store_true")
    parser.add_argument("--chunk-cycles", type=int, default=1000000)
    parser.add_argument("--max-cycles", type=int, default=2000000000)
    args = parser.parse_args()
    if hashlib.sha1(args.rom.read_bytes()).hexdigest() != ROM_SHA1:
        raise SystemExit("ROM SHA-1 mismatch")
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    save = output / "erased.sav"
    save.write_bytes(b"\xff" * 262144)
    trace = output / "flash.jsonl"
    environment = os.environ.copy()
    environment["NDS_FLASH_TRACE"] = str(trace)
    command = [str(args.runner.resolve()), str(output), "--serve", "--port", str(args.port),
               "--rom", str(args.rom.resolve()), "--config", str(args.config.resolve()),
               "--save-path", str(save), "--boot", "direct", "--freebios",
               "--generated-firmware", "--identity-mac", "02:00:00:00:00:01",
               "--diagnostics", "off", "--no-coverage-manifest", "--network", "off"]
    if args.force_tier3:
        command.append("--force-tier3")
    ledger = bytearray(b"\xff" * 262144)
    marker_transaction = None
    marker_offset = None
    records = []
    completed = False
    responses = []
    with (output / "stdout.log").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=environment,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            connection = None
            for attempt in range(100):
                if process.poll() is not None:
                    raise RuntimeError(f"runner exited during boot: {process.returncode}; see {output / 'stderr.log'}")
                try:
                    connection = socket.create_connection(("127.0.0.1", args.port), timeout=1)
                    break
                except OSError:
                    time.sleep(0.1)
            if connection is None:
                raise RuntimeError("debug server did not start")
            with connection:
                connection.settimeout(60)
                wire = connection.makefile("rwb")

                def request(payload: dict) -> dict:
                    wire.write(json.dumps(payload).encode() + b"\n")
                    wire.flush()
                    line = wire.readline()
                    if not line:
                        raise RuntimeError("debug connection closed")
                    response = json.loads(line)
                    responses.append({"request": payload, "response": response})
                    if "error" in response:
                        raise RuntimeError(response["error"])
                    return response

                request({"cmd": "ping"})
                position = 0
                for target in range(args.chunk_cycles, args.max_cycles + 1, args.chunk_cycles):
                    response = request({"cmd": "run_cycles", "arm9": target})
                    while not response.get("reached"):
                        previous_cycles = response["cycles"]
                        advanced = request({"cmd": "run_rounds", "count": 65536})
                        if advanced["cycles"][0] == previous_cycles[0]:
                            break
                        response = request({"cmd": "run_cycles", "arm9": target})
                    if trace.exists():
                        with trace.open("rb") as stream:
                            stream.seek(position)
                            while True:
                                start = stream.tell()
                                line = stream.readline()
                                if not line.endswith(b"\n"):
                                    position = start
                                    break
                                event = json.loads(line)
                                if event["sequence"] != len(records) + 1:
                                    raise RuntimeError("non-contiguous Flash sequence")
                                previous = bytes.fromhex(event["old_hex"])
                                committed = bytes.fromhex(event["new_hex"])
                                if len(previous) != event["length"] or len(committed) != event["length"]:
                                    raise RuntimeError("Flash length mismatch")
                                for index, value in enumerate(committed):
                                    address = (event["offset"] + index) & event["wrap_mask"]
                                    if ledger[address] != previous[index]:
                                        raise RuntimeError(f"old-byte mismatch at {address:#x}")
                                    ledger[address] = value
                                records.append(event)
                                if marker_transaction is None:
                                    found = ledger.find(MARKER)
                                    if found >= 0:
                                        marker_transaction = event["transaction"]
                                        marker_offset = found
                                if event["transaction"] == marker_transaction and event["last"]:
                                    completed = True
                    if completed:
                        request({"cmd": "io_state"})
                        break
                    if not response.get("reached"):
                        state = request({"cmd": "io_state"})
                        request({"cmd": "regs", "cpu": 9})
                        request({"cmd": "regs", "cpu": 7})
                        raise RuntimeError(f"runner stopped advancing before marker: {response}; state={state}")
                    if target % 10000000 == 0:
                        print(f"arm9 target={target}, Flash records={len(records)}", flush=True)
                if args.checkpoint:
                    request({"cmd": "state_save", "path": str(output / "boot.state")})
                    request({"cmd": "regs", "cpu": 9})
                    request({"cmd": "regs", "cpu": 7})
                    request({"cmd": "read_mem", "cpu": 7, "addr": 0x038032B8, "len": 4})
                    for engine in ("A", "B"):
                        write_frame(output / f"engine-{engine}.png", request({"cmd": "framebuffer", "engine": engine}))
                request({"cmd": "io_state"})
        finally:
            (output / "debug-responses.json").write_text(json.dumps(responses, indent=2) + "\n")
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)
    (output / "debug-responses.json").write_text(json.dumps(responses, indent=2) + "\n")
    (output / "replayed.sav").write_bytes(ledger)
    relevant = [event for event in records if marker_offset is not None and any(
        marker_offset <= ((event["offset"] + index) & event["wrap_mask"]) < marker_offset + len(MARKER)
        for index in range(event["length"]))]
    (output / "marker-sequence.json").write_text(json.dumps(relevant, indent=2) + "\n")
    persisted = save.read_bytes()
    summary = {"marker_completed": completed, "marker_offset": marker_offset,
               "marker_transaction": marker_transaction, "records": len(records),
               "marker_records": len(relevant), "save_marker_offset": persisted.find(MARKER),
               "persisted_matches_ledger": persisted == ledger,
               "final_cycles": [responses[-1]["response"]["counts"]["cyc9"], responses[-1]["response"]["counts"]["cyc7"]],
               "save_sha1": hashlib.sha1(persisted).hexdigest(),
               "command": command, "trace": str(trace)}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)
    return 0 if completed and persisted.find(MARKER) == marker_offset else 1


if __name__ == "__main__":
    raise SystemExit(main())
