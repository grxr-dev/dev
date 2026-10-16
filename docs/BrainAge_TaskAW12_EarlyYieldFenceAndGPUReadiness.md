# AW12 - owned early yield, pre-device fence and GPU readiness

**FULL PASS for the bounded ROM-free task:** a conditional **zero-guest,
capture-only handoff to a terminal pre-device fence** is statically certified.
This is **not** a full scheduler-tail/new-slice certificate. No guest instruction,
live replay, Brain Age MMIO, save/checkpoint access or mutation occurred.
`dynamic_execution_ready=false`; B4 remains forbidden. No runner was launched,
linked, installed, or made newly runnable.

## Authority and the two blockers

AW11 `b10e83d9f5e236930d7b2fd8e1b2b301e978decc`; AW10
`c699e3a21207abaa72b8130bf54c0f189c846412`; AW9
`fb3e417aa48cc70cc4c05f796263c9cf87b791af`; framework
`3a57236bb23d25dcb4caad7d58d733311062ff5e`.

AW11's complete 411-scalar/five-identity AW2S v1 terminal is retained verbatim.
Its 8,862-byte canonical SHA-256 is
`ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526`.
PC is `020019B4`, last retirement `020019B0`, cycle **3416875777**, cap/fast limit
**3416875778**. B4's eight-cycle LDRH still cannot fit. No field, epoch, cap,
hint, debt, or readiness observation is cleared to make admission pass.

1. Ordinary Tier-3 return, even with preserved unwind state, returns to
   `run_slice`, where cycle < cap redispatches B4. A new diagnostic owner must
   dominate this path; pretending the cap expired is not an acceptable fix.
2. `GPU3D::CyclesToRunFor()` exposes max(raw CycleCount,0), not command eligibility.
   Equal zero debt can hide different `GPU3D::Run()` branches. The new owner
   stops **before service**, observes the distinguishing fields, and rejects work
   eligibility rather than speculatively running it.

## Small diagnostic overlay, no normal scheduler redesign

`tools/task_aw12/hooks.py` builds a **private ignored source overlay** for four
runner translation units and AW7's header. Every textual change has a unique
anchor and an inverse that reconstructs the original source. The unmodified AU
header is copied too, so its quoted AW7 include resolves to the patched header,
not silently to the original header. No generated recomp C is read for rewriting
or modified. The original runner, AU guards, one-shot locks and prior evidence
remain unchanged.

| Source function | Narrow hook and ordering |
|---|---|
| `runtime_dispatch_impl` | Construct ownership Frame before `TailDispatchScope`, recording actual prior static-guard and tail-dispatch presence |
| `task_aw7::receive` | Offer only after the real ledger accepts its 69th observation and old bus/count/cycle/full-digest terminal guards pass |
| `tier3_run` | After retired observer, sync/preserve/break **before** IRQ acceptance, normal slice checks, fast-limit publication and the next instruction loop |
| `run_slice` | After original restore, consume ownership and break before terminal/DMA/HALT/event/slice branches; execute only original ARM9 slot save |
| `scheduler_run_round` | Fence immediately before first device observer, ARM9 timer tick and GPU Run; never return past it |
| GPU/runtime facades | Direct const GPU projection and actual saved-unwind-valid latch access |

`controller.h::arm_capture_only()` binds **fixed** original `task_aw3::passive`,
runtime GPU and saved-unwind getters. It is unavailable without
`AW12_DIAGNOSTIC_CAPTURE_ONLY`; there is no environment/gameplay activation or
launcher. Production sources are not installed by this task.

## One-use ownership and full-state transitions

The offer requires the exact terminal identity, unchanged AW6 readiness checks,
two exact passive samples, original observer ownership, one owner thread, an
exclusive audit, no active access, and a previously unspent ticket. The runtime
frame must be outermost, with **both actual prior tail-dispatch and static-guard
pointers null**, and no saved unwind state. These are additional trusted runtime
preconditions, **not claims about unrecorded historical AW9 host-stack state**.

Dispatch serials may legitimately increase before the offer. The selected serial
is then sealed and cannot change. A positive test has three completed earlier
frames and correctly binds frame 4 instead of freezing the synthetic frame-1
value. Ticket reuse, overflow, stale epochs, nested/parent contexts, duplicate
offers, re-entry and out-of-order consumption fail nonreturningly.

Exact event order:

`yield_requested -> tier3_exit -> unwind_preserved -> slice_consumed -> slot_saved
-> pre_device_fence -> gpu_observed -> scheduler_admitted_capture_only -> disposal`

Only two protected core fields change:

| Stage | Protected delta | Canonical core SHA-256 |
|---|---|---|
| Offer/escape | none | `ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526` |
| Preserve/consume | `unwinding: 0 -> 1` | `64eeeb47b0d41e4814916852bf817a105b22bf28b96710c8c4e750af1fe7c99e` |
| Slot save/fence | additionally `slot9.cycle: 3416875650 -> 3416875777` | `3528c2be122178850a3d3c78157cdd1adaf5409e5eb32f6d794e1c3f81d27d84` |

Every other scalar and all five identities remain exactly constant. CPU/registers,
NZCV, PC, ordinals, cap/fast limit, journal, scheduler/system time, IRQ/ARM7,
divider, protected-memory and save identities are not normalized or advanced.
The original whole-CPU preserve/restore code is used; the saved-valid latch is
`false,false,true,false,false,false,false,false`, frame depth
`1,1,1,0,0,0,0,0`. Parent guard revalidation is excluded by the entry gate.
Scope teardown between Tier-3 and the fence is limited by source to CPU restore,
host dispatch/profiling bookkeeping and slot save, not device/guest execution.

Each audit stage includes the entire canonical core. A SHA-256 chain starts with
the ASCII terminal digest and binds prior-chain ASCII, self-delimiting core and
GPU-extension AW2S bytes, LE index:u64, ticket:u64, phase:u8, saved-valid:u8,
depth:u32, bound-frame:u64 and a uint16-length event label. No pointer, padding,
thread-ID representation or uninitialized object bytes participate. GPU bytes
are present at the last two observation stages; earlier stages bind empty AW2S.

## Passive GPU projection and conservative readiness

`gpu.h` reads the actual vendored GPU type via the runtime-owned `g_nds` facade.
There are **19 base logical scalars**, plus two fields for every occupied queue
entry. The separate AW2S extension carries `gpu.schema:u16=1`:

- GeometryEnabled, FlushRequest, GXStat, signed raw CycleCount and Timestamp;
- VertexPipeline, NormalPipeline, PolygonPipeline, VertexSlotCounter,
  VertexSlotsFree, NumPushPopCommands, NumTestCommands, ExecParamCount;
- ARM9Timestamp and ARM9ClockShift;
- CmdPIPE/CmdFIFO/CmdStallQueue counts and **logical ordered Command:u8,
  Param:u32** entries, bounds 4/256/64. Const `Level/IsEmpty/Peek` only; no queue
  consumption, private union padding, renderer/savestate operation or MMIO.

The source-derived work branch is:
`GeometryEnabled && !FlushRequest && (!CmdPIPE.IsEmpty() || GXStat.bit27)`.
Capture admission additionally requires complete schema/widths, stable repeat
sampling, matching old GPU-debt projection, clock shift 1, no future timestamps,
no busy bit, nonpositive raw cycles, empty queues and zero relevant pipeline /
push-pop / test / execution-parameter counts. Unknown or latent work rejects.
This is deliberately more restrictive than merely observing the early-out branch.

The same-debt command-queued and busy-bit alternatives are now observably distinct
and fail **before** GPU Run. Even the admitted branch never calls Run: its normal
timestamp update and all downstream service are forbidden in this certificate.
Historical AW9 GPU values remain **unknown**. Synthetic idle extension hash
`2ee3910544906c52d6c29f2be2808d30ad36d4914c9dc40f2b5b6b7f35e79640`
is a test witness, **not** a substituted historical/live identity.

## Fence, disposal and certificate boundary

After slot save, the fence samples all protected core state, samples GPU twice,
resamples core, binds canonical observations and evaluates capture admission.
Success flushes/closes the audit and calls `std::_Exit(73)`. Any mismatch or
unexpected old observer event follows nonreturning failure disposal, code 79
(audit IO failure 78). No `nds_halt()` fallback, scheduler tail, GPU/device/IRQ/
ARM7 work, shutdown, persistence or post-terminal destructor can follow disposal.
Host-only scope bookkeeping **before** the terminal fence is not shutdown.

`tools/task_aw12/certificate.json` certifies only this zero-guest transition.
There is **no new slice/cap relation to invent**: cycle 3416875777 remains less
than cap 3416875778. The resulting architectural PC is still `020019B4`, but
**no next guest boundary is certified for dispatch**. B4 fetch/account/dispatch,
the status read, any service, new round and new cap remain forbidden.

## Tests and provenance limits

Final evidence: `local/task-aw12/certification-014/`; summary SHA-256
`d8b719839bc8974f097469a5b30812210ae637e3326f453a4674c58d13f9b427`.

- **1,311 focused native unit assertions**: all 411 fields mutated/omitted/
  width-changed, all five identities, GPU schema omissions/widths/value binding,
  wrapped FIFO logical order, passive reads, alternate eligibility and defaults.
- **49 children**: three successes (explicit owner, fixed runtime facade,
  prior-frame evolution), **45 independent failure disposals**, one disabled
  original-redispatch control. No service/shutdown/persistence/tail sentinel ran.
- **19 independent audit tamper rejections**: missing/duplicate stages, chain,
  frame and reordered transcript. Complete positive record/phase/full-state
  order and chains are independently recomputed in Python.
- **Eight syntax-only checks** of the four actual patched runtime translation
  units, diagnostic and default builds; a ninth check instantiates the getter
  against the **actual melonDS GPU3D/FIFO types**, including private entry type
  access via const Peek. No runner linking or execution.

The scalar rail compiles original preserve/restore/clear functions, actual mutable
runtime/scheduler getter bodies and patched original `run_slice`; it uses the
actual AW3 journal/passive aggregator and AW6/AW7 ledger. The other **267 readonly
bus/CP15/IO cells** and five identities are authenticated historical metadata with
an explicit ownership partition, **not live image measurements**. They cannot
silently fill missing mutable getters. The first 68 ledger observations are a
historical source/model receipt; the last retired observation comes from the
current isolated provider. No instruction interpreter or real bus is linked.
The stub models the already-running dispatch's return at the terminal cycle; it
does not resume AW9, reset a live cap or execute a fresh slice of Brain Age.

Full actual dispatcher/Tier-3 control flow is source-checked and syntax-compiled,
not executed. GPU content is synthetic. The new host-context preconditions and
extended GPU facts must still be measured later. This does not certify a full
GPU object, renderer thread, complete scheduler tail, physical hardware or guest
status-read execution. Old AW9 one-shot permissions remain consumed and unchanged.

## Disabled behavior, safety and next task

With no diagnostic owner, hooks do nothing; arming is rejected in the default
build. The disabled original `run_slice` still redispatches under the unexpired
cap, reproducing AW11 rather than silently changing ordinary semantics. Original
source/evidence/lock hashes are checked unchanged. No ROM/save/checkpoint was
opened; zero guest/MMIO/save operations or Flash commits occurred. Historical
save SHA-256 remains a reference, not a fresh measurement:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

**Next safe task:** separately authorize one capture-only terminal-to-pre-device-
fence validation using this exact owner. It must acquire fresh permission for
any prerequisite AU replay plus the previously certified 11-instruction prefix,
if reaching the terminal requires it; AW9's consumed permit cannot be reused.
Require exact preflight/69-event terminal identity, trusted outermost context and
passive GPU samples; take the owned zero-guest exit, then dispose at the fence on
success **or** mismatch. No B4 fetch/account/dispatch, service, new cap or retry.
That later validation is justified, **not performed or authorized by AW12**.
Only afterward reconsider separate full scheduler-tail/new-slice certification.

Stopped after AW12. No AX or further guest instructions were executed.
