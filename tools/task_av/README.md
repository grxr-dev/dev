# Task AV: static only

Run `python -B tools/task_av/check.py`. Regenerate the ROM-free certificate with
`python -B tools/task_av/analyze.py --export`. These tools read retained evidence,
decode file bytes, check source text, and perform integer arithmetic. They do not
load a runtime, execute ARM, call MMIO, replay AU, or service an event.

The proposed AW boundary is conditional, not permission to run it. See the report
for missing live-entry evidence and the scheduler-tail hazard. No AW installer,
runner, runtime patch, or guest evaluator is included.
