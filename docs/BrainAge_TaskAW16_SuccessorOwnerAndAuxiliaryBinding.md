# AW16 ? owned tail and immutable auxiliary binding

**FULL PASS for ROM-free, conditional static readiness.** AW15's two static
blockers are closed: an explicit one-use successor consumes the completed
AW7/AW12 receipts, and fresh passive auxiliary observations are sealed into its
full-state ledger. The source-coupled path ends immediately after ordinary
ARM9 slice-begin, **before any guest re-entry**.

This is not a live validation, a resumed AW14 process, a B4/status-read
certificate, or permission to execute anything. Original runtime files,
checkpoints/saves and consumed permits remain unchanged. No ROM/save/checkpoint
was opened, no runner was linked/launched, and no Brain Age instruction/MMIO
executed. Only framework source/scalar tests and syntax checks ran.

## Authority and exact entry

- AW15: `12710efe8a81c15f91a86a637704573899f9cf38`.
- AW14: `9c2b342f4fdf1f09316ce7d62ac2240edc0f9589`.
- Framework: `3a57236bb23d25dcb4caad7d58d733311062ff5e`.
- AW14 core: **411 scalars/five identities**, canonical SHA-256
  `3528c2be122178850a3d3c78157cdd1adaf5409e5eb32f6d794e1c3f81d27d84`.
- GPU: **19 scalars**, SHA-256
  `708de6de2568d09123820267c9daaa7abd49321e90e275923ac93d96513ad5d4`.

PC is `020019B4`, ARM9 cycle **3416875777**, retained cap **3416875778**;
ARM7 cycle **1708437825**, HALT **1**, parked debt **2**. Existing AU/prefix
guards and the 69-event receipt remain mandatory. AW14's eight ownership-chain
records, ticket **1**, frame **566**, no saved unwind latch and no parent frame
are preserved. The last parent chain is
`10bad78f6ef2fd96a21b26be7e074943e6ded5fa5541844c731d3e39892472b4`.

The seven non-GPU-wrapper source files are checked against AW15's authenticated
source-evidence hashes. The GPU wrapper is checked against its complete pinned
framework Git blob. Existing AW11/AW12 source/guard checks are retained.

## Successor ownership, not observer removal

`hooks.py` creates a reversible **ignored private overlay**. Originals and old
reports/controllers are not edited. It composes AW12 and adds one guarded offer
after the original fence has validated and audited its eighth stage.

`AW16_DIAGNOSTIC_TAIL` alone does not arm anything. Explicit host arming uses
fixed passive getters; default arming rejects. Admission requires:

1. The actual AW12 object's private admitted phase, audit/cursor/ticket/frame/
   chain; actual spent latch, global ticket/frame serials and owner thread.
2. The actual AW7 ledger complete at 69 observations/11 instructions, 18 bus
   calls, no active access/failure and unchanged observer ownership.
3. A recomputed original expected plan, logical per-event chain and invariant
   seal. Every later phase rechecks this receipt, not just a supplied boolean.
4. Exact core/GPU binding and repeatable fresh auxiliary/core/GPU samples.

Only then does the parent enter the new `transferred` phase and the **non-null**
observer atomically change from AW7's completed ledger to the successor ledger.
The old receipt/seal remain immutable; AW7 access checks and AW12's guest-frame
guard remain active. Missing/lost/duplicate ownership, stale epochs, unexpected
events or an attempted dispatch dispose nonreturningly. No return to ordinary
guest redispatch is a fallback.

## Passive auxiliary schema and immutable seal

The separate **19-cell** extension uses the existing sorted, explicit-width,
little-endian AW2S v1 encoding, with `aux.schema:u16=1`. It contains no padding,
raw pointers, callback addresses or thread-ID representations.

| Cells | Width/source and admission |
|---|---|
| `journal.bound` | u8; runtime-owned AW3 seal latch; must be false so original cap-note may establish a new epoch |
| `overlay.enabled` | u8; actual `g_live.enabled`; must be false |
| `wifi.network_enabled`, `wifi.bridge`, `wifi.device`, `wifi.worker`, `wifi.scheduled` | u8; configuration, object presence, worker pointer presence and actual `HasPendingEvent`; network/worker/scheduled must be false |
| `wifi.raw_deadline`, `wifi.timestamp` | u64; actual scheduler slot and CurrentSystemTimestamp; absent bridge has explicit zero representation; timestamp may not exceed rendezvous |
| `trace.count`, `trace.last.count`, `trace.last.cycle` | u64; existing const run-trace getters; last-record provenance must match; count overflow rejects |
| `trace.last.before`, `trace.last.after`, `trace.last.debt_before`, `trace.last.debt_after` | u32; logical GXStat/signed-cycle bit patterns, not struct bytes |
| `scheduler.modulus`, `scheduler.sample` | u64/u8; actual cached profile modulus and active sample flag; both must be zero |

No flag is cleared or populated from a witness to obtain admission. The exact
extension is sampled twice, hashed/audited at entry and compared field-for-field
throughout. All values remain fixed except the modeled Wi-Fi timestamp update
and single GPU trace append. Both bridge-present and bridge-absent paths, a
bridge without a Wi-Fi device, and trace-ring index wrap are covered.

AW14 did **not** measure these new auxiliary values. Test values are synthetic
witnesses, not recovered historical facts. A later validation must obtain them
from the fixed live getters; unsupported readiness rejects before tail service.

### Deliberately noninterfering state

- Disabled Overlay returns **before** reading/incrementing its local countdown
  or touching work queues/bank publication. Those internals cannot affect this
  admitted path, even if host preparation bookkeeping changes.
- With no scheduled Wi-Fi event, callback/parameter/packet/transport internals
  are not read by event service. A present idle bridge/device only publishes
  its timestamp. Host network/worker operation is conservatively rejected.
- The GPU early-out performs no geometry/renderer work. Its wrapper's one
  append has a checked ordinal/index and exact new record. Other diagnostic
  history cells are not used to select scheduler/device behavior; this is not
  a claim that the entire history ring or GPU object was hashed.
- Scheduler profiling is excluded by measured modulus/sample predicates.
  PC-frequency notes and host attribution bookkeeping have no guest/device/
  cap inputs or outputs. No new guest slice is entered through these helpers.

No remaining scheduler-affecting auxiliary field is knowingly unbound within
this conservative branch. This is not certification of enabled Overlay,
network service, GPU work, sample profiling or arbitrary device states.

## Exact 26-stage path and terminal

The ledger checks admission; the original scheduler-device and ARM9-timer
observers; timer9 completion; GPU completion; ARM7 slice gate/observer/HALT
completion/timer observer/completion; power check; display; SPU; Wi-Fi; RTC
observer/completion; system observer/completion; time publication; Overlay;
round exit; next scheduler observer/round entry; target selection; ARM9 slice
gate; and **slice-begun terminal**. Missing/extra/reordered observations reject.
Actual original observer kinds, phase/index and all canonical snapshots are
chained and independently checked. No protected field is discarded.

The deterministic source effects remain AW15's:

- Rendezvous **1708437888**; timer 0 counter/accum **14558/62**, timer 4
  **50776/43**, timer 5 **64195/39**; both timer timestamps equal rendezvous.
- ARM7 advances its HALT timestamp by **63**, with zero instructions and debt
  **2** unchanged. No timer IRQ, GPU command, display edge, SPU mix, Wi-Fi/RTC
  callback, system completion or IRQ acceptance occurs.
- GPU facade ARM9Timestamp becomes **3416875777**, GPU Timestamp becomes
  **1708437888**, and the diagnostic trace appends once.
- Divider deadline **1708437913** is still pending. It wins next-target
  selection over LCD/SPU/RTC deadlines; next ARM9 target/cap is **3416875826**,
  quantum **49**.
- Original slice-begin, not normalization, resets cap epoch **496?497**,
  serial **506?507**, scheduler round epoch **1168?1169**, and six journal
  records to one. The old complete history remains bound in preceding states.
- Fast limit becomes **0**, yield hint stays **1**, unwinding stays **1**;
  ARM9 cycle/registers/NZCV/PC remain unchanged.

The terminal core has **361 scalars/five unchanged identities**, SHA-256
`68b88b2de2264fb8fc456422de7aa026a8ac00685268f8cd8ea5650d3b01f773`.
The 50-field reduction is precisely the source-defined journal replacement,
not a removed guard. Final GPU hash is
`4283d85effe5028f12adbe1fe495174d9eda117d65f7accc0eb9e248f5b189d9`.
The final auxiliary hash is a deterministic function of the freshly sealed
extension, **not** a substituted synthetic constant.

Success and failure flush/close the same exclusive audit and `_Exit` (73/79;
IO failure 78). The success hook is immediately after `nds_slice_begin` and
before wake/dispatch logic, unwind clearing, B4 fetch/accounting/dispatch or
another pre-device fence. There is no `nds_halt()` path or scheduler/persistence
tail after disposal.

## Certification evidence and limits

Final evidence: `local/task-aw16/certification-010/`.

- **87 native assertions**, including every auxiliary omission/width/identity,
  entry scalar/identity negatives and inactive-branch noninterference.
- **35 children:** four full successes, 29 independent fail-closed negatives,
  one legacy AW12 fence control and one default original-redispatch control.
  No post-terminal scheduler/device/IRQ/ARM7/shutdown/persistence sentinel ran.
- **Four independent complete-state oracles** check all 26 stages; **14 audit
  tamper cases** reject missing/duplicate snapshots/stages, wrong kind/index,
  chain/order and entry-seal mutation.
- **16 actual-source syntax checks** cover default, legacy and successor modes,
  including real Overlay/Wi-Fi/GPU types. No runner is linked.

The rail executes extracted original framework service/scheduler functions on
bounded synthetic objects and original mutable runtime/scheduler/journal getter
bodies. **192 initial mutable core cells** (including 48 device cells) are
projected; **219 readonly cells and five identities** are authenticated historical
metadata, not new image measurements. The initial dispatch stub models an
already-running pre-fence return and feeds the original ledger its certified
model receipt; it is not an interpreter, a B4 dispatch, or new prefix execution.
Fault hooks exist only under `AW16_ROMFREE`, not in the actual-type builds.

All original source/evidence/locks remain unchanged. Default hooks are inert,
arming is unavailable without the explicit diagnostic build, and an unarmed
successor retains AW12's exact terminal fence. No ordinary timing or scheduler
semantics changed. Historical save identity remains
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`;
there is no fresh save measurement or save/checkpoint access in AW16.

## Certificate and exact next safe task

`tools/task_aw16/certificate.json` issues **conditional static readiness for a
later host-only scheduler-tail/new-slice validation**. It issues no guest/B4
read permission and no current replay/validation authorization.

Next: separately authorize one fresh, fail-closed validation of this exact
transition, re-establishing the exact AW14 fence only through an independently
authorized prerequisite and fresh permit. Require the unchanged full entry,
actual predecessor receipts and repeated live auxiliary admission; on mismatch
dispose without service/retry/normalization. If admitted, run only this owned
tail and dispose at the new slice-begin fence. Do not fetch/read B4 or continue
into guest execution. AW14's process is gone and old permits remain consumed.

Stopped after AW16.
