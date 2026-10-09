"""Audit the two bounded profile returns and their exact RTC/date differential."""

import argparse
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_e"))
from analyze_save import audit
from launch_return import decoded_rtc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--same", type=Path, required=True)
    parser.add_argument("--next", type=Path, required=True)
    parser.add_argument("--source-rtc", type=Path, default=Path("local/task-f/source-rtc-check/rtc-evidence.json"))
    parser.add_argument("--legacy", type=Path, default=Path("local/task-e/restart-001"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline = "fa9c6b3253574bac7d2969943ff29175022264e6cb1e190a2b963e1cd499c40a"
    source = json.loads(args.source_rtc.read_text())
    same = audit(args.same, "04-quiet-settle")
    next_day = audit(args.next, "04-quiet-settle")
    phases = ("00-initial", "01-passive-startup", "02-daily-training-entry", "03-select-AAA", "04-quiet-settle")
    observations = []
    for label in phases:
        first = json.loads((args.same / label / "summary.json").read_text())
        second = json.loads((args.next / label / "summary.json").read_text())
        for field in ("rtc_before", "rtc_after"):
            assert decoded_rtc(second[field]) - decoded_rtc(first[field]) == timedelta(days=1)
            assert second[field]["datetime"][3] == (first[field]["datetime"][3] + 1) % 7
        for observed in (first, second):
            if label == "03-select-AAA":
                assert (observed["api_operations"], observed["submissions"], observed["accepted_bytes"], observed["changed_bytes"]) == (1, 1, 48, 13)
            else:
                assert observed["api_operations"] == observed["submissions"] == observed["accepted_bytes"] == observed["changed_bytes"] == 0
        observations.append({"label": label, "same_rtc": decoded_rtc(first["rtc_after"]).isoformat(),
                             "next_rtc": decoded_rtc(second["rtc_after"]).isoformat(),
                             "same_hash": first["save_sha256_after"], "next_hash": second["save_sha256_after"],
                             "api_operations_each": first["api_operations"], "accepted_bytes_each": first["accepted_bytes"],
                             "net_changed_bytes_each": first["changed_bytes"]})
    for result, root in ((same, args.same), (next_day, args.next)):
        assert result["initial_sha256"] == baseline
        assert (result["api_operation_count"], result["submission_count"], result["accepted_bytes"], result["net_changed_bytes"]) == (1, 1, 48, 13)
        operation = result["operations"][0]
        assert (operation["callsite"], operation["offset"], operation["length"], operation["payload"]) == ("0x202d744", 0x7040, 48, 0x020e95fc)
        assert hashlib.sha256((root / "erased.sav").read_bytes()).hexdigest() == result["final_sha256"]
    first_image = (args.same / "04-quiet-settle/after.sav").read_bytes()
    second_image = (args.next / "04-quiet-settle/after.sav").read_bytes()
    differences = [{"offset": index, "same": first, "next": second}
                   for index, (first, second) in enumerate(zip(first_image, second_image)) if first != second]
    assert differences == [{"offset": 0x7066, "same": 1, "next": 2}, {"offset": 0x706e, "same": 0xa4, "next": 0xa3}]
    initial_same = json.loads((args.same / "00-initial/summary.json").read_text())
    assert initial_same["rtc_before"] == source["default_before_patch"]
    assert decoded_rtc(initial_same["rtc_before"]).date() == decoded_rtc(source["task_e_completed_profile_rtc"]).date()
    for current, legacy in (("01-passive-startup", "01-passive-startup"), ("02-daily-training-entry", "02-recognize-profile")):
        observed = json.loads((args.same / current / "summary.json").read_text())
        previous = json.loads((args.legacy / legacy / "summary.json").read_text())
        assert observed["final"] == previous["final"]
        assert observed["save_sha256_after"] == previous["save_sha256_after"] == baseline
    report = {"same": same, "next": next_day, "observations": observations,
              "source_profile_rtc": decoded_rtc(source["task_e_completed_profile_rtc"]).isoformat(),
              "exact_calendar_difference_seconds": 86400, "disabled_matches_prepatch_default": True,
              "disabled_matches_legacy_boot_and_profile_selection": True,
              "final_save_differences": differences,
              "rollover_exclusive_operation_observed": False,
              "both_profile_returns_write_date_dependent_record": True}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("source_profile_rtc", "exact_calendar_difference_seconds", "disabled_matches_prepatch_default", "final_save_differences", "both_profile_returns_write_date_dependent_record")}, indent=2))
    print("final hashes:", same["final_sha256"], next_day["final_sha256"])


if __name__ == "__main__":
    main()
