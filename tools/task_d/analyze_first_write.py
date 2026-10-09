"""Audit the bounded first profile page and an optional signature-only replay."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_a"))
from route_marker import ranges


def digest(image):
    return hashlib.sha256(image).hexdigest()


def audit(checkpoint):
    before = (checkpoint / "before.sav").read_bytes()
    after = (checkpoint / "after.sav").read_bytes()
    assert len(before) == len(after) == 262144
    requests = [json.loads(line) for line in (checkpoint / "requests.jsonl").read_text().splitlines()]
    commits = [json.loads(line) for line in (checkpoint / "flash.jsonl").read_text().splitlines()]
    assert [event["kind"] for event in requests] == ["write_api", "submit", "fifo_send", "fifo_receive", "arm7_write"]
    owner, submitted = requests[:2]
    payload = bytes.fromhex(submitted["payload_hex"])
    assert bytes.fromhex(owner["payload_hex"])[:submitted["length"]] == payload
    for event in requests[1:]:
        assert (event["offset"], event["length"], event["payload_hex"]) == (submitted["offset"], submitted["length"], submitted["payload_hex"])
    assert requests[2]["r"][2] == requests[3]["r"][1] == 0x1eb
    ledger = bytearray(before)
    for index, event in enumerate(commits, 1):
        assert event["sequence"] == index and event["length"] == 1
        assert event["offset"] == submitted["offset"] + index - 1
        assert ledger[event["offset"]] == int(event["old_hex"], 16)
        ledger[event["offset"]] = int(event["new_hex"], 16)
        for origin in (event["command_origin"], event["byte_origin"]):
            assert origin["valid"] and origin["cpu"] == 7 and origin["pc"] == "0x038032B8"
            assert not origin["thumb"] and origin["execution"] == "tier3"
    assert bytes(ledger) == after
    assert len(commits) == len(payload) == submitted["length"]
    assert after[submitted["offset"]:submitted["offset"] + len(payload)] == payload
    changed, spans = ranges(before, after)
    return {"checkpoint": str(checkpoint), "before_sha256": digest(before), "after_sha256": digest(after),
            "changed_bytes": changed, "changed_ranges_inclusive": [[start, end - 1] for start, end in spans],
            "ranges_hex": [{"offset": start, "old_hex": before[start:end].hex(), "new_hex": after[start:end].hex()} for start, end in spans],
            "requests": requests, "commit_count": len(commits), "transactions": sorted({event["transaction"] for event in commits}),
            "first_commit": commits[0], "last_commit": commits[-1], "replay_matches_live": True,
            "pending_owner_bytes": owner["length"] - submitted["length"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--differential", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.checkpoint)
    if args.differential:
        control = audit(args.differential)
        assert report["before_sha256"] == control["before_sha256"]
        assert len(report["requests"]) == len(control["requests"])
        for first, second in zip(report["requests"], control["requests"]):
            for field in ("kind", "pc", "lr", "offset", "length", "payload", "system_cycles"):
                assert first[field] == second[field], field
        first_payload = bytes.fromhex(report["requests"][0]["payload_hex"])
        second_payload = bytes.fromhex(control["requests"][0]["payload_hex"])
        first_page = bytes.fromhex(report["requests"][1]["payload_hex"])
        second_page = bytes.fromhex(control["requests"][1]["payload_hex"])
        report["differential"] = {"checkpoint": str(args.differential), "after_sha256": control["after_sha256"],
                                  "changed_bytes_from_baseline": control["changed_bytes"],
                                  "owner_payload_differences": sum(first != second for first, second in zip(first_payload, second_payload)),
                                  "first_page_differences": sum(first != second for first, second in zip(first_page, second_page)),
                                  "matching_request_system_cycles": True}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("before_sha256", "after_sha256", "changed_bytes", "changed_ranges_inclusive", "commit_count", "transactions", "pending_owner_bytes")}, indent=2))
    if args.differential:
        print(json.dumps(report["differential"], indent=2))


if __name__ == "__main__":
    main()
