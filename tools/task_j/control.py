"""Supply one explicit host-native probe sample or Continue input; never advance guest logic directly."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--action", choices=("sample", "continue"), required=True)
    parser.add_argument("--sequence", type=int, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[2]
    root = args.out.resolve()
    assert root.is_relative_to(project / "local/task-j")
    records = [json.loads(line) for line in (root / "native-probe.jsonl").read_text().splitlines()]
    assert records and records[-1]["enabled"]
    assert records[-1]["event"] in ("panel_active", "held_sample"), "probe is not awaiting input"
    assert not any(record["event"] == "continue_original" for record in records)
    control = root / "native-control.txt"
    previous = int(control.read_text().split()[1]) if control.exists() else 0
    assert args.sequence > previous
    temporary = root / "native-control.next"
    temporary.write_text(f"{args.action} {args.sequence}\n")
    temporary.replace(control)
    print(f"Explicit native probe input: {args.action} {args.sequence}")


if __name__ == "__main__":
    main()
