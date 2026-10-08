"""Independently replay every logged Flash commit against an erased image."""

import argparse
import collections
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory
    trace = root / "flash.jsonl"
    ledger = bytearray(b"\xff" * 262144)
    events = []
    origins = {}
    pcs = collections.Counter()
    changed = 0
    for line in trace.read_text().splitlines():
        event = json.loads(line)
        assert event["sequence"] == len(events) + 1, "sequence gap"
        previous = bytes.fromhex(event["old_hex"])
        committed = bytes.fromhex(event["new_hex"])
        assert len(previous) == len(committed) == event["length"], "length mismatch"
        actual_changes = sum(before != after for before, after in zip(previous, committed))
        assert actual_changes == event["changed_bytes"], "change-count mismatch"
        changed += actual_changes
        for index, value in enumerate(committed):
            offset = (event["offset"] + index) & event["wrap_mask"]
            assert ledger[offset] == previous[index], f"old-byte mismatch at {offset:#x}"
            ledger[offset] = value
        transaction = event["transaction"]
        origin = event["command_origin"]
        assert origins.setdefault(transaction, origin) == origin, "command origin changed mid-transfer"
        pcs[(origin["cpu"], origin["pc"], origin["execution"])] += 1
        events.append(event)
    persisted = (root / "erased.sav").read_bytes()
    page_transactions = {event["transaction"] for event in events if 0x100 <= event["offset"] < 0x200}
    initial_page = [event for event in events if event["transaction"] in page_transactions]
    (root / "initial-page-sequence.json").write_text(json.dumps(initial_page, indent=2) + "\n")
    summary = {
        "records": len(events), "changed_bytes": changed, "write_transactions": len(origins),
        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
        "replay_matches_persisted_save": bytes(ledger) == persisted,
        "save_sha1": hashlib.sha1(persisted).hexdigest(),
        "marker_offset": persisted.find(b"CLEAR-RAM-CHECK"),
        "command_origins": [{"cpu": cpu, "pc": pc, "execution": execution, "records": count}
                            for (cpu, pc, execution), count in pcs.items()],
        "initial_page": {"transactions": sorted(page_transactions), "records": len(initial_page),
                         "first": initial_page[0] if initial_page else None,
                         "last": initial_page[-1] if initial_page else None},
    }
    (root / "trace-audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["replay_matches_persisted_save"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
