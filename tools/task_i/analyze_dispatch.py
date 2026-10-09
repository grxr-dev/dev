"""Reconcile the three bounded Task I call inventories and exact-ROM scene tables."""

import argparse
import hashlib
import json
from pathlib import Path
import struct


EXPECTED_ROM = "b8a105bacc3234dede8d4465df0869f2b922a0e2"
BASELINE_SAVE = "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"
TARGETS = {0x0202C668, 0x0204D790, 0x020610B4, 0x0205A150,
           0x02027A28, 0x0202756C, 0x02085BA8, 0x020857E0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    assert hashlib.sha1(rom).hexdigest() == EXPECTED_ROM

    def words(address, count):
        offset = address - 0x02000000 + 0x4000
        return list(struct.unpack_from("<" + "I" * count, rom, offset))

    def branch_case(address, index):
        site = address + index * 4
        opcode = words(site, 1)[0]
        assert opcode >> 24 == 0xEA
        displacement = opcode & 0xFFFFFF
        if displacement & 0x800000:
            displacement -= 1 << 24
        return site + 8 + displacement * 4

    tables = {hex(address): words(address, 9)
              for address in (0x020C7814, 0x020C785C, 0x020C7880)}
    result = {"rom_sha1": EXPECTED_ROM, "tables": tables, "scenes": {}, "runs": {}}
    for scene in (3, 0x41, 0x43, 0x10, 0x11, 0x6E):
        result["scenes"][hex(scene)] = {
            "cleanup_branch": hex(branch_case(0x0204D7B0, scene)),
            "initialize_branch": hex(branch_case(0x0204E35C, scene)),
            "update_branch": hex(branch_case(0x0204FC84, scene)),
        }
    for name in ("x20-001", "x100-001", "reading-001"):
        root = args.root / name
        restored = json.loads((root / "restore.json").read_text())
        assert restored["save_sha256"] == BASELINE_SAVE
        replay = bytearray((root / "initial.sav").read_bytes())
        assert hashlib.sha256(replay).hexdigest() == BASELINE_SAVE
        for sequence, line in enumerate((root / "flash.jsonl").read_text().splitlines(), 1):
            event = json.loads(line)
            assert event["sequence"] == sequence
            old, new = bytes.fromhex(event["old_hex"]), bytes.fromhex(event["new_hex"])
            assert len(old) == len(new) == event["length"]
            for index, value in enumerate(new):
                offset = (event["offset"] + index) & event["wrap_mask"]
                assert replay[offset] == old[index]
                replay[offset] = value
        assert replay == (root / "ledger.sav").read_bytes()
        records = [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]
        assert [row["sequence"] for row in records] == list(range(1, len(records) + 1))
        assert len(records) < 6000, "observer cap reached; inventory is incomplete"
        edges = {(row["pc"], row["target"]) for row in records}
        focused = [{"sequence": row["sequence"], "pc": hex(row["pc"]),
                    "target": hex(row["target"]), "r0_r3": [hex(value) for value in row["r"][:4]],
                    "system_cycles": row["system_cycles"], "instruction": row["instruction"]}
                   for row in records if row["target"] in TARGETS and
                   (row["hit"] == 1 or row["target"] == 0x0204D790)]
        phases = []
        for path in sorted(root.glob("*/summary.json")):
            summary = json.loads(path.read_text())
            assert summary["answer"] is None and not summary["strokes"]
            assert summary["replay_matches_live"]
            assert hashlib.sha256((path.parent / "after.sav").read_bytes()).hexdigest() == summary["save_sha256_after"]
            phases.append({key: summary[key] for key in (
                "label", "tap", "save_sha256_before", "save_sha256_after", "api_operations",
                "accepted_bytes", "changed_bytes", "changed_ranges_half_open", "live_matches_disk")})
        result["runs"][name] = {"restore": restored, "call_records": len(records),
                                  "distinct_edges": len(edges), "focused_calls": focused,
                                  "phases": phases}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    for name, run in result["runs"].items():
        print(name, "records", run["call_records"], "edges", run["distinct_edges"],
              "API operations", sum(phase["api_operations"] for phase in run["phases"]),
              "accepted", sum(phase["accepted_bytes"] for phase in run["phases"]))


if __name__ == "__main__":
    main()
