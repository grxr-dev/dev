# AW5: single AU capture, not AX activation

The authorized live attempt has been consumed in `local/task-aw5/capture-001/`.
It reached 0x02001980 before accounting/fetch/dispatch and **rejected** the
unchanged admission contract. Do not delete `live-attempt.lock`, normalize its
observed state, or run another capture without separate authorization.

`capture.h` is a capture-only wrapper at the already guarded AU terminal.
It records the real journal and full canonical snapshot, checks AW4 admission
and its pure prospective projection, seals/rechecks only if admission succeeds,
and disposes without returning. It never installs a candidate controller or
observer, dispatches an instruction, or changes timing/readiness state.
AW3's loader-derived ROM identity and exclusive audit remain mandatory.

The disabled path is unchanged. `NDS_TASK_AW5_CAPTURE_ONLY=1` selects this
wrapper only within the existing armed `NDS_TASK_AW3_CAPTURE_ONLY=1` AU handoff.
The legacy AW3-only capture and fully disabled AU path are model-tested.

## Helpers

- `install.py`: checked apply_patch installation into the local pinned runner;
  leaves all AU guards intact and adds no AX execution path.
- `check.py --out local/task-aw5/check-new`: ROM-free wrapper/guard tests,
  historical source/image binding and current single-bus-call/guard-order checks.
  Run from the AW4 authority checkout before committing AW5.
- `build.py --out build/task-aw5-capture-new`: recompiles native runner objects
  in isolation with existing Ninja flags and relinks existing compiled banks.
  No generator invocation or generated ROM-derived C modification. Existing SDL
  and headless executables/objects/archives are hashed and left untouched.
- `run.py`: one-attempt capture launcher using the immutable AU checkpoint and
  frozen frontend gesture. This is **not permission to replay it**. A fresh
  directory, successful preflight, matching build/source identities and an
  exclusive task-wide attempt lock are required. Uses `_Exit` 73/79, never
  expects normal shutdown/final-save output. Timeout cleanup is emergency
  process termination, never counted as successful terminal evidence.
- `analyze.py --capture local/task-aw5/capture-001 --out local/task-aw5/analysis-new`:
  read-only independent canonical/hash, AU event-budget and file-safety audit.
  `inspect.cpp` applies unchanged schema/manifest/journal/preflight/cost checks
  to the saved observation, without runtime calls or state normalization.

The old AU source checker expects literal `return bus_read` spelling, replaced
by AW observers. AW5 checks the same dominating read guard, exactly one real
bus call, write guards on both sides, and prefetch control ordering in current
source instead. No historical evidence or source table is rewritten.

All game-containing evidence, state/save copies, canonical buffers and executables
remain local/ignored. Commit only this ROM-free support and the report/result.
