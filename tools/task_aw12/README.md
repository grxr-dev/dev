# AW12: ROM-free owned early yield and terminal pre-device fence

This folder cannot launch a runner or authorize guest execution. The certificate
is conditional and **capture-only**; B4, scheduler/device work and new slices are
not authorized. Production files and consumed AW9 permits are never changed.

Files:

- `controller.h`: one-use ownership, full 411-field transitions, chain and disposal.
- `gpu.h`: passive runtime-field/logical-FIFO projection and conservative admission.
- `hooks.py`: checked, reversible private overlay, not an installer.
- `fixture.h`, `inspect.cpp`: isolated scalar rail, no interpreter or real bus.
- `check.py`: source binding, native assertions, disposal/default children and audit checks.
- `certify.py`, `certificate.json`: source-bound static decision, never a launch permit.

Focused reproduction from repository root, with existing local pinned source,
w64devkit and authenticated historical AW9 metadata available:

```powershell
python -X utf8 tools/task_aw12/check.py --out local/task-aw12/repro-001
python -X utf8 tools/task_aw12/certify.py --evidence local/task-aw12/repro-001 --out local/task-aw12/repro-decision-001.json
```

Both destinations must be fresh. No ROM, save, checkpoint, screenshot, generated
recomp C or game runner executable is opened by these commands. The compiler
syntax-checks four runner translation units without linking them; only standalone
ROM-free diagnostic/default test executables are launched.

AW11's terminal metadata is committed. The first 68 historical ledger observations
are reconstructed using the first canonical snapshot from the old AW9 audit,
authenticated against its committed hash. Missing/stale local source or evidence
fails closed; do not regenerate it by replaying Brain Age. All new GPU values are
synthetic test inputs, never substitutes for a future live provider.

See `docs/BrainAge_TaskAW12_EarlyYieldFenceAndGPUReadiness.md` for exact scope,
preconditions, core-state hashes, source hooks, limits and next-task boundary.
