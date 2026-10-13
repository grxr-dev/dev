# Task AW3 - live provider, immutable observations and AU handoff

**PARTIAL. AX certificate withheld; AX and optional live capture were not run.**
Meaningful live-provider/handoff gaps are closed in implementation and focused
ROM-free tests. A concrete expected-state/controller contradiction now prevents
full certification. It is not hidden by dropping fields or relaxing guards.

Authority: AW2 `cb7ab39c07fd2d35bf7bdd04bcdda2d06aaf6540`, AW
`71f28f7ecc87388691c4c68589811d4322d05863`, AV
`524acc6bead2768183e45ae4913b00ea811b274b`, AU
`f17f95ae2b2a15f7fced6f04d82d2593350d37a4`; framework
`3a57236bb23d25dcb4caad7d58d733311062ff5e`; exact ROM SHA-1
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

No Brain Age runner was launched, no guest instruction/AX opcode executed,
no divider or other MMIO read/write occurred, and no ROM/save/checkpoint was
loaded or mutated. Native tests set synthetic host globals and mock CPU records;
a record whose PC is 0x02001980 is not execution at that address. Only six runner
object targets were compiled, not the runner executable or generated banks.
Unrelated `jarvis-inbox-v1.zip` and prior committed helpers/evidence are preserved.

## Blocker-by-blocker disposition

| AW2 blocker | AW3 implementation/proof | Remaining certification |
|---|---|---|
| 1. Trusted live cap/epoch and hidden latches | Runtime hooks record actual slice begin, every reschedule including nonshortening calls, and direct setters. Source/CPU/clock/before/after/deadline/epoch/serial are recorded before cap mutation. Component imports invalidate eligibility. Actual-runtime tests exercise the hooks. Hidden code/data addresses, page-cache class/generation, retained region class, publication, sampled I/D-cache bits and poll/debt state are copied directly. | Not proven eligible at the real AU stop; direct setters, unknown timing and stale histories reject. These added fields still need complete per-instruction prediction. |
| 2. Actual readiness projection | Typed actual IRQ masks/cache, ARM7 lifecycle/clock/debt, scheduler target/event/round epoch, device deadlines, DMA/timers, divider model, display/RTC/SPU phase and passive GPU debt are projected. Unknown enabled timers, power/persistence service, synthetic event configuration, stale phase and nonzero GPU debt reject. All actual providers compile. | Complete actual I/O/provider-to-controller end-to-end test is not supplied; the native linked rail uses device stubs. No live readiness claim. |
| 3. Trusted immutable observations | Cartridge loader hashes actual input with SHA-1 before transformations. Direct RAM/DTCM vectors supply actual hashes and scalar code/protected-range values; save snapshot supplies actual save hash/dirty state, separately observed request/commit counters. Independent AU anchors/eligibility precede immutable seal, then a second passive snapshot must match every canonical field/digest and current epochs. | The positive full seal test uses synthetic authority-compatible observations. No actual AU image/ROM observation was collected in this task. |
| 4. Full original-runtime projection into controller | Actual canonical provider and protected core projection implemented, with more metadata than AW2. A negative test proves the strict AW2 ledger rejects the runtime-grown cap history. | **Not closed:** AW2 expected states freeze cap history and snapshot ordinal; actual history/ordinal, hidden latches and accounting change. A revised complete expected model/adapter is needed. |
| 5. Guarded AU ownership handoff | Installed AU index-7 handoff is after all original CPU/path/count/memory/save/forbidden-dispatch checks and before legacy files/finish. Armed AU finish, ordinary halt and escaping AU exceptions use nonreturning failure disposal. If AU control returns at 0x02001980, Tier-3 disposes before exit polling/bank/accounting/fetch. Tests compile the actual guarded AU fragment. | Certified capture-only admission/terminal behavior on synthetic provider observations, not a transition into executable AX. |
| 6. Complete live AU-to-terminal success | Capture-only success/failure disposal passes with the actual AU guard fragment and a synthetic provider model. Actual cap/import hooks are separately tested and all provider objects compile. | **Not closed:** there is no complete actual-I/O/full-state/77-event success coupling. No live replay is allowed until that certification is complete. |

This is not BLOCKED on a broad scheduler redesign. The remaining work is exact
state-model/controller integration and full actual-provider testing. The first
candidate instruction is MMIO, so no positive reduced prefix is certified.

## Runtime-owned provenance

`tools/task_aw3/bridge.h` is default-inactive. The cartridge loader arms only
with `NDS_TASK_AW3_CAPTURE_ONLY=1` and an exclusive fresh
`NDS_TASK_AW3_AUDIT` file. Wrong actual ROM input is a fatal failure. No caller
provides a title-verified boolean. The selectors were not enabled in a game run.

Hooks cover all three cap-changing APIs: `nds_slice_begin`, `nds_set_cycle_cap`,
`nds_reschedule_slice`. A slice begin starts a new epoch; reschedules record the
checked ARM9/system conversion and minimum even when the cap does not shorten.
An earlier cap survives later deadline replacement. Direct setters are recorded
as unclassified and invalidate eligibility until a fresh genuine slice origin.
Overflow, missing epoch, excessive journal size and off-owner changes fail closed.

The cap history's initial logical predecessor is zero at its new slice epoch,
because slice begin replaces the old cap. The actual overwritten value is retained
separately as `observed_before`; it is not normalized or lost. Base/quantum/target
must match the actual stored ARM9 slot and scheduler-planned target. ARM7 records
cannot be relabeled ARM9. ARM7's historical lag is preserved, not set to zero.

Runtime, bus, CP15, core-I/O, peripheral-I/O and scheduler imports invalidate the
epoch before component changes. Imports or cap changes after immutable sealing
dispose immediately. Fresh imports cannot silently reuse an older sealed proof.

## Passive provider and readiness

`runtime.inc` copies registers/CPSR/clocks/ordinals, current cap/fast limit/debt,
stop/unwind flags and active return stack. `scheduler.inc` verifies owner/current
slot and copies stored ARM7/ARM9 clocks/debt/lifecycle, system timestamp, actual
round-selected target and next event, Wi-Fi deadline, SPU mix phase and GPU debt.
It does not call `save_current`, run a slice or advance a device.

`bus.inc` reads only direct vector storage: complete RAM/DTCM hashes, all required
code/literal/protected scalars, stack word, code/data latches, retained/published
timing class and sampled I/D-cache bitmap bits for the candidate addresses.
`cp15.inc` copies actual MPU/cache/permission/TCM/generation values.
`io.inc` copies typed core fields and private scalar deadlines/results, timer/DMA
state, cached IRQ masks, periodic phase, persistence dirtiness, save bytes for
hashing, and independent counters. No raw object padding or pointer identity is
serialized. The current ordinal/clock must remain equal the ending stamps.

Copied code/data bitmap values must agree with the independent copied-CP15
classifier. The preceding AU code/data latch must be 0200197C/020019A8; cached
page/generation/region/publication must be consistent. Fast-poll mode is captured
as a feature flag, not mistaken for an IRQ/service-ready flag. Pending yield
state rejects conservatively.

Readiness derives the scheduler minimum from periodic LCD/SPU/RTC timing and
copied peripheral/divider/Wi-Fi deadlines and checks the actual recorded minimum.
Display last-service timestamp and RTC/SPU processed phase must match the copied
system timestamp; GPU debt must be zero. Enabled timer state is not guessed safe.
Actual IRQ IME/IE/IF/cache agreement, ARM7/debt relation and prospective cap/cost
checks remain fail-closed. This is a deliberately conservative eligibility subset,
not a general enabled-device scheduler certification.

## Immutable binding and handoff

The AW2S v1 logical encoding is reused with additional protected keys; no raw
layout changes or pointer-based identity. The independent 74-scalar/five-identity
AU manifest remains unchanged. A complete observed snapshot is sealed only after
authority-anchor, epoch, hidden-latch and readiness checks. The second passive
sample must equal the full snapshot and its SHA-256, not merely the reduced core.
Unknown/unrecorded actual entry facts are never replaced by fixture constants.

The new AU branch is capture-only: it logs canonical observations, seals/verifies,
flushes/closes audit and `_Exit(73)`. Failed guards/provider/preflight/seal checks
flush failure evidence and `_Exit(79)`; audit failure hard-exits 78. There is no
success branch returning to fetch, synthetic LR return, scene forgery or AX mode.
When inactive, the old AU behavior remains, including its legacy halt path.

All original AU checks precede handoff. Armed `finish` is fenced before final
save copies or `nds_halt`. `nds_halt` itself is fenced before setting terminal;
escaped AU exceptions and returned pre-MMIO handoff also dispose. Thus the
capture-only design does not try to make the unsafe scheduler-tail halt safe.

## Exact remaining controller contradiction

AW2 `model.h::transcript` increments `ordinal9` but leaves `snapshot_ordinal`
frozen in its expected snapshots. The actual provider copies both from the
current instruction count. After fetch/accounting they therefore cannot match.
Also AW2 expected cap history stays at one entry. Actual provenance appends a
record for every reschedule, including deadline replacements that do not change
the retained cap. The first setup write already creates a different protected
history/serial/count. Hidden fetch/data/publication, return-stack and accounting
fields also need a complete expected transition model.

The new test accepts AW2's entire 77-event synthetic model, then separately
constructs the runtime-grown history at the first reschedule and proves the
same strict ledger rejects it. This is a concrete contract contradiction, not
an excuse to ignore new fields. The capture-only seal also deliberately forbids
post-seal mutations; it is not an executable AX controller admission.

## Tests, limitations and optional replay

Final evidence: `local/task-aw3/certification-005/tests.json`, `commands.json`,
native audit and fourteen child audit directories. Earlier failed compilation /
test directories remain historical and were not overwritten as passing evidence.

- **813 assertions**: canonical identity, every protected field mutation/omission,
  manifest classes, epochs, hidden latches/bitmaps, service readiness, cap retention,
  import staleness, disabled journal, AW2 ordered model and exact new-state rejection.
- **10 actual-runtime checks**: real slice/setter/reschedule provenance, nonshortening
  deadline replacement, direct passive cap/clock stability, real CP15 import
  invalidation, fresh epoch and unchanged disabled cap semantics.
- **14 child processes**: capture-only success; stale identity, manifest, hidden
  latch, readiness, preserved guard, bad AU CPU, actual wrong-ROM hash, overflow,
  off-owner change, missing field, post-seal cap/import, and disabled control.
  Armed cases never reach old-halt/legacy file/post-boundary/device/IRQ/ARM7/
  destructor/persistence sentinels. Disabled control deliberately reaches its
  old-halt sentinel, proving the original path is not silently replaced.
- **Six actual objects compile**: runtime, scheduler, bus, I/O, CP15 and Tier-3.
  No runner relink/launch or generated-C emission/edit occurred.

The AU guard-fragment positive test uses a mock CPU and synthetic provider and
memory observations. The linked runtime rail uses existing device stubs and an
I/O provider that rejects unsupported use; it does not prove a full actual I/O
success path. Zero actual guest/MMIO is measured by construction, not an invented
live trace. Actual AU readiness/timing/save before-after results are not claimed.

**Optional live capture was skipped:** requirements A-D are not fully certified
because the full expected state/controller and actual-I/O coupling remain open.
No live boundary was observed or disproven. No executable AX certificate or
reduced prefix can honestly be issued yet.

Next bounded work: reconcile every expected full-state transition with actual
ordinal/journal/hidden-latch evolution, connect guard-preserving admission to
that controller, and prove full actual-provider success/failure coupling ROM-free.
Only then reconsider capture-only replay and certification. This recommendation
does not authorize AX. Stopped after AW3.
