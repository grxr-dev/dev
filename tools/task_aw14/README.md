# AW14 one-shot replay/capture - consumed

The newly authorized AW14 attempt completed. **Do not rerun, delete claims, make
replacement tickets, or launch this private runner again.** Old AW9 permission
and artifacts remain unchanged; AW14 uses a different task lock and permit.

- `preflight.py`: reserves the sole attempt, rechecks AW8/AW12 certificates and
  frozen ROM/checkpoint/save/input identities. No guest launch.
- `build.py`: private native-source overlay with unchanged AW12 controller/GPU
  code and AU guards; reuses existing bank/support archives without generation.
- `permission.h`: compile-scoped fresh contract/nonce claim before the first
  scheduler round, fixed passive-provider arming, then unchanged exact AU/prefix
  admission. There is no gameplay or arbitrary guest-call API.
- `run.py`: one exclusive launch, historical frozen SDL input, no retry; disposes
  through the unchanged controller at the pre-device fence. Emergency termination
  is a failure contingency only and was not used.
- `analyze.py`: read-only prefix/full-state/chain and fence verification.
- `export.py`: promotes scalar-only live fence metadata; never makes a checkpoint
  or execution permit.
- `contract.json`: the consumed task's bounded scope, not renewable permission.
- `fence.json`: lossless reference to AW11's 411-field core plus two verified
  deltas, actual live GPU scalars and ownership chain; no RAM/ROM/save bytes.

Proof: `local/task-aw14/attempt-001/analysis.json`, `capture.jsonl` and
`docs/BrainAge_TaskAW14_PrerequisiteReplayAndFenceCapture.md`.

Exactly one guarded prerequisite replay reached the same AW9 terminal after the
11-instruction/56-cycle/five-write prefix. Then eight AW12 observations led to
nonreturning disposal at the pre-device fence with zero additional guest/MMIO or
service. B4 was never fetched/accounted/dispatched in the protected interval.

The private runner/build, ROM, saves/checkpoints, memory snapshots and raw audit
remain local/ignored. `local/task-aw14/one-shot.lock`, `attempt-001/launch.claim`
and `attempt-001/runtime.permit.claimed` must remain intact.

Next work is separately authorized **ROM-free scheduler-tail/new-slice
certification** from the committed fence metadata. No new replay, GPU service,
cap change, status read or guest execution is authorized.
