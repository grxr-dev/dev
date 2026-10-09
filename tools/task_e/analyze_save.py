"""Replay Task E Flash and correlate every API operation, page, FIFO and worker."""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_a"))
from route_marker import ranges


def digest(image):
    return hashlib.sha256(image).hexdigest()


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit(root, checkpoint):
    initial = (root / "initial.sav").read_bytes()
    final = (root / checkpoint / "after.sav").read_bytes()
    assert len(initial) == len(final) == 262144
    requests = records(root / "requests.jsonl")
    commits = records(root / "flash.jsonl")
    assert [event["sequence"] for event in requests] == list(range(1, len(requests) + 1))
    ledger = bytearray(initial)
    for sequence, event in enumerate(commits, 1):
        assert event["sequence"] == sequence and event["length"] == 1 and event["command"] == "0x0A"
        assert ledger[event["offset"]] == int(event["old_hex"], 16)
        ledger[event["offset"]] = int(event["new_hex"], 16)
        for origin in (event["command_origin"], event["byte_origin"]):
            assert origin["valid"] and origin["cpu"] == 7 and origin["pc"] == "0x038032B8"
            assert not origin["thumb"] and origin["execution"] == "tier3"
    assert bytes(ledger) == final
    transactions = [list(group) for transaction, group in itertools.groupby(commits, lambda event: event["transaction"])]
    request_index, transaction_index = 0, 0
    operations = []
    while request_index < len(requests):
        api = requests[request_index]
        assert api["kind"] == "write_api" and api["pc"] == "0x0200DE78" and api["payload_valid"]
        payload = bytes.fromhex(api["payload_hex"])
        assert len(payload) == api["length"]
        request_index += 1
        pages, consumed = [], 0
        while request_index < len(requests) and requests[request_index]["kind"] != "write_api":
            stages = requests[request_index:request_index + 4]
            assert [event["kind"] for event in stages] == ["submit", "fifo_send", "fifo_receive", "arm7_write"]
            submitted = stages[0]
            page = bytes.fromhex(submitted["payload_hex"])
            assert submitted["offset"] == api["offset"] + consumed and len(page) == submitted["length"] <= 256
            assert page == payload[consumed:consumed + len(page)]
            for event in stages:
                assert (event["offset"], event["length"], event["payload"], event["payload_hex"]) == (submitted["offset"], len(page), submitted["payload"], submitted["payload_hex"])
            assert stages[1]["r"][2] == stages[2]["r"][1] == 0x1eb
            transfer = transactions[transaction_index]
            assert len(transfer) == len(page) and transfer[-1]["last"]
            assert [event["offset"] for event in transfer] == list(range(submitted["offset"], submitted["offset"] + len(page)))
            assert b"".join(bytes.fromhex(event["new_hex"]) for event in transfer) == page
            pages.append({"offset": submitted["offset"], "length": len(page), "payload": submitted["payload"],
                          "payload_sha256": digest(page), "stages": [{key: event[key] for key in ("sequence", "kind", "cpu", "pc", "system_cycles", "instruction")} for event in stages],
                          "transaction": transfer[0]["transaction"], "sequence_first": transfer[0]["sequence"], "sequence_last": transfer[-1]["sequence"],
                          "commit_cycle_first": transfer[0]["byte_origin"]["system_cycles"], "commit_cycle_last": transfer[-1]["byte_origin"]["system_cycles"]})
            consumed += len(page)
            request_index += 4
            transaction_index += 1
        assert consumed == api["length"], "incomplete enclosing API operation"
        operations.append({"index": len(operations) + 1, "sequence": api["sequence"], "pc": api["pc"], "lr": api["lr"],
                           "callsite": hex(int(api["lr"], 16) - 4), "offset": api["offset"], "length": api["length"], "payload": api["payload"],
                           "payload_sha256": digest(payload), "system_cycles": api["system_cycles"], "instruction": api["instruction"], "pages": pages})
    assert transaction_index == len(transactions)
    changed, spans = ranges(initial, final)
    summary = json.loads((root / checkpoint / "summary.json").read_text())
    last_cycle = max([event["system_cycles"] for event in requests] + [event["byte_origin"]["system_cycles"] for event in commits], default=None)
    return {"root": str(root), "initial_sha256": digest(initial), "final_sha256": digest(final),
            "operations": operations, "api_operation_count": len(operations), "submission_count": sum(len(operation["pages"]) for operation in operations),
            "transactions": [transfer[0]["transaction"] for transfer in transactions], "accepted_bytes": len(commits),
            "changed_byte_commits": sum(event["changed_bytes"] for event in commits), "net_changed_bytes": changed,
            "changed_ranges_inclusive": [[start, end - 1] for start, end in spans], "last_event_system_cycle": last_cycle,
            "final_system_cycle": summary["final"]["counts"]["cyc7"],
            "quiet_system_cycles": summary["final"]["counts"]["cyc7"] - last_cycle if last_cycle is not None else None,
            "replay_matches_live": True,
            "paired_copies": [{"offset": start, "mirror": start + 0x20000, "length": length,
                               "equal": final[start:start + length] == final[start + 0x20000:start + 0x20000 + length]}
                              for start, length in ((0x100, 16), (0x600, 1792), (0x1b00, 32))]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aaa", type=Path, required=True)
    parser.add_argument("--bbb", type=Path)
    parser.add_argument("--restart", type=Path)
    parser.add_argument("--checkpoint", default="02-quiet-settle")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.aaa, args.checkpoint)
    if args.bbb:
        control = audit(args.bbb, args.checkpoint)
        assert control["initial_sha256"] == report["initial_sha256"]
        assert len(control["operations"]) == len(report["operations"])
        differing_operations = []
        for first, second in zip(report["operations"], control["operations"]):
            for field in ("callsite", "offset", "length", "payload", "system_cycles"):
                assert first[field] == second[field], field
            if first["payload_sha256"] != second["payload_sha256"]:
                differing_operations.append(first["index"])
        first_image = (args.aaa / args.checkpoint / "after.sav").read_bytes()
        second_image = (args.bbb / args.checkpoint / "after.sav").read_bytes()
        changed, spans = ranges(first_image, second_image)
        report["differential"] = {"bbb_final_sha256": control["final_sha256"], "differing_bytes": changed,
                                  "ranges_inclusive": [[start, end - 1] for start, end in spans],
                                  "differing_api_payloads": differing_operations, "matching_api_system_cycles": True}
    if args.restart:
        reload = json.loads((args.restart / "reload.json").read_text())
        assert reload["reload_sha256"] == report["final_sha256"] and not reload["savestate_imported"]
        for label in ("00-reloaded", "01-passive-startup", "02-recognize-profile"):
            observed = json.loads((args.restart / label / "summary.json").read_text())
            assert observed["save_sha256_after"] == report["final_sha256"]
            assert observed["accepted_bytes"] == observed["api_operations"] == observed["submissions"] == 0
        disk = (args.restart / "erased.sav").read_bytes()
        assert digest(disk) == report["final_sha256"]
        report["restart"] = {"exact_image_loaded": True, "no_startup_or_recognition_writes": True, "disk_sha256": digest(disk)}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("initial_sha256", "final_sha256", "api_operation_count", "submission_count", "accepted_bytes", "net_changed_bytes", "quiet_system_cycles")}, indent=2))
    for key in ("differential", "restart"):
        if key in report:
            print(json.dumps(report[key], indent=2))


if __name__ == "__main__":
    main()
