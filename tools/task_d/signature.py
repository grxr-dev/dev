"""Generate deterministic signature or birth-field strokes for the real profile UI."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_c"))
from digits import DIGITS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("value", choices=("AAA", "BBB", "85", "01"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    outlines = {
        "A": [[(0, 1), (0.25, 0.5), (0.5, 0), (0.75, 0.5), (1, 1)],
              [(0.2, 0.6), (0.5, 0.6), (0.8, 0.6)]],
        "B": [[(0, 1), (0, 0.5), (0, 0)],
              [(0, 0), (0.7, 0), (1, 0.2), (0.7, 0.5), (0, 0.5),
               (0.7, 0.5), (1, 0.75), (0.7, 1), (0, 1)]],
    }
    strokes = []
    if args.value.isdigit():
        for index, digit in enumerate(args.value):
            for stroke in DIGITS[digit]:
                strokes.append([(round(255 - (65 + vertical * 115)),
                                 round(52 + index * 75 + horizontal * 38))
                                for horizontal, vertical in stroke])
    for index, letter in enumerate(args.value):
        for stroke in outlines.get(letter, []):
            strokes.append([(round(255 - (96 + vertical * 46)),
                             round(18 + index * 54 + horizontal * 42))
                            for horizontal, vertical in stroke])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(strokes, indent=2) + "\n")


if __name__ == "__main__":
    main()
