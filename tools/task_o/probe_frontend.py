"""Record the SDL-disabled runner prerequisite failure without replaying gameplay."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


EXPECTED_SAVE = "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"
EXPECTED_ROM = "b8a105bacc3234dede8d4465df0869f2b922a0e2"
EXPECTED_ERROR = (
    "[sdl] this runner was built without SDL; configure NDS_SDL_BACKEND=SDL3 "
    "or SDL2 for interactive presentation"
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    root = args.out.resolve()
    if not root.is_relative_to(repository / "local" / "task-o"):
        raise ValueError("output must be a new directory under local/task-o")
    cache = (repository / "build/task-a-runner/CMakeCache.txt").read_text()
    if "NDS_SDL_BACKEND:STRING=NONE" not in cache.splitlines():
        raise RuntimeError("this failure-only probe requires the SDL-disabled build")
    source = repository / "local/task-g/session-001/04-training-menu"
    image = (source / "after.sav").read_bytes()
    before = hashlib.sha256(image).hexdigest()
    if len(image) != 262144 or before != EXPECTED_SAVE:
        raise ValueError("unexpected Task G baseline save")
    if image.find(b"CLEAR-RAM-CHECK") != 0x180:
        raise ValueError("baseline marker missing")
    template = repository / "local/task-n/normal-enabled-002/session.json"
    command = list(json.loads(template.read_text())["command"])
    rom = Path(command[command.index("--rom") + 1])
    rom_sha1 = hashlib.sha1(rom.read_bytes()).hexdigest()
    if rom_sha1 != EXPECTED_ROM or "--force-tier3" in command:
        raise ValueError("unexpected ROM or forced-interpreter command")
    root.mkdir(parents=True, exist_ok=False)
    for name in ("initial.sav", "erased.sav"):
        (root / name).write_bytes(image)
    for name in ("flash.jsonl", "requests.jsonl", "calls.jsonl"):
        (root / name).touch()
    command[1] = str(root)
    command[command.index("--serve")] = "--interactive"
    command[command.index("--port") + 1] = "19875"
    command[command.index("--save-path") + 1] = str(root / "erased.sav")
    environment = os.environ.copy()
    environment.pop("NDS_TASK_B_TRACE", None)
    environment.update({
        "NDS_TASK_J_CUSTOM_EXERCISE_PROBE": "1",
        "NDS_TASK_N_DS_PRESENTATION": "1",
        "NDS_TASK_F_RTC_PLUS_ONE_DAY": "1",
        "NDS_FLASH_TRACE": str(root / "flash.jsonl"),
        "NDS_TASK_C_TRACE": str(root / "requests.jsonl"),
        "NDS_TASK_I_TRACE": str(root / "calls.jsonl"),
    })
    with (root / "stdout.log").open("wb") as stdout, (root / "stderr.log").open("wb") as stderr:
        result = subprocess.run(
            command, cwd=repository, env=environment, stdout=stdout, stderr=stderr,
            timeout=60, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    after_image = (root / "erased.sav").read_bytes()
    after = hashlib.sha256(after_image).hexdigest()
    stderr = (root / "stderr.log").read_text(errors="replace")
    trace_lines = {
        name: len((root / name).read_text().splitlines())
        for name in ("flash.jsonl", "requests.jsonl", "calls.jsonl")
    }
    evidence = {
        "classification": "blocked_missing_sdl_frontend",
        "command": command,
        "runner_exit_code": result.returncode,
        "expected_error_observed": EXPECTED_ERROR in stderr,
        "expected_error": EXPECTED_ERROR,
        "sdl_backend": "NONE",
        "rom_sha1": rom_sha1,
        "checkpoint_reference": str(source / "checkpoint.state"),
        "checkpoint_restored": False,
        "save_sha256_before": before,
        "save_sha256_after": after,
        "changed_save_bytes": sum(old != new for old, new in zip(image, after_image)),
        "trace_line_counts": trace_lines,
        "authoritative_window_proof_performed": False,
    }
    (root / "prerequisite.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    if result.returncode != 1 or EXPECTED_ERROR not in stderr:
        raise RuntimeError("unexpected startup result; inspect preserved logs")
    if after_image != image or any(trace_lines.values()):
        raise RuntimeError("unexpected activity in frontend failure-only probe")


if __name__ == "__main__":
    main()
