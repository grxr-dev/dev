# Task AW2 - ROM-free divider harness certification, clean retry

**PARTIAL. No executable AX certificate, including a reduced prefix, is issued.**
AX was not executed or authorized. This retry produces useful independently
tested canonical/preflight/controller code, including disposal from a real
runtime observer, but does not claim that a complete trustworthy live AU entry
provider or AU-to-controller guard handoff exists.

Authority: AW `71f28f7ecc87388691c4c68589811d4322d05863`, AV
`524acc6bead2768183e45ae4913b00ea811b274b`, AU
`f17f95ae2b2a15f7fced6f04d82d2593350d37a4`; ndsrecomp
`3a57236bb23d25dcb4caad7d58d733311062ff5e`. ROM SHA-1 identity is
`b8a105bacc3234dede8d4465df0869f2b922a0e2`. No ROM, save, checkpoint or
Brain Age image was opened by the AW2 certification helpers. No Brain Age
process/interpreter was launched, no original opcode executed, and no runtime
MMIO access occurred. Synthetic scalar representations and host timing queries
at the candidate's addresses are not guest execution.

The earlier failed attempt is historical, not a task result. Four uncommitted
scaffolding files were present when this clean retry began; they were preserved,
checked against authority, and included only after new tests. Unrelated
`jarvis-inbox-v1.zip` remains untouched/untracked.

## Exact blocker and current source ordering

AW's root finding still holds. `io.cpp::start_div` replaces one deadline with
`(active ARM9 cycles >> 1)+34` for mode 1. `runtime_arm.cpp::nds_reschedule_slice`
only shortens the cap, so replacement of a divider deadline does not undo an
earlier shorter cap. RtBus performs MMIO before instruction-cycle commit.
Tier-3's retired observer is before IRQ acceptance; a slice exit can occur before
the next instruction-entry guard. `nds_halt` returns through `run_slice`, and
`scheduler_run_round` still has its timer/GPU/ARM7/display/SPU/Wi-Fi/RTC/system
event tail. A halt flag remains insufficient.

There is a second concrete integration edge, not merely a missing test flag:
`tools/task_au/setup.inc::au_control`, index 7, verifies the exact pending
`0x02001980` STRH **must not dispatch**, then calls `finish(0)` and returns 2.
`diagnostic.h::finish` uses `nds_halt`. In `tier3.cpp`, AW's instruction observer
runs before that AU control, but installing an observer does not transfer AU's
guard ownership. Historical AU access guards also precede the added AW access
observers. Silencing/disabling those guards would not be certification.

`tools/task_aw2/review.py` checks pinned framework identity, AW source hashes,
the five AW-installed source hashes, instruction/retired/cap/tail observer
ordering and the preserved AU stop. **AW2 changes no runtime source, generated
C, ROM, scheduler semantics, runner executable or prior evidence.** The new
native test is a separate executable, linked to real runtime/bus/CP15/scheduler
units and device stubs; it is not a relinked or launched game runner.

## Seven missing-certification items: exact disposition

| AW item | AW2 disposition | Remaining obligation |
|---|---|---|
| 1. Trusted cap provenance and copied-state cost classification | **PARTIAL.** Pure cap-chain replay and overflow/debt/stale-cap rejection implemented. Actual typed CP15/publication snapshot and prospective costs compared against real runtime functions for all 12 instructions. | No runtime-owned journal covers slice begin, every cap setter/reschedule/import and the AU entry epoch. The fixture's cap records are not trusted live provenance. Publication fields do not capture every hidden last-access/page latch. |
| 2. Complete passive readiness | **PARTIAL.** Derived IRQ/cache, ARM7 lag/debt/lifecycle, deadline, periodic RTC/SPU/LCD, cap/fast-limit, DMA and conservative disabled-timer predicates with negative tests. | Complete actual I/O/peripheral/periodic phase and scheduler-latch capture is not projected into the new schema. Enabled timers, synthetic-event configuration and other unclassified service state reject, not normalize. |
| 3. Canonical logical identity | **CLOSED for AW2's identity/preflight/ledger format.** No raw-object comparison or hashing. Every protected field tested for mutation/removal/width, round trip and stable digest. | Historical AW raw-copy format remains available for its old report; AW2 explicitly refuses to arm from it. A full live canonical provider is still item 2/7 work. |
| 4. Immutable AU manifest binding | **PARTIAL.** Immutable authority-checked 74 scalar anchors and five identity strings are bound to preflight; each mismatch rejects. | Actual RAM/DTCM/save/code/ROM observation-to-hash binding is not supplied by a complete live provider. AU did not record the required divider operands/results/deadline or timing/cap/peripheral baseline; synthetic values are not promoted to AU facts. |
| 5. Complete transcript/controller | **PARTIAL.** Strict 77-observation conditional plan, sticky ordered ledger and controller implemented; omissions, duplicates, reordering, wrong accesses/results/models/costs/clocks and forbidden service tested. | Full original-runtime event-to-canonical-state projection, bookkeeping/hidden timing transitions and instruction guards are not certified. No actual Tier-3 candidate was run. |
| 6. Prospective guard plus AU terminal/failure replacement | **PARTIAL.** Source-derived guards and shared flush/close + `_Exit` controller tested end-to-end. | No reviewed AU terminal/access-guard ownership handoff exists. AU's old halt path is preserved, not bypassed; non-observer failures/yields still need a dominating task-scoped disposal fence. |
| 7. Actual snapshot/ledger-to-disposal coupling | **PARTIAL, substantially stronger than AW.** Positive complete synthetic controller test plus eight failure children; one failure originates inside the real `nds_reschedule_slice` observer using actual copied cap/cycle/register scalars. | Actual full live AU snapshot -> immutable manifest -> every original instruction -> successful terminal is not certified. The real-runtime test deliberately uses synthetic surrounding peripheral/hash state and cannot establish that path. |

This is not BLOCKED on a demonstrated need for broad scheduler redesign. The
implementation/certification is incomplete at three narrow integration seams:
trusted complete live entry capture (including cap history), live immutable
baseline binding, and preserved-guard AU/controller transfer with complete
event projection/disposal fences. No caller can close them by setting a truth
flag or comparing a snapshot with itself.

## Canonical snapshot and manifest

`tools/task_aw2/canonical.h` schema `AW2S`, version 1:

- Four ASCII magic bytes, little-endian uint16 version.
- Little-endian uint32 field count, then lexicographically sorted ASCII keys.
- Key length is uint16; key bytes have no terminator. Each cell has an explicit
  width byte (1/2/4/8), then that many little-endian unsigned value bytes.
- Hash section: uint32 count, sorted keys, uint16-length lowercase hexadecimal
  strings. Image hashes are SHA-256; ROM identity is SHA-1; framework identity
  is its Git commit SHA. The map key fixes the meaning.
- Bounds, overflow, unknown schema, duplicate/noncanonical ordering, truncated
  data, extra bytes and invalid keys/digests reject. No pointer, padding, vtable
  or object-layout bytes enter identity. SHA-256 is over the canonical bytes.

`observed_timing.h` copies explicit members from the pure CP15 exporter and the
published code-class globals. It does not invoke timing classifiers, resync,
device service or guest reads while copying. Real timing queries are called
only afterward on synthetic host state to compare the independent model.

`manifest.json` / `au_manifest.h` bind all sixteen AU registers, CPSR=0x1F,
ARM9/ARM7 clocks and ordinals, 12 candidate words plus forbidden ANDS, both
literal values, all 35 protected address/width/value observations, the DTCM
stack word, save/request baselines, full main-RAM/DTCM/save identities, ROM
identity and framework pin. `make_manifest.py` checks the source reports against
the authoritative commits and generates identical metadata in memory. It never
reads image bytes. Unrecorded AU divider/timing/service classes are explicitly
listed rather than fabricated.

Canonical AU-anchor digest:
`174535cef7bbfb1b499f3b256593019731199c9bc49a5ab35ce23697841c2af5`.
Synthetic complete-entry digest:
`3f26015457e575e952577ef1f14ff03647f79b94769d1dcf1a3603490be58b0d`.
Actual typed timing copy on the synthetic configured runtime:
`40796a700c559ec4d2c6275eb1b8e97e68f5bc7691eb6b556caa969d1d7a141e`.
These are distinct evidence classes; none is a measured live AU peripheral hash.

## Passive readiness and timing/cap derivation

The pure classifier implements highest-priority MPU-region selection from copied
C1/cache bits/region words. Unknown/stale publication class or generation, TCM
overlap/unclassified mapping and uncertified data regions fail closed. Cached
ARM fetch timing uses **PC+8**, not PC, for the 32-byte boundary. Literal numD=3,
uncached MMIO numD=8; the source overlap expression is
`max(max(numC,numD), max(numC+numD-6,0))`. BX/BL replace the source fetch with
the target cached refill (3+1 here). Debt is required zero. All twelve predicted
costs match the actual bus/runtime cost functions on configured synthetic state.

Cap replay requires a bounded complete chain, an exact slice origin/base/quantum,
monotonic epochs/clocks and matching before/after values. Reschedules take the
minimum of the old cap and checked `deadline*2`; unknown setters/CPU switches,
missing history, stale clock, impossible conversion or overflow reject. This
validates supplied records; **the trusted live recorder is not implemented**.

The readiness predicate derives IRQ eligibility from IME/IE/IF and checks cached
agreement, captures slot/debt/stop/backend ownership conditions, and rejects
pending DMA or unclassified timers. It derives the scheduler's next LCD/SPU/RTC
deadlines from the copied system timestamp with checked arithmetic. Copied
card/SPI/aux-SPI/sqrt/Wi-Fi deadlines must exceed the prospective terminal system
time. Divider busy/deadline consistency and inherited-deadline readiness are
checked; later writes replace the scalar deadline, not an invented queue ID.

**ARM7 catch-up must not be falsely reported absent.** AU's stored ARM7 clock
1708437825 is already 35 system cycles behind `3416875721>>1`. At the conditional
terminal it would be 67 behind. The model preserves this relation. Isolation
would follow only from a certified uninterrupted ARM9 slice and nonreturning
disposal before the scheduler tail, not by inventing an ARM7-ready=0 flag or
changing the slot clock. The current live path has not established that fence.

## Prospective transcript and terminal controller

`model.h::transcript` produces a conditional plan from an entry that passes the
logical guards. Each instruction has an entry/prospective check, a fetch
before/after pair with exact opcode, its data-access pair if any, nested cap
change if shortened, committed cost/clock/CPU state and retired observation.
All CPU/manifest identities and observed model fields must match. BX/BL active
return-stack changes are represented. Actual hidden latch/accounting transitions
still require a complete provider; this plan is not a substitute interpreter.

Before dispatch, checked prospective cost must leave the clock **strictly below**
the retained cap, including a cap shortened by the pending write. Readiness
must hold through that clock. MMIO model changes are specified before cost
commit. The final read additionally requires DIVCNT=0x8001 and a future divider
deadline. Unexpected service of any scheduler/device/IRQ/ARM7 kind always fails.

`controller.h::Controller` obtains a passive-source snapshot, records canonical
identity, constructs the manifest-bound ledger, and subscribes to AW's observer
ABI. Every observation is logged with index/metadata/clock/state digest. The
first mismatch is sticky and immediately flushes/closes failure evidence then
`std::_Exit(79)`. Complete final retired observation flushes/closes the final
canonical state and exits 73. Audit failure exits 78. No `nds_halt`, exception
unwind, destructor, atexit, persistence shutdown or scheduler return is used.
Observer exceptions also retain AW's nonreturning failure behavior.

The real-runtime child seeds only synthetic host globals, supplies the first four
synthetic observations, then calls the real `nds_reschedule_slice` with a wrong
earlier deadline. The callback receives the actual copied cap=3416875786,
fails the exact ledger and exits **inside that function**, before its remaining
fast-limit-clear statement/return. Its surrounding divider/hash states are
explicitly fixture data, not live AU evidence.

## Tests and disabled behavior

Authoritative local evidence:
`local/task-aw2/retry-20261013/certification-003/tests.json`, `commands.json`,
nine child `audit.jsonl` files, and `source-review.json` in the retry root.

- **1,170 ROM-free assertions**: canonical/hash/width/presence mutations, every
  immutable manifest class, unknown attestations, timing/class/region/TCM changes,
  cap origin/chain/shortening/wrap, IRQ/debt/ARM7/device/deadline readiness,
  exact 77-event transcript, every duplicate/missing event, wrong access metadata,
  result/model/post-MMIO clock, wrong committed cost/clock and extra terminal work.
- **28 checks linked to actual runtime units**: repeated typed passive copy,
  canonical round trip, all twelve prefetch/full-cost comparisons, and original
  disabled cap retention/shortening behavior. No guest interpreter is linked.
- **Nine child processes**: success, bad preflight, legacy raw provider, wrong
  MMIO, IRQ, cost, debt/state, missing final event, and real-runtime cap mismatch.
  All expected exits match. Scheduler/device/IRQ/ARM7/shutdown/destructor/atexit
  sentinels are absent; real-runtime return sentinel is also absent.
- File-only review verifies the current AW runtime sources and AU guards unchanged.

The separate native target uses existing savestate-test device stubs that abort
on unsupported accesses. A missing test ABI payload symbol was supplied with an
abort stub, not a guest implementation. Existing runtime compiler warnings were
not changed. Initial TCM/incorrect test-index and local executable-resolution
failures were corrected; earlier evidence directories are retained, not passed
off as certification. The final fresh suite passes.

New code has no environment activation/installation, and AW's observer remains
null in ordinary runs. Thus headless/SDL binaries and normal scheduler/timing
semantics are preserved. This is source/ROM-free disabled behavior evidence, not
a gameplay, compiled-parity or live-divider result.

## Conditional route retained - NOT an executable AX certificate

Start `0x02001980`, stop `0x020019B8` after one read at `0x020019B4`, before ANDS
fetch/accounting/dispatch. Costs/cumulative ARM9 cycles:

| PC | Cost | Cumulative |
|---|---:|---:|
| 02001980 | 8 | 8 |
| 02001984 | 1 | 9 |
| 02001988 | 8 | 17 |
| 0200198C | 1 | 18 |
| 02001990 | 3 | 21 |
| 02001994 | 8 | 29 |
| 02001998 | 8 | 37 |
| 0200199C | 8 | 45 |
| 020019A0 | 4 | 49 |
| 02001A20 | 4 | 53 |
| 020019B0 | 3 | 56 |
| 020019B4 | 8 | 64 |

Conditional MMIO: W16[04000280]=1; W32[04000290]=0;
W32[04000294]=1000 hex; W32[04000298]=1000 hex; W32[0400029C]=0;
R16[04000280]=8001. Write deadlines respectively 1708437894, 1708437899,
1708437905, 1708437909, 1708437913. DIVCNT becomes 8001; numerator high:low
becomes 1000:0, denominator high:low 0:1000. Inherited quotient/remainder are
preserved, not inferred. Latest deadline remains 1708437913 at the read.
Retained cap is `min(entry cap,3416875788)` under the specified valid nonzero
entry chain. Final ARM9 clock=3416875785, ordinal=281098020. Conditional final
r0=8001, r1=04000280, r3=1000, r12=0, SP=027E3654, LR=02001A24,
PC=020019B8, CPSR=1F/NZCV=0000; other registers unchanged.

Conditional RAM/DTCM/protected-field/save deltas and logical save/Flash activity
are zero. Their required AU hashes remain those in the manifest. These are model
invariants, **not newly observed guest before/after results**. Forbidden ANDS
`E2100902` would add 3 and reach the first shortened cap; it, further reads,
divider completion, IRQ acceptance and all scheduler tails are excluded.

**No safely reduced positive prefix can be certified from the current binding:**
the first instruction is already a forbidden AU MMIO write and live trusted cap/
readiness/guard transfer are missing before it. A purely synthetic success must
not authorize it.

## Remaining next work (no AX execution)

Finish the task-scoped live canonical entry provider and trusted cap journal;
bind actual immutable observations and all readiness phases; implement a reviewed
AU-to-controller handoff preserving the entire prior prefix/denial guards and
covering non-observer failure/yield paths. Test the complete actual provider and
event projection ROM-free, then reconsider certification. This recommendation
does not authorize Brain Age execution or AX. Stopped after AW2.
