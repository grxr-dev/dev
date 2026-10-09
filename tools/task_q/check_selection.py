"""Check catalog defaults, stable selection, legacy no-ID default and unknown rejection."""

import argparse
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    assert output.is_relative_to(Path(__file__).resolve().parents[2] / "local/task-q")
    subprocess.run([str(args.binary.resolve())], check=True)
    cases = (("default", {}, "arithmetic-2plus2", 0),
             ("legacy", {"NDS_TASK_J_CUSTOM_EXERCISE_PROBE": "1"}, "arithmetic-2plus2", 0),
             ("stable", {"NDS_BRAINAGE_CUSTOM_EXERCISE": "1"}, "arithmetic-2plus2", 0),
             ("freehand", {"NDS_BRAINAGE_CUSTOM_EXERCISE_ID": "freehand-canvas"}, "freehand-canvas", 0),
             ("empty", {"NDS_BRAINAGE_CUSTOM_EXERCISE_ID": ""}, "arithmetic-2plus2", 0),
             ("unknown", {"NDS_BRAINAGE_CUSTOM_EXERCISE_ID": "not-registered"}, "unknown Brain Age custom exercise ID: not-registered", 2))
    results = []
    for label, selectors, expected, code in cases:
        environment = {key: value for key, value in os.environ.items() if not key.startswith(("NDS_BRAINAGE_", "NDS_TASK_"))}
        environment.update(selectors)
        result = subprocess.run([str(args.binary.resolve()), "--selection"], env=environment, capture_output=True, text=True)
        assert (result.stdout.strip(), result.returncode) == (expected, code)
        results.append({"case": label, "selectors": selectors, "result": expected, "code": code})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"pass": True, "cases": results}, indent=2) + "\n")
    print("PASS: catalog selection and clear unknown-ID rejection")


if __name__ == "__main__":
    main()
