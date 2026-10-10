# Task T: custom-host recognizer lifecycle preflight

**BLOCKED before implementation.** The mapped initialized recognizer is unavailable at the existing custom-host interception boundary. No service, factory changes or digit exercise were added. Task U was not begun.

## Evidence and classification

Read-only preflight used disposable copies of `local/task-g/session-001/04-training-menu/checkpoint.state` and `after.sav`, the preserved Task S executable, and the normal compiled dispatch path (`force_tier3` explicitly disabled after restore). No production code or runtime binary changed. ROM SHA-1 remains `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline remains `3a57236bb23d25dcb4caad7d58d733311062ff5e`.

`local/task-t/preflight-002` stopped before ARM9 `0x0204D790`, with r0=0x41, LR=0x02050268, ARM mode and current/requested/selected=0x32/0x41/0x11. Training context is 1. `preflight-001` reached the same stop but did not request the additional host observer log; it remains preserved.

The standard breakpoint stops before the compiled observer callback. To corroborate the backend without changing the host, `preflight-compiled-003` used a fresh restore and stopped at `0x0204D794`, immediately after the first push instruction. The existing observer records the boundary at `0x0204D790`, backend `compiled`, forced_tier3=false, and an accepted disabled-host gate. Neither rules initializer nor calculation constructor appears in the observer. The complete 4 MiB main-RAM dump is identical to the exact-entry snapshot (the push is outside main RAM).

This is a headless read-only preflight with ordinary debug menu touch at (166,75), not the authoritative SDL glyph experiment. No custom exercise is activated. No glyph is drawn, recognizer called or candidate submitted. All processes stop at this boundary and are discarded; no rules/Back/handoff trial is claimed.

Classification: **C for the mapped Calculations recognizer: not initialized here.** There is no proven safely borrowable alternative context. We do not claim exhaustive knowledge of all possible middleware object formats.

## Re-resolution rather than address reuse

The Task S addresses fail the object invariants in the boundary snapshot:

| Address/reference | Boundary value | Task S value |
|---|---|---|
| Prior exercise+0xC24 at 0x020EA624 | 0x1E581591 | manager 0x020FA808 |
| Prior manager at 0x020FA808 | 0x80E812E5 | slot count 1 |
| Prior context at 0x0211B994 | 0x88888888 | internal pointer 0x0211BA18 |

These are not usable pointers/objects at this lifecycle point. No writes or guessed calls were attempted.

The analyzer additionally scans all canonical 4 MiB main RAM for the mapped initialized context's self-relative pointer shape, then resolves slots through context pointers and validates the four point/descriptor allocation spans, then looks for manager-shaped references. At the boundary it finds **zero contexts, zero slots, zero manager candidates**.

As a positive control, the identical scanner recovers Task S context `0x0211B994` and slot `0x020FAA50`. It finds manager-shaped references at `0x020FA808` and `0x020FA840`; only the former is the Task R/S proven owner, so the scan does not assign ownership based on shape alone. This limits the negative result appropriately: no object matching the proven initialized shape exists in this snapshot, not proof against every hypothetical alternative representation.

## Minimum static lifecycle explanation

The narrow original setup path explains the absence:

1. Calculations constructor `0x02027A28`, normal handwriting branch, allocates a 0x238-byte manager at `0x02027AAC..0x02027AB0`.
2. It passes slot count 1 to setup `0x020531C8` at callsite `0x02027AC0`, then stores the returned manager at exercise+0xC24 (`0x02027AC4`). This is later than the Training-to-rules interception; the constructor is intentionally still unexecuted at that boundary.
3. Setup allocates 0x370-byte slot records, loads `/data/Decuma/_databas_le.bin` through `0x02066124`, allocates the context using `0x020A3F08`'s size, constructs configuration and allocates input/scratch buffers.
4. The same setup includes queue/worker facilities: calls at `0x0205330C` to `0x02005EC8`, `0x02053344` to `0x02005710` with entry 0x02051A30 and allocated stack, then `0x0205334C` to `0x02005568`. Worker-creation semantics are strongly supported by these parameters and the already mapped worker, not newly executed in Task T.
5. Slot activation later invokes `0x020A447C` at `0x020523E8`, as mapped by Task R.

This establishes where the known context comes from, but does not establish a standalone, reversible initialization contract at the earlier boundary. Simply calling the manager setup would add allocations, resource and worker/scheduler state beyond Task S's proven recognition memory ranges. Running the original Calculations constructor would violate Task T's requirement that it remain unexecuted before custom Continue. Copying the Task S context would contain state-specific pointers and would fake initialization.

The requested borrow-only path therefore cannot proceed. Safely manufacturing a new context would require additional resource, allocation, initialization and teardown ownership analysis, rather than reuse of the proven call boundary. That work was not expanded into broad middleware/runtime reverse engineering. No claim is made that safe initialization is impossible; it remains a separate prerequisite.

## Safety and unchanged implementation

For all three bounded preflights:

- logical save requests 0; Flash commits 0; changed save bytes 0;
- source checkpoint and canonical save bytes unchanged;
- disposable initial/live-final/disk save equal;
- no recognition call, exercise answer submission or correctness validation;
- no original exercise started/completed; no custom UI, service or guest-memory injection;
- no ROM patch, generated C edit, scheduler change or production host/contract/catalog modification.

Before and after SHA-256:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

Main-RAM SHA-256 at exact entry and after the first push:
`34c4307521d05dad103a7020eeb7ecf209c710c823c50cddef4c786233417b7f`.

Task S adapter bounds test passes unchanged. Existing arithmetic/freehand activation and SDL/headless implementation are unchanged; their runtime tests were not rerun because Task T made no implementation changes. No SDL presentation or service rollback evidence is claimed.

## Artifacts and reproduction

- `tools/task_t/preflight.py`: disposable restore, explicitly disable inherited force-tier3, bounded menu route, exact boundary stop, read-only memory/register capture and save comparison. Optional `--after-first` corroborates the existing compiled observer.
- `tools/task_t/analyze_preflight.py`: pointer-shape scan, positive Task S control, boundary invariants and save audit.
- `tools/task_t/static_lifecycle.py`: ROM-identity-gated narrow constructor/setup/activation disassembly, output local only.
- `docs/BrainAge_TaskT_Preflight.json`: compact derived facts and hashes.
- Local evidence: `local/task-t/preflight-001`, `preflight-002`, `preflight-compiled-003`, `static`.

Use fresh output directories:

```
python tools/task_t/preflight.py --out local/task-t/new-preflight
python tools/task_t/analyze_preflight.py --out local/task-t/new-preflight
python tools/task_t/preflight.py --out local/task-t/new-compiled --after-first
python tools/task_t/analyze_preflight.py --out local/task-t/new-compiled
```

Raw memory, ROM-derived disassembly, saves, checkpoints and logs stay local/ignored. The production host and the Task S implementation/evidence remain untouched.

## Next smallest task (recommendation only)

Isolate the minimum title-specific recognizer initialization and teardown lifecycle, including database/configuration ownership, allocator effects and whether the worker can be omitted for synchronous recognition. Establish an independently owned initialized session at the existing boundary without entering the original calculation constructor or advancing unrelated guest state. Do this before digit generalization or custom-host integration. No Task U implementation was begun.
