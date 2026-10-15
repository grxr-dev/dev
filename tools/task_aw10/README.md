# AW10: negative next-boundary certification

`python -B tools/task_aw10/check.py --out local/task-aw10/certification-new`

Use a fresh ignored output directory for another ROM-free test invocation. This
command never invokes a runner, interpreter, scheduler, bus, ROM reader, checkpoint
reader, or historical gameplay/capture driver. It reads committed scalar/hash
metadata with `git show fb3e417:...`. Current runtime source and retained AW9 build
metadata are read only to inspect and identify source, not to reconstruct state.
AW9 audit/canonical payloads are deliberately not opened.

`boundary.py` reconstructs an explicitly incomplete 89-scalar/five-identity
projection from committed AW9, AW8, AW6 and AU facts. It keeps the complete
411-scalar AW2S commitment separate. A projection is never admitted as the full
snapshot and never substituted for the provider. No positive execution path,
activation, identity adapter, cap write, early-yield hook or runner change exists.

The checker compiles `rail.cpp` with four extracted, identity/order-checked scalar
functions: cycle combination, slice-cap predicate, clock conversion and math
register selection. Synthetic arrays stand in for all peripheral storage. Calling
the scalar selector is not calling `nds_io_read` or a runtime bus. No ARM decoding
or guest instruction execution occurs. Original source excerpts/native binaries
remain ignored. The two disposal children exercise unchanged `task_aw::dispose`;
these are process-primitive checks, not a newly coupled live controller.

Python tests reject every projected scalar/identity mutation, wrong opcode/status,
timing/cap boundaries, unexpected/missing/reordered service events, and unknown
readiness fields. They cannot establish a complete new readiness projection or
scheduler transcript without the missing committed scalar state. That limitation
is why the overall result remains PARTIAL despite a conclusive negative cap proof.

`certificate.json` is a **negative admission certificate**. Zero guest instructions
and zero MMIO accesses are certified. The source-modeled `0x8001` status is not an
observed read. Every existing full-state provider/controller/owner/terminal guard
remains unchanged. No previous run permission or lock is removed or renewed.
