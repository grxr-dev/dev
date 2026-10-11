# Task AW ? divider diagnostic harness safety

**PARTIAL. AX executable certificate withheld.** No Brain Age process was
launched, no ARM instruction was evaluated, no Brain Age MMIO occurred, and no
save/checkpoint was changed. The native synthetic test uses ordinary C++ fixture
data, not an interpreter. The harness now has useful tested primitives and inert
runtime observation points, but complete live preflight/transcript/disposal
coupling is not yet certified. Do not execute the AV candidate.

Authority: AV `524acc6bead2768183e45ae4913b00ea811b274b`, AU
`f17f95ae2b2a15f7fced6f04d82d2593350d37a4`; pinned ndsrecomp
`3a57236bb23d25dcb4caad7d58d733311062ff5e`. Branch `codex/brainage`.
ROM identity remains `b8a105bacc3234dede8d4465df0869f2b922a0e2`.

## Exact root blocker re-established

In `runner/src/tier3.cpp`, RtBus calls the underlying bus while instruction costs
are still uncommitted. `io.cpp::start_div` replaces one scalar deadline with
`(g_runtime_cycles >> 1) + 34` in mode 1 and calls `nds_reschedule_slice`.
`runtime_arm.cpp::nds_reschedule_slice` only shortens `g_cycle_cap`; later writes
do not lengthen an earlier shortened cap. No older independent divider event
survives. `nds_run_system_events` checks the latest deadline and runs `finish_div`
only when due. Source audit verifies the divider model bodies against the pinned
baseline, removing only AW's inert system-event entry observer for comparison.

Tier-3 commits cycles, adjusts call/return bookkeeping and can accept an IRQ or
exit at slice expiry before the next instruction-entry guard. AU's `finish`
calls `nds_halt`, which sets `g_nds_terminal` and requests yielding. In
`scheduler.cpp::run_slice`, that flag breaks the dispatch loop, saves slot cycles
and **returns normally**. `scheduler_run_round` then still ticks ARM9 timers,
runs GPU3D, catches ARM7 up to the actual rendezvous and services display/SPU/
Wi-Fi/RTC/system events. The frontend checks terminal state only after that round.
Halting either/both slots is not a scheduler-tail barrier.

These exact edges, the cycle commit/IRQ/slice ordering and divider cap replacement
are mechanically checked by `tools/task_aw/analyze.py`. The old AV checker is
intentionally not edited: its strict system-event body comparison fails after
inert instrumentation. AW checks the same original model with only its added
observer removed. No timing/guest semantics were normalized to satisfy a gate.
File-only hashing also verifies 105 original AV inputs unchanged, including the
ROM, AU retained images/save/checkpoint and unaffected framework source.

## Implemented source

`tools/task_aw/bridge.h`: null-by-default observer, event types, explicit local
audit serialization, and process disposal. No environment variable installs an
observer. Observer exceptions immediately dispose instead of reaching existing
`std::exception` catches that would call `nds_halt`.

`harness.h`: pure exact preflight and a sticky-failure ordered ledger. Required
maps/blobs must be present and exactly equal the independently supplied contract;
unknown/extra fields also reject. Exact AU r0?r15, CPSR=0x1F, ARM9
cycle=3416875721/ordinal=281098008 and ARM7 slot cycle=1708437825/ordinal=96026779
are checked. Entry cap must be zero or strictly greater than 3416875785. Debt,
IRQ-ready, ARM7-ready, device-ready and stop-ready must be zero; copied timing
must certify cached code, literal numD=3 and MMIO numD=8. A due inherited divider
deadline rejects. Empty ledger, complete plan and explicit source/timing/provenance
attestations are required. Those attestations default false; they are caller
obligations, not automatically established proofs.

`passive.h` plus `runtime.inc`, `scheduler.inc`, `bus.inc`, `io.inc`:
copy live CPU/registers/flags, active CPU, ARM9 cycles, both instruction ordinals,
cap, fast limit, debt, yield/stop/event/unwind flags, return stack, both stored
scheduler slots/clocks/return stacks, current slot, system timestamp, in-round and
owner-thread status; CP15 visible state/MPU/cache/permission maps/generation;
code/data timing latches/class publication; complete main RAM and DTCM; I/O core
including IRQ enables/flags, halt/DMA/timers; divider control/operands/results/
deadline; card/SPI/aux-SPI/sqrt deadlines; save bytes/dirty flag. Divider event
identity is its **scalar deadline**, not an invented queued-event ID. No
`save_current`, scheduler checkpoint export, bus/MMIO read, timing-classifying
helper or device advancement is invoked by these providers. Scheduler slot
copies retain stored state; live active CPU/time is recorded separately.

`install.py`: checked one-occurrence source anchors install only these committed
ROM-free helpers into the local pinned framework. Before/after source hashes are
local. Tier-3 emits pre-instruction (before AU/bank/accounting/fetch), pre/post
RtBus accesses with read results, post-cycle-commit, and retired-after-call-stack/
before-IRQ events. Rescheduling emits cap-change. Scheduler round, ARM7 slice,
first scheduler-tail service, IRQ-acceptance and timer/RTC/system-event entry
sites are observed before their side effects. The first tail fence dominates the
remaining GPU/display/SPU/Wi-Fi/RTC work on this path. This is **not** a claimed
exhaustive per-device global callback framework or compiled-path observer.

The expected ledger contract includes full snapshots after accesses and commits;
kind/PC/address/width/read-write/value/result and every copied field must match
the ordered plan. IRQ/scheduler/device/ARM7 events always reject, even if listed
in a plan. Unarmed access, rearm, omission, reordering, extra entry, incomplete
terminal state and post-failure continuation reject. A future controller must
capture the state at each event and connect rejection to disposal **before** the
underlying side effect. This coupling is not implemented/certified for AX yet.

## Terminal primitive and synthetic proof

`dispose(FILE*,code)` explicitly flushes/closes the audit, then calls
`std::_Exit(code)`. Flush/close/missing-audit failures hard-exit with 78; observer
exceptions dispose with 79. No C++ unwind, static destructor, atexit callback,
normal save shutdown or scheduler return follows. This avoids the joinable-thread
destructor risk of ordinary `std::exit` and the AU halt-tail gap.

`check.py` builds/runs a standalone native test with `-Wall -Wextra -Werror`:
**147 assertions** cover synthetic exact acceptance, nonmutation, every numeric
and byte-field mismatch/removal, AU registers/flags, extra/missing fields, cap,
divider deadline/event identity, IRQ/ARM7/device readiness, timing/debt/owner,
unsealed contracts, nonempty ledger, empty plan, ordered-event and sticky terminal
failure, forbidden service and disabled behavior. Fixture peripheral/timing
values are labeled synthetic, not reconstructed AU evidence.

Two child processes test the same terminal primitive: success exits 73 after
retaining a complete synthetic snapshot and ledger count; observer failure exits
79 and retains failure audit. Scheduler-tail/device/ARM7/shutdown-save sentinels
placed after the hook are never reached; a static destructor sentinel is also
absent. This proves **process-disposal mechanics**, not execution of the actual
scheduler tail or a certified live Brain Age controller. The distinction matters.

Five actual runtime object files (runtime_arm, bus, io, tier3, scheduler) compile
with the installed inert support. Runner binaries were not relinked or launched;
historical headless/SDL executables and evidence remain intact. Existing source
warnings are unrelated. Initial BOM/compiler-test warnings were fixed locally.
Disabled observer is null: no snapshots, callbacks, disposal or added `sync_out`
execute, and normal scheduler/device/IRQ behavior is unchanged by inspection and
the synthetic disabled-path control. No gameplay/compiled parity is claimed.

## Why no executable AX certificate can yet be issued

The collector intentionally does **not invent** cap-source provenance, cached
timing/cost classification, complete peripheral/periodic readiness, stop readiness
or ARM7 catch-up predicates. Required preflight fields/blobs are absent, so its
current live output cannot arm the checker. Raw copied C++ structures also need
canonical logical serialization (padding can reject spuriously). There is no
trusted AU image/code/ROM identity manifest loader, complete runtime transcript
controller, prospective-cost/cap guard or terminal controller replacing AU halt.
AU's old guards still forbid these MMIO writes. A caller setting three booleans
or comparing a snapshot against itself is **not** certification.

Consequently this is not FULL PASS. The process primitive needs no broad runtime
refactor, so it is not BLOCKED on scheduler architecture either. Remaining work
is narrow but safety-critical. Do not fill missing fields with guessed constants,
strip AU guards or execute the candidate on the strength of synthetic tests.

## Conditional AV candidate retained ? NOT an AX certificate

Start `0x02001980`, before STRH; terminal `0x020019B8`, after exactly one status
read at `0x020019B4`, before ANDS fetch/accounting/dispatch. Twelve PCs and
conditional cycle costs:

| PC | Operation | Cost / cumulative ARM9 cycles |
|---|---|---|
| 02001980 | STRH control=1 | 8 / +8 |
| 02001984 | MOV r12=0 | 1 / +9 |
| 02001988 | STR numerator low=0 | 8 / +17 |
| 0200198C | MOV r3=1000 hex | 1 / +18 |
| 02001990 | LDR denominator pointer literal | 3 / +21 |
| 02001994 | STR numerator high=1000 hex | 8 / +29 |
| 02001998 | STR denominator low=1000 hex | 8 / +37 |
| 0200199C | STR denominator high=0 | 8 / +45 |
| 020019A0 | BX LR=02001A20 | 4 / +49 |
| 02001A20 | BL 020019B0; LR=02001A24 | 4 / +53 |
| 020019B0 | LDR DIVCNT pointer literal | 3 / +56 |
| 020019B4 | LDRH status=8001 conditional | 8 / +64 |

Expected conditional MMIO accesses:

| PC | Address / width / value | Pre-write/read ARM9 clock | New system deadline |
|---|---|---:|---:|
| 02001980 | 04000280 / W16 / 1 | 3416875721 | 1708437894 |
| 02001988 | 04000290 / W32 / 0 | 3416875730 | 1708437899 |
| 02001994 | 04000294 / W32 / 1000 hex | 3416875742 | 1708437905 |
| 02001998 | 04000298 / W32 / 1000 hex | 3416875750 | 1708437909 |
| 0200199C | 0400029C / W32 / 0 | 3416875758 | 1708437913 |
| 020019B4 | 04000280 / R16 / 8001 | 3416875777 | unchanged |

Each write restarts busy, DIVCNT=8001; operands change only in the listed words.
Inherited quotient/remainder remain unchanged, never guessed. Final numerator
high:low=1000:0, denominator=0:1000. Retained cap is
`min(nonzero entry cap,3416875788)` (zero becomes 3416875788). Final ARM9 clock
3416875785/ordinal281098020; ARM7 slot/ordinal and scheduler timestamp unchanged.
Required entry relations remain AV's: exact immutable AU CPU/RAM/DTCM/save/code,
cached code at every PC/branch target, literal=3, MMIO=8, debt=0, entry cap zero or
greater than final clock, no pending IRQ/halt/DMA/stop/service, and fully audited
return-stack/timing/device state. These relations are specifications, not measured
live facts.

Conditional final r0?r12: `8001,04000280,04000290,1000,020EA1BC,0,DA,020E9A00,
1000,1000,020FD00C,0,0`; SP=027E3654, LR=02001A24, PC=020019B8;
NZCV=0000, T/mode/I/F=0/31/0/0. Twelve fetches plus two literal reads and one
status read = 15 reads; five MMIO writes. No architectural RAM/DTCM/stack/save/
mapped-field changes; quotient/remainder invariant. Main RAM SHA-256
`84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340`, DTCM
`a5313aa2084674d767307c09ebd86fb888ebf992b8f486602412f9499c55496f`, save
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb` remain required.
Forbidden ANDS at B8 would retire at +67, meeting the retained first-write cap;
second poll, quotient read, completion, IRQ and all scheduler tails are excluded.
The required terminal assertion is explicit audit retention then process `_Exit`
from the final retired boundary, never `nds_halt`; it remains unbound to AX.

## Artifacts and next authorization

Local: `local/task-aw/tests.json`, `terminal/terminal.jsonl`,
`failure/terminal.jsonl`, `compile.log`, `installation.json`, synthetic executable.
Committed: this report/result and ROM-free `tools/task_aw/`. No runtime binary,
state, screenshot, ROM, SDK or generated C is committed. Unrelated
`jarvis-inbox-v1.zip` is preserved untracked.

Recommended next authorization: **finish AW live-state/controller certification
ROM-free**, including complete passive predicates/canonical fields, immutable
manifest and exact runtime-event-to-process-disposal tests. Only afterward may a
separately authorized AX evaluate live eligibility; no candidate dispatch until
the complete preflight passes. Stopped after AW; AX was not executed.
