# AW9 one-shot validation - consumed

The single authorized live attempt completed successfully. **Do not rerun.**
Do not remove `local/task-aw9/one-shot.lock`, `attempt-001/launch.claim` or
`attempt-001/runtime.permit.claimed`, create alternate tickets, or launch the
private executable again.

- `preflight.py` reserved the attempt, verified frozen inputs and reran the exact
  AW8 artifact certificate preflight. It launches no guest process.
- `build.py` compiled an isolated source overlay, preserving original sources and
  existing binaries/archives. Only compile-scoped one-shot permission was added.
- `permission.h` adds guarded live admission after the original AU checks, exact
  captured-profile comparison, repeat-sampled AW7 ownership and runtime callback
  permission. No fixture identity adapters or guest-state writes are present.
- `run.py` has exactly one `Popen`, exclusive launch/ticket claims, frozen SDL
  input, no retry loop, and emergency termination only as a failure contingency.
- `analyze.py` is read-only with respect to the run; its local `analysis.json`
  output is exclusive. It independently verifies all 69 actual observations,
  canonical states and chain links against the frozen AW8 reference.

Proof: `local/task-aw9/attempt-001/analysis.json` and
`docs/BrainAge_TaskAW9_BoundedDividerValidation.md`. Exactly 11 original ARM
instructions/56 cycles executed, five MMIO writes/zero reads, final digest matches.
Architectural PC=0x020019B4 at terminal, but that instruction was never fetched,
accounted or dispatched. `_Exit(73)` bypassed the IRQ/scheduler/shutdown tail.

No additional execution is authorized. The next investigation must be ROM-free
and must address the retained cap before considering any status read.
