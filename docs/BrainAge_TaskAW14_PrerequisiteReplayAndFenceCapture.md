# AW14 - one authorized prerequisite replay and terminal-fence capture

**FULL PASS. One launch, one admitted replay/prefix, one capture-only ownership
transfer, no retry.** The expected AW9 terminal was re-established exactly, then
the unchanged AW12 controller reached its pre-device fence and disposed through
audit flush/close plus `std::_Exit(73)`. B4 was not fetched/accounted/dispatched
in the protected interval. No guest instruction, MMIO, IRQ, device, timer, GPU,
ARM7 or scheduler-tail service followed the verified terminal boundary.

This task consumed **new AW14 authorization** for the exact prerequisite replay
that AW13 correctly declined. AW9's consumed permits, previous evidence and
production runtime were not reused or modified. No further run is authorized.

## Authority, scope and artifact preflight

AW13 `1d64040633738bc63b5f49d2718d5c30dbad801c`; AW12
`b60203a9d30b3a8536395aaacdd15d126ee88399`; AW9
`fb3e417aa48cc70cc4c05f796263c9cf87b791af`; framework
`3a57236bb23d25dcb4caad7d58d733311062ff5e`.

Before launch, the unchanged AW8 certificate verifier was repeated and its entire
result matched the frozen prefix certificate. AW12's source/evidence-bound
certificate was independently regenerated and matched exactly. Its
`dynamic_execution_ready=false` was **not changed**: the user separately
authorized this one prerequisite replay and capture, not general execution.

All inherited source/evidence/claim hashes and actual ROM/checkpoint/save/frozen
input identities matched; no prerequisite mismatch or normalization occurred.
The immutable Task G context remains **11 - 7 = 4**:

- ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`.
- Checkpoint SHA-256
  `3911c3e98f90d77916497fd82e4f7ae49e7ca825273e52a90b66fd05ce2b2f2f`.
- Frozen gesture SHA-256
  `88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`.
- Prefix certificate payload
  `8381e1335266a05767982f292eb5237eb157bb5d8d9ea431c1a81d7552bae417`.

The consumed AW14 contract payload SHA-256 is
`98de9142486b367d4eb06f7260e42de649ff6e1e4fdcaf75e4c029ea43e3bcae`.
`tools/task_aw14/contract.json` records scope, not renewable permission.

## Isolated build and fresh ownership permission

`build/task-aw14-once/nds_runner.exe`, SHA-256
`dd57452989e3a9e97dd818ef5f246d8e89fc14c69905999f5aebb3fa64943f0e`,
recompiles **48 native runner sources** and reuses existing unchanged bank/support
archives. No ROM patch, generator, generated recomp-C edit, test identity adapter
or broad scheduler change was involved. All original native sources, binaries,
cached objects/archives and old one-shot claims remain unchanged.

The private overlay composes the exact AW12 hooks with narrowly scoped AW14 glue:

1. Claim a fresh contract/entry/nonce permit exclusively before the first
   scheduler round and arm AW12 through its fixed actual-provider facade. This
   records dispatch frames before the eventual terminal offer; arming inside the
   already-running AU dispatch would not establish the required frame ownership.
2. At AU's pre-dispatch boundary, **after all original AU guards**, compare the
   original live-provider 361-scalar/five-identity entry, run unchanged AW6 entry
   checks and unchanged AW7 repeat-sampling/controller handoff.
3. Open only the same narrowly guarded runtime access-owner permission used by
   AW9, under the new AW14 one-use contract. All address/order/value/model/cost/
   readiness/full-state checks remain dominating.
4. After the 69th accepted observation and all original terminal checks, offer
   the full terminal to unchanged AW12. Its controller, GPU projection, admission
   predicates and terminal/failure paths are **byte-identical** to the certificate.

AW14 has its own `one-shot.lock`, `launch.claim` and `runtime.permit.claimed`.
The nonce differs from AW9's consumed nonce; no old claim was cleared or copied
to bypass it. Permission forbids AW9/model/fixture compile modes. There is no new
gameplay selector, arbitrary guest-call API or production installation.

## Actual prerequisite replay and exact terminal

The same historical checkpoint/gesture route ran once in the real SDL3 runner,
with normal SDL-queue frontend events before coordinate conversion. Ten tokened
events generated recognition **2 then 4**; all ten native touches were consumed
with zero custom guest-delivery delta. No direct exercise/recognizer/raw-DS
shortcut was introduced.

The original AU preparation still recorded eight steps, nine reads and its one
certified stack write, ending before the STRH at `02001980`. This earlier
prerequisite preparation is distinct from the reduced prefix and zero-guest
handoff; the whole replay is **not claimed** to contain only 11 instructions or
zero device/MMIO activity.

At the protected prefix entry, all **361 scalars/five identities** and repeated
live samples matched digest
`0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c`.
Exactly **11 original ARM instructions / 56 ARM9 cycles**, five divider writes
and zero MMIO reads followed. **All 69 events, full states and chain links match
AW9 exactly**, including costs, model/deadline replacements and retained cap.

After retiring `020019B0`, the full **411-scalar/five-identity** terminal matched:

- SHA-256 `ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526`.
- Architectural PC `020019B4`; ARM9 cycle **3416875777**, cap **3416875778**,
  ordinal **281098019**.
- ARM7 cycle **1708437825**, ordinal **96026779**, parked debt **2**.
- SP `027E3654`, LR `02001A24`, CPSR `1F`, NZCV `0000`.
- Divider model deadline **1708437913**; no status read or completion service.

## Live AW12 ownership/fence transcript

The exact previously uncertified host-context predicates **passed on the real
runtime**: outermost tracked dispatcher, actual prior tail-dispatch/static-guard
pointers null, saved-unwind latch initially false, correct owner thread and
repeat-sampled complete terminal identity. Frame serial **566** was sealed, not
normalized to the synthetic test's frame 1. Ticket **1** was consumed once.

| Index | Event | Frame depth | Saved-unwind valid |
|---:|---|---:|---|
| 0 | yield_requested | 1 | false |
| 1 | tier3_exit | 1 | false |
| 2 | unwind_preserved | 1 | true |
| 3 | slice_consumed | 0 | false |
| 4 | slot_saved | 0 | false |
| 5 | pre_device_fence | 0 | false |
| 6 | gpu_observed | 0 | false |
| 7 | scheduler_admitted_capture_only | 0 | false |

Every full core snapshot and chained observation was independently checked with
the existing AW12 verifier. Only the two certified core changes occurred:

- `unwinding: 0 -> 1`, core SHA-256
  `64eeeb47b0d41e4814916852bf817a105b22bf28b96710c8c4e750af1fe7c99e`.
- `slot9.cycle: 3416875650 -> 3416875777`, fence core SHA-256
  `3528c2be122178850a3d3c78157cdd1adaf5409e5eb32f6d794e1c3f81d27d84`.

All other protected scalars and all five identities remained constant. CPU
registers/flags, both CPU cycles/ordinals, system time, cap/fast limit, journal,
divider state, RAM/DTCM/save identities and latent readiness observations did not
advance during the handoff. Final chain:
`10bad78f6ef2fd96a21b26be7e074943e6ded5fa5541844c731d3e39892472b4`.

## New passive live GPU readiness

The fixed getter read runtime-owned fields and logical queues twice, without
calling GPU Run or using a synthetic identity/ready flag. Complete schema and
repeat equality passed unchanged AW12 admission.

| Field | Captured value |
|---|---:|
| GeometryEnabled | 1 |
| FlushRequest | 0 |
| GXStat | **0x80000000** |
| raw CycleCount | 0 |
| GPU Timestamp | 1708437825 |
| ARM9Timestamp / ClockShift | 3416875650 / 1 |
| CmdPIPE / CmdFIFO / CmdStallQueue counts | 0 / 0 / 0 |
| Vertex / Normal / Polygon pipelines | 0 / 0 / 0 |
| VertexSlotCounter / VertexSlotsFree | 0 / **1** |
| Push-pop / test / execution-parameter counts | 0 / 0 / 0 |

The **19-scalar** canonical projection SHA-256 is
`708de6de2568d09123820267c9daaa7abd49321e90e275923ac93d96513ad5d4`.
It is deliberately **not** the AW12 synthetic idle fixture's hash: actual GXStat
and free-slot values differ. Neither was discarded or normalized. Busy bit 27
is clear, queues are empty and the observed command/work branch is ineligible;
all conservative capture predicates pass. This is not a claim that the entire
GPU, its status modes or a future scheduler tail has no effects. No GPU service,
including its ordinary timestamp update, was performed.

`tools/task_aw14/fence.json` losslessly binds all 411 core scalars/five identities
by reference to committed AW11 metadata plus the two validated deltas, and stores
all 19 typed live GPU scalars and ownership-chain metadata. Reconstruction was
checked against actual canonical audit bytes. It contains no ROM/RAM/save bytes
and is **not resumable emulator/host state or an execution permit**.

## Terminal disposal, safety and evidence

Actual escape preceded the Tier-3 IRQ check and next instruction loop. Actual
scheduler consumption preceded redispatch; slot save was followed by the fence
**before** the first device observer, ARM9 timer tick, GPU run and ARM7 catch-up.
The still-owned old ledger would reject any extra service observation, while
AW12's active guest guard rejects a further fetch/account/dispatch attempt.

The last event is AW12's capture-only terminal. Audit flush/close and `_Exit(73)`
were awaited normally; no timeout, first mismatch, emergency termination, normal
halt, shutdown or persistence tail occurred. There are zero protected B4 events,
zero additional guest instructions/MMIO after terminal, and zero post-fence
service. There was no next round, new slice/cap, status read or scheduler-tail
continuation. The one-cycle margin remains unaltered.

Logical save requests **0**, Flash commits **0**, changed save bytes **0**, verified
by empty traces, protected snapshot counters/identities and a direct byte
comparison of disposable initial/final save files. Source and disposable
checkpoints, source save, prior artifacts and permits remain unchanged.
Before/after Flash SHA-256:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

Local evidence: `local/task-aw14/attempt-001/`, including preflight, contract,
session, audit, frontend/save traces, analysis, scalar export, completion checks
and exclusive claims. Raw/game-containing files and private build remain ignored.

- Capture audit SHA-256:
  `23333fa102ef4f897a4c6ed9f69fb1c8c5be4f039d4b438b576ba492b606eb45`.
- Independent analysis SHA-256:
  `e1a01c6d7a5af1fc219cc4161ed3a30addac549cce43221046e9a8a5ebd1159e`.
- Fence-only audit SHA-256:
  `2966b0512cbbdd1b6c34e2f53b5930df59f083c1c37ccb48dba07391e5cf566e`.

## Exact next safe task and limits

The missing live context/readiness and ownership/fence observations are now
available. The next justified task is **ROM-free scheduler-tail/new-slice
certification from this lossless captured fence state**, including actual GPU
status/clock fields and every retained timer/IRQ/ARM7/device/cap observation.
Mechanically map/check each proposed service transition and its ordering, derive
the next safe pre-dispatch boundary if possible, and fail closed on missing state.

Do not execute that tail, replay again, normalize a cap, fetch/dispatch B4 or
perform the divider status read. This task did not certify any such execution,
compiled parity, full GPU/renderer object state, correctness/progression or save
integration. A full provider observation is not a full process checkpoint.

**Remaining authorized runs: zero.** Stopped after AW14.
