"""Clean-load an observed Flash snapshot, without advancing guest execution."""

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
    parser.add_argument("--port", type=int, default=19857)
    args = parser.parse_args()
    source, root = args.source.resolve(), args.out.resolve()
    summary = json.loads((source / "summary.json").read_text())
    image = (source / "after.sav").read_bytes()
    expected = hashlib.sha256(image).hexdigest()
    assert len(image) == 262144 and expected == summary["save_sha256_after"]
    command = json.loads((source.parent / "session.json").read_text())["command"]
    assert hashlib.sha1(Path(command[command.index("--rom") + 1]).read_bytes()).hexdigest() == "b8a105bacc3234dede8d4465df0869f2b922a0e2"
    root.mkdir(parents=True, exist_ok=False)
    save = root / "observed.sav"
    save.write_bytes(image)
    command[1] = str(root)
    command[command.index("--port") + 1] = str(args.port)
    command[command.index("--save-path") + 1] = str(save)
    environment = os.environ.copy()
    for name in ("NDS_FLASH_TRACE", "NDS_TASK_B_TRACE", "NDS_TASK_C_TRACE"):
        environment.pop(name, None)
    with (root / "stdout.log").open("wb") as stdout, (root / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=environment,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    try:
        connection = None
        for attempt in range(100):
            if process.poll() is not None:
                raise RuntimeError("runner exited before snapshot reload")
            try:
                connection = socket.create_connection(("127.0.0.1", args.port), timeout=1)
                break
            except OSError:
                time.sleep(0.1)
        if connection is None:
            raise RuntimeError("debug server did not start")
        with connection:
            connection.settimeout(120)
            wire = connection.makefile("rwb")

            def request(payload):
                wire.write(json.dumps(payload).encode() + b"\n")
                wire.flush()
                response = json.loads(wire.readline())
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response

            actual = bytes.fromhex(request({"cmd": "cart_save"})["hex"])
            counts = request({"cmd": "io_state"})
            save_info = request({"cmd": "cart_save_info"})
            assert actual == image and counts["counts"]["insn9"] == counts["counts"]["insn7"] == 0
            report = {"source": str(source), "command": command, "snapshot_sha256": expected,
                      "reload_sha256": hashlib.sha256(actual).hexdigest(), "bytes_match": True,
                      "io_state": counts, "save_info": save_info, "guest_execution_advanced": False,
                      "profile_recognition_tested": False, "automatic_write_through_tested": False}
            (root / "reload.json").write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report, indent=2))
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
