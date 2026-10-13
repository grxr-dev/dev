# Task AW4 - full-state/controller reconciliation

**FULL PASS for the bounded ROM-free AW4 certification. No AX certificate or
execution authorization is issued. No Brain Age process was launched.**

Authority: AW3 `61a1f50676a99b2b11c390c177175f22507807b6`, AW2
`cb7ab39c07fd2d35bf7bdd04bcdda2d06aaf6540`, AW
`71f28f7ecc87388691c4c68589811d4322d05863`, AV
`524acc6bead2768183e45ae4913b00ea811b274b`, AU
`f17f95ae2b2a15f7fced6f04d82d2593350d37a4`; framework
`3a57236bb23d25dcb4caad7d58d733311062ff5e`, ROM SHA-1
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

## Disposition

The concrete AW3 contradiction is resolved without discarding observations.
The old AW2 transcript remains available for its historical proof. AW4 supplies
a separate full-state transition plan and controller; it is not an AX activation
path and is not connected to Brain Age dispatch. The production AU handoff remains
capture-only and nonreturning.

| Requirement | Evidence |
|---|---|
| Expected evolution, rather than a frozen full snapshot | Explicit ordinal, journal, cap, fast-limit, bank-counter, fetch/data, register and return-stack transitions; every other observed field remains exact. |
| Strict 77-observation reconciliation | Two profiles read actual runtime objects at all 77 observations; exact full logical equality, metadata/order, prospective guards and chained identity succeed. |
| Actual provider, not AW3's stubbed I/O rail | Real runtime, bus, CP15, scheduler, I/O/core save source, SPU, GPU and Wi-Fi getter implementations are linked. No replacement I/O/provider getters supply expected snapshots. |
| Failure coupling | Thirty-six actual-provider fault children terminate with flushed failure evidence and exit 79. |
| AU guard/disabled safety | Original AU/Tier-3 source guards unchanged; three existing AU guard-fragment controls preserve armed nonreturn and disabled old-halt behavior. |
| Terminal isolation | Two positive controller children exit 73 at observation 77; no scheduler/device/IRQ/ARM7/guest/old-halt/shutdown/persistence sentinel is reached. |

## Source-derived mutation ordering

`tier3.cpp` emits `instruction` after `sync_out` but before AU control, exit/bank
polling, ordinal accounting and fetch. `nds_has_bank` calls
`lookup_static_cached`; a selected bank discarded by the force-Tier-3 selector
increments `g_nds_force_tier3_misses`. `nds_note_insn_retired` increments the
instruction ordinal as execution begins, not at the later `retired` observation.
`runtime_code_cycles` changes the last-code latch before fetch. Interpreter data
access timing changes the last-data address before the access observer; ordinary
opcode readback does not change that data latch.

`io.cpp::start_div` changes busy/deadline before `nds_reschedule_slice`.
AW3 records every reschedule before the runtime's minimum-cap comparison.
`cap_change` is emitted after a genuine shortening, before clearing fast_limit.
Nonshortening deadline replacements append journal records but emit no cap event.
Instruction cycle commit happens after the access. Return-stack bookkeeping follows
commit and precedes `retired`. When `poll_after` is true, fast-limit publication
occurs after `retired`; its resulting limit/counter is first seen at the next
instruction observation. The controller disposes at final `retired`, before that
publication, IRQ acceptance, slice exit or scheduler tail.

The passive bank classifier uses the existing uncached `lookup_static` selector,
not `nds_has_bank` or its mutable cache. Its validation reads backing bytes/write
provenance, not MMIO. Only logical selected/not-selected results and dispatch epoch
are copied; no function/pointer identity is serialized. The test executable's
synthetic bank bodies abort if called. Real force-Tier-3 lookup accounting is
exercised without calling those bodies or interpreting any opcode.

## Immutable, constant and evolving ownership

The initial actual-provider snapshot has **356 scalars and five identities**.
The final snapshot has **406 scalars** because five ten-field journal entries are
appended. No old entry is removed. The invariant seal contains **318 scalars plus
all five identities**. Initial values of the remaining 38 scalar cells are bound
by the immutable admission/manifest and initial canonical chain root, then checked
by the full transition plan. Dynamic return/cap structure is checked exactly at
every observation, not merely omitted from the invariant projection.

| Class | Fields / exact rule |
|---|---|
| Immutable identity | ROM/framework/RAM/DTCM/save identity strings, code/literal/protected-memory scalars, fixed CPU registers/flags, CP15 permissions/cache/mapping/generation, bank-selection bits and dispatch epoch. Actual AU anchors are still required in a non-test compile. |
| Constant throughout the protected interval | Capture/ROM epoch, scheduler round/target/minimum selected at round entry, system and stored slot clocks, ARM7 ordinal/lifecycle/debt, IRQ masks/cache, timer/DMA/peripheral/periodic readiness, save counters/dirtiness, quotient/remainder, cache class/page/publication and feature/stop/yield latches. Any unexplained change rejects. |
| Ordinals / stamps | Before fetch, ordinal9 advances exactly once per candidate; snapshot_ordinal and capture.end_ordinal equal that counter. They do not increment merely because the passive provider was sampled. capture.end_cycle equals the committed ARM9 clock. |
| Cap journal | Fixed capture epoch; each setup write appends one source-1 ARM9 entry, with serial exactly prior+1, actual predecessor equal prior cap, current precommit cycle, deadline=(cycle9>>1)+34, after=min(before,2*deadline), zero base/quantum for a reschedule. capture.serial and cap.count advance exactly once. Existing entries remain byte-logically identical. |
| Cap / fast limit | The 77-event subset requires the first write to shorten the entry cap. First cap_change observes the new cap and the old fast limit; the following access_after observes fast_limit=0. Later writes replace deadlines but retain the earlier cap. After the first retired poll, an enabled publisher restores the cap and increments its counter once. Disabled publisher modes retain zero and are modeled, not normalized. |
| Bank miss counter | Each instruction's pre-fetch lookup adds exactly the sealed logical bank-selection bit. Both no-bank and all-selected synthetic profiles are tested through the actual lookup function. |
| Fetch / data latches | last-code becomes the current fetch PC; last-data changes only for the eight candidate data accesses, before access_before. Branch refills retain the same cached page/class in this candidate. Unknown latch changes reject. |
| Registers / return stack | Only the candidate's specified MOV/load/branch results change at cycle_commit. BX pops the matching enclosing return before retired; BL pushes its exact return before retired. SP/NZCV/other registers remain exact. |
| Divider model | Five setup writes update only the specified operand/control and deadline. Status read returns 0x8001; inherited quotient/remainder do not change. Model updates are before instruction-cycle commit. |

Admission also requires the complete independently enumerated provider schema:
every mandatory cell/width and all five identity names, including constant service
fields not touched by candidate execution. All 356 entry-cell omissions and width
mismatches reject before binding. A smaller provider cannot silently seal a smaller
protection set. The schema is checked again at every observation.

Every observed cell is covered by invariant equality or full expected-state
equality (evolving cells are also retained in full canonical observations).
Unknown additions, omissions, widths, rewinds, gaps, duplicate appends and
unmodeled changes cannot pass the expected full map. The copied initial scheduler
minimum is a round-selection fact: it remains constant even as a newer divider
deadline changes the live model. It is not recomputed to erase that distinction.

## Canonical and semantic checks

AW2S v1 is unchanged: sorted explicit keys, widths 1/2/4/8, little-endian values,
explicit identities, no padding, object layout or pointer bytes. Each observation
has a canonical SHA-256. A chained digest binds predecessor ASCII SHA-256,
canonical state bytes, index u64, kind/PC/address/width/value u32 and write u8.
The independent Python auditor verifies this encoding and rejects a tampered
observation. Semantic equality and prospective predicates precede chain advancement;
the chain is not a substitute for transition validation.

`Ledger` admission occurs once while the real journal matches the entry. It does
not re-run entry-era module comparisons against a stale entry after legitimate
evolution. Full invariants and transitions then protect every observation. Missing,
duplicate, reordered, extra, wrong-access/value/model/cost events stickily fail.
Overflow-checked expected construction rejects ordinal/serial/counter/cycle wrap
before admission. Prospective cost/debt/cap/readiness checks remain AW2's original
checks; earlier retained caps, debt, unknown timing and eligible services reject.

## Actual-provider ROM-free test rail

`tools/task_aw4/fixture_*.cpp` includes the real provider-owning translation units
to initialize private runtime objects in a **separate test executable**. It does
not add fixture setters to the runner. Actual CP15 import, slice origin,
instruction-accounting, bank lookup, timing/refill, reschedule, return-stack and
fast-limit functions are exercised. Synthetic divider scalar updates are performed
directly by the fixture, never via an I/O read/write or guest opcode. The event
driver is independent of expected snapshots; each observer obtains a new full
`task_aw3::passive()` sample. No expected Snapshot is installed into the provider.

Actual typed I/O, memory/save hashing, SPU/GPU/Wi-Fi readiness getters are linked,
unlike AW3's device-stub rail. Unused guest Tier-3/overlay entry points are abort
fences. Vendored device/network dependencies are linkage only: no Wi-Fi attach,
network traffic, renderer execution or scheduler service is requested.

A separately labeled synthetic identity profile is required: zero-filled RAM/DTCM
with allowed scalar anchors and a constant artificial save are not the actual AU
images and cannot possess AU's real hashes. Expected identities are computed
independently from that fixture definition; observed identities come from the real
provider's buffers. **Manifest substitution and the controller's test entry point
exist only with `AW4_ROMFREE_CERTIFICATION`.** Positive/negative compile tests also
prove the default production signature cannot accept an override. Non-test preflight still
requires the unmodified AU manifest; the synthetic profile is explicitly tested
to reject against real AU authority. No synthetic hash is promoted to an AU fact.

## Terminal, AU and default behavior

The controller flushes/closes the audit and invokes the already proven `_Exit`
primitive immediately on final retired or any failure. It never calls nds_halt,
returns a fabricated guest LR, changes scene state, or enters a scheduler tail.
Failure evidence includes the sampled canonical state when available and the
sticky reason. A missing final event is also terminal failure, not success.

AW3 capture-only AU handoff still follows all original AU guards and precedes
legacy finish/halt. Existing failure/returned-handoff/ordinary-halt fences are
unchanged. Three guard-fragment model controls establish success exit 73, rejected
CPU exit 79 and disabled legacy-halt sentinel exit 99. These are model controls,
not live AU replay or a positive actual-AU identity claim.

A Windows CRT compatibility defect was discovered during testing: fopen("wbx")
was rejected on this toolchain. `exclusive_audit` now uses CRT
`_open(O_CREAT|O_EXCL|O_WRONLY|O_BINARY|O_NOINHERIT)` and `_fdopen`; existing paths
reject atomically and are not truncated. The system's CRT declarations are supplied
explicitly because runner/src/io.h shadows the system io.h. Every actual-provider
child uses this same file opener and independently verifies an existing file cannot
be reopened. Non-Windows code retains the prior exclusive fopen spelling; no
cross-platform execution claim is made.

Default observers/journal activation remain inactive; the new passive fields are
read only when diagnostics request a snapshot. No new environment selector or AX
dispatch/handoff was installed. A disabled actual-runtime control returns normally
from reschedule without journal/observer activity. Original source guard files are
hash-identical before/after installation; six default runner objects compile.
SDL and headless runner executables are hash-identical and were not relinked/launched.

## Evidence and counts

Authoritative evidence: `local/task-aw4/certification-004/` (`commands.json`,
`tests.json`, unit field counts, full local canonical audits and three `au-*`
guard controls). Earlier build/test attempts, certification-001/002/003 and
`local/task-aw4/au-guards-001/`
remain historical, not overwritten.

- **8,456 assertions**: 4,228 in each no-bank/all-selected profile; two complete
  actual-provider ledgers accept all 77 events, including exact grown journals.
- **39 actual-provider children**: two terminal successes, 36 independent failures,
  one disabled control. Every expected exit and audit ending passes.
- **Three AU guard-fragment children** pass separately. Total disposal/control
  children: **42**. Only the deliberately disabled AU control reaches old halt.
- Faults include coherent skipped/duplicate/rewound/unexplained ordinals; every
  scalar mutation/omission at four transcript phases and every entry-field
  omission/width mismatch; every manifest class; journal
  missing/extra/epoch/serial/source/predecessor/result/deadline; import staleness;
  hidden latch/yield; IRQ/ARM7/device/scheduler readiness; image/save/CPU mutation;
  divider model; debt/cap/cost; missing/extra events; wrong MMIO metadata; torn binding;
  and chained-audit tamper. Prospective retained-cap/debt/unknown-timing hazards and
  forbidden service kinds are independently negative-tested.
- Success/failure tail, guest, old-halt, destructor/shutdown and persistence
  sentinels are absent. Complete canonical snapshots are flushed before disposal.

## Limits and next task

**Zero Brain Age guest execution, zero runtime Brain Age MMIO, zero live capture,
zero AX execution, zero save/checkpoint loading or mutation, zero ROM/generated-C
edits.** Synthetic buffer/state mutation is confined to isolated test processes.
No actual AU timing/peripheral/divider baseline was newly observed. There is no
compiled-parity claim or proof that a future real AU snapshot will meet the
conservative admission predicates. Observations that do not meet them must reject.

No remaining AW4 state-evolution/provider-coupling contradiction is known.
The next justified step is a **separately authorized single capture-only AU replay**
ending at 0x02001980 before fetch/accounting/dispatch, with actual ROM/image/save/
cap/readiness binding, unchanged AU guards, exclusive audit and nonreturning
disposal. It must execute no AX instruction/MMIO and stop on any mismatch. Only
that result can establish real AU eligibility and inform a later certificate.
AW4 neither authorizes that replay nor issues an executable AX certificate.
Stopped after AW4.
