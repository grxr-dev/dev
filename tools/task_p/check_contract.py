"""Check the exercise contract and actual stable/compatibility environment translation."""

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
    repository = Path(__file__).resolve().parents[2]
    output = args.out.resolve()
    assert output.is_relative_to(repository / "local/task-p")
    subprocess.run([str(args.binary.resolve())], check=True)
    names = ("NDS_BRAINAGE_CUSTOM_EXERCISE", "NDS_TASK_J_CUSTOM_EXERCISE_PROBE",
             "NDS_BRAINAGE_NATIVE_PRESENTATION", "NDS_TASK_N_DS_PRESENTATION")
    cases = (("disabled", {}, "0 0"),
             ("legacy-popup", {names[1]: "1"}, "1 0"),
             ("legacy-native", {names[1]: "1", names[3]: "1"}, "1 1"),
             ("stable-default-native", {names[0]: "1"}, "1 1"),
             ("stable-off-wins", {names[0]: "0", names[1]: "1", names[3]: "1"}, "0 0"),
             ("stable-popup-wins", {names[0]: "1", names[2]: "0", names[3]: "1"}, "1 0"))
    results = []
    for label, selectors, expected in cases:
        environment = os.environ.copy()
        for name in names:
            environment.pop(name, None)
        environment.update(selectors)
        actual = subprocess.check_output([str(args.binary.resolve()), "--activation"], env=environment, text=True).strip()
        assert actual == expected, (label, actual, expected)
        results.append({"case": label, "selectors": selectors, "enabled_presentation": actual, "pass": True})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"pass": True, "contract_test": True, "activation_cases": results}, indent=2) + "\n")
    print("PASS: contract and six actual environment compatibility/configuration cases")


if __name__ == "__main__":
    main()
