"""Audit the first marker construction and the menu-to-marker save transition."""

import argparse
import json
from pathlib import Path

from probe_boot import MARKER
from route_marker import digest, ranges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--before", required=True, help="Checkpoint immediately before selecting Daily Training")
    args = parser.parse_args()
    root = args.directory
    before = (root / args.before / "after.sav").read_bytes()
    before_summary = json.loads((root / args.before / "summary.json").read_text())
    events = [json.loads(line) for line in (root / "flash.jsonl").read_text().splitlines()]
    ledger = bytearray(b"\xff" * 262144)
    first_marker = None
    for sequence, event in enumerate(events, 1):
        assert event["sequence"] == sequence
        old, new = bytes.fromhex(event["old_hex"]), bytes.fromhex(event["new_hex"])
        assert len(old) == len(new) == event["length"]
        assert sum(previous != committed for previous, committed in zip(old, new)) == event["changed_bytes"]
        for index, value in enumerate(new):
            offset = (event["offset"] + index) & event["wrap_mask"]
            assert ledger[offset] == old[index]
            ledger[offset] = value
        if first_marker is None and ledger.find(MARKER) >= 0:
            first_marker = event
        if sequence == before_summary["sequence_after"]:
            assert bytes(ledger) == before
    persisted = (root / "erased.sav").read_bytes()
    assert bytes(ledger) == persisted, "replay differs from persisted save"
    assert first_marker is not None, "marker never constructed"
    transaction = [event for event in events if event["transaction"] == first_marker["transaction"]]
    assert transaction[-1]["last"], "marker transaction incomplete"
    (root / "marker-transaction.jsonl").write_text("".join(json.dumps(event) + "\n" for event in transaction))
    entry_events = events[before_summary["sequence_after"]:]
    changed_count, changed_ranges = ranges(before, persisted)
    report = {
        "save_sha256_before": digest(before), "save_sha256_after": digest(persisted),
        "changed_bytes": changed_count, "changed_ranges_half_open": changed_ranges,
        "accepted_commits": len(entry_events), "writing_transactions": len({event["transaction"] for event in entry_events}),
        "sequence_range": [entry_events[0]["sequence"], entry_events[-1]["sequence"]],
        "first_marker_event": first_marker, "marker_offset": persisted.find(MARKER),
        "marker_occurrences": persisted.count(MARKER), "marker_transaction_events": len(transaction),
        "replay_matches_persisted": True,
        "entry_transactions": []
    }
    for transaction_id in dict.fromkeys(event["transaction"] for event in entry_events):
        writes = [event for event in entry_events if event["transaction"] == transaction_id]
        report["entry_transactions"].append({
            "transaction": transaction_id, "sequence_range": [writes[0]["sequence"], writes[-1]["sequence"]],
            "offset_range": [writes[0]["offset"], writes[-1]["offset"]],
            "commits": len(writes), "changed_bytes": sum(event["changed_bytes"] for event in writes),
            "command_origin": writes[0]["command_origin"],
            "first_byte_origin": writes[0]["byte_origin"], "last_byte_origin": writes[-1]["byte_origin"]
        })
    (root / "marker-route-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "entry_transactions"}, indent=2))


if __name__ == "__main__":
    main()
