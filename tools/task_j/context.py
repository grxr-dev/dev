"""Capture read-only scene, CPU and dispatch invariants while the runner is paused."""

import argparse
import json
from pathlib import Path
import re
import socket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    root = args.out.resolve()
    assert any(root.is_relative_to(Path(__file__).resolve().parents[2] / name) for name in ("local/task-j", "local/task-k"))
    assert re.fullmatch(r"[a-z0-9-]+", args.name)
    output = root / f"{args.name}-context.json"
    assert not output.exists()
    session = json.loads((root / "session.json").read_text())
    with socket.create_connection(("127.0.0.1", session["port"]), timeout=30) as connection:
        wire = connection.makefile("rwb")

        def request(command):
            wire.write(json.dumps(command).encode() + b"\n")
            wire.flush()
            response = json.loads(wire.readline())
            assert "error" not in response, response
            return response

        values = {}
        for name, address in (("current", 0x020DA464), ("requested", 0x020DA3EC),
                              ("selected", 0x020DA3F0), ("menu_mode", 0x020DA420),
                              ("scene_object", 0x020DA3BC), ("calculation_object", 0x020DA4E0)):
            data = request({"cmd": "read_mem", "cpu": 9, "addr": address, "len": 4})
            values[name] = int.from_bytes(bytes.fromhex(data["hex"]), "little")
        result = {"globals": values, "io": request({"cmd": "io_state"}),
                  "cpu9": request({"cmd": "regs", "cpu": 9}),
                  "cpu7": request({"cmd": "regs", "cpu": 7}),
                  "dispatch": request({"cmd": "dispatch_stats"})}
        if values["scene_object"]:
            result["scene_object_hex"] = request({"cmd": "read_mem", "cpu": 9,
                "addr": values["scene_object"], "len": 0xEA4})["hex"]
    output.write_text(json.dumps(result, indent=2) + "\n")
    print({name: hex(value) for name, value in values.items()})


if __name__ == "__main__":
    main()
