# Task AW8 - exact-profile provider binding

**FULL PASS for the requested ROM-free provider/controller certification.**
`dynamic_execution_ready=true` only for a **later separately authorized** one-shot
diagnostic of the unchanged 11-instruction contract. **No execution is authorized
or armed here; the runtime real-bus interlock remains closed.** No Brain Age replay,
guest instruction, runtime Brain Age MMIO or prefix execution occurred.

## Authority and provenance

AW7 `01fe942d8d42b0dc819acf92836c7cfb845a6470`, AW6
`1d4aeb1e17486b1db2276931f43a9c5d9a540f1b`, AW5
`e366a8b8811668ae9bd22bd34b661799c6058bad`. Framework remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`.

The fixture is derived from the retained AW5 `capture.jsonl`, SHA-256
`303f069c8d7f4e36da31aaab6b2810cc34e06b0eaee5ced7fcf67e463146327a`.
Its complete **361-scalar/five-identity** AW2S observation has SHA-256
`0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c`,
already bound by committed AW5/AW6 evidence. Python verifies the capture/canonical
hashes and cross-checks the identities with AW5's committed result. C++ independently
decodes, re-encodes and authenticates the complete canonical input before restoring
any fixture field. Missing, extra, stale or changed evidence is rejected.
This is integrity authentication against the project's authoritative hashes, not
an independent external signature or a new observation of the original game.

No ROM, save/checkpoint, retained RAM/DTCM image or game asset was opened. Only
allowed historical hashes/scalars, source, libraries and metadata were used.
AW5's prior rejected result was not rewritten or normalized.

## Fixture construction, not snapshot injection

`tools/task_aw8/` constructs fresh synthetic objects containing the exact captured
CPU/register/CPSR, return-stack, CP15/cache-map, timing-latch, IRQ/DMA/timer/divider,
scheduler/ARM7, periodic phase and accounting values. Values come from authenticated
evidence rather than a second hand-entered profile or readiness truth flags.

The **original provider function bodies** read those objects through
`task_aw3::passive()` and its runtime/bus/CP15/IO/scheduler getters. No component
getter is replaced with an expected snapshot. Thread ownership, cacheability,
pending IRQ projection, timer fields, SPU/Wifi/GPU readiness and logical counters
are obtained from the actual source interfaces. CP15 bitmaps are rebuilt by its
real structure importer, not asserted by a caller-supplied boolean.

The cap journal is seeded with the authenticated prior epoch/serial and regenerated
through actual `nds_slice_begin`. Actual `runtime_publish_fast_limit` establishes
the captured cap while preserving hint=1. During the model transcript, actual
`nds_reschedule_slice` appends the five replacement-deadline records. Instruction
costs use real fetch/data/refill classifiers; actual `nds_has_bank` must report
no compiled takeover before each modeled fetch. CPU effects are **modeled**, never
dispatched through an interpreter or compiled guest bank.

This closes AW7's 103-scalar/four-identity fixture mismatch: all 361 entry scalars
and five identities now compare exactly, including the seven-entry return stack.
No protected field, journal record, timing latch or latent timer value was removed.

## Explicit immutable-observation binding

AW8's authorization permits authoritative AW5 identity metadata with provenance.
This is used honestly rather than claiming synthetic images hash to original ones:

- RAM/DTCM/save surrogate bytes have their own computed hashes. Three adapters in
  **generated, ignored test copies only** bind those local digests to AW5's
  authenticated historical observations. Every sample checks the actual local
  digest against its sealed value and rechecks the immutable canonical evidence.
- ROM identity is restored from the authenticated loader observation, bound to a
  computed local provenance-tag digest. No ROM is loaded or represented as newly
  measured ROM bytes.
- Framework identity remains the original provider's constant and is checked
  against the pinned source/evidence. All five metadata classes have independent
  corruption tests.
- The binding map is copied into an immutable sealed object. Late rebinding,
  unsealed use, modified backing bytes and changed historical evidence fail closed.

Each binding audit labels `new_measurement_of_AW5_image=false` and records both
local-surrogate and authenticated historical digests. The differing surrogate
hashes are intentionally visible. They are **not** production identity overrides.
`binding.h` rejects compilation outside `AW8_ROMFREE_FIXTURE`; no production
source, provider API or identity behavior is changed. Generation reverses/checks
its three adapter additions against the original getter text. All other provider
reads are unchanged. This permission is specific to ROM-free fixture certification;
a future live runner must compute its own original identities with **no adapters**.

## Handoff, owner and complete evolution

The installed, unchanged AU `au_control` fragment is exercised at its certified
terminal index. Its CPU/opcode/order/read/write guards use actual fixture CPU and
instruction counters; full RAM/DTCM/save comparisons use real surrogate byte
copies, not the empty suppliers from AW7's model. No earlier AU path is replayed.
The guarded terminal hands ownership to unchanged `task_aw7::handoff` before the
legacy halt path. The controller independently samples the real passive interface
twice, admits the unchanged AW6 manifest/profile and primes its first observation.

The test drives actual provider objects through the same AW7 access-owner,
prospective checks and strict 69-observation ledger. Model callbacks perform the
five synthetic divider-state transitions, not MMIO function calls. Every complete
state, epoch/serial/ordinal transition and chained canonical identity is checked.
A mutation between handoff samples rejects with `AW7: torn actual provider binding`.

| Property | Proven ROM-free result |
|---|---|
| Start / terminal | 0x02001980 / retired 0x020019B0, architectural PC 0x020019B4 |
| Instructions / observations | 11 modeled transitions / 69 observations |
| Costs | 8,1,8,1,3,8,8,8,4,4,3; total 56 |
| Final cycle / retained cap | 3416875777 / 3416875778; margin 1 |
| Accesses | 11 modeled code reads, two RAM literals, five divider writes; zero status reads |
| Divider deadlines | 1708437894, 1708437899, 1708437905, 1708437909, 1708437913 |
| Journal | Epoch 496; serial 501 -> 506; records 1 -> 6; no cap shortening |
| Final canonical identity | `ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526` |

The complete final digest matches AW6, including its 411 scalars/five identities.
Independent Python verification checks all observation hashes/chains, costs, write
deadlines/serials, final state and unchanged identities. Hint=1, parked ARM7 debt=2,
RTC phase and active-but-latent timers remain protected throughout.

## Disposal and tests

Authoritative command:
`python tools/task_aw8/check.py --out local/task-aw8/certification-008`.
All expected outcomes pass:

- **56 provider process controls:** one exact-entry inspection, one full 69-event
  success (exit 73), and 54 failure disposals (exit 79).
- **Five independent identity-input corruption children** reject before admission:
  ROM, main RAM, DTCM, save and framework.
- **One default-build executable** proves no diagnostic arming/owner/observer;
  an additional negative compile proves the fixture binding header is unavailable
  without its test capability. Total: **62 runtime process controls plus one
  negative compilation check**.
- Negatives cover AU guard failure, cap one shorter, ordinal/cycle/cap/hint/bank/
  hidden-latch/debt drift, ARM7/IRQ/RTC/timer/device/scheduler readiness, immutable
  backing/evidence changes, journal serial/source, torn handoff, missing/extra/
  reordered events, wrong access address/width/value, every instruction's cycle
  drift, forbidden fetch/account/dispatch, old halt and unexpected service.
- Real-bus/MMIO callbacks are rejected by AW7 before invocation. Generated IO test
  copies additionally trip **before the original body** at real IO read/write
  entry; two negative attempts prove no MMIO body effect can occur in this harness.
- Success/failure flush and close the audit, then use unchanged nonreturning
  `_Exit`. No scheduler/device/IRQ/ARM7/guest/halt/shutdown/persistence sentinel
  executes after either terminal path. The inspector intentionally returns
  normally outside a protected run.

The first preparation/compile attempts found encoding/type issues; an early driver
incorrectly supplied the store bit as the timing API's sequential flag and was
rejected at the first cycle commit. It was corrected to the ordinary nonsequential
data-access classification. No guard, expected cost or certificate was changed to
accept that bug; all attempts remain local and no guest run occurred.

## Certificate and limits

`tools/task_aw8/certificate.json`, canonical payload SHA-256
`8381e1335266a05767982f292eb5237eb157bb5d8d9ea431c1a81d7552bae417`,
sets `dynamic_execution_ready=true`, `live_execution_authorized=false`, and
`runtime_execution_armed=false`. `certify.py` checks source/artifact identities,
all process audits/chains and preserved historical evidence before issuing it.

It is scoped to **one later separately authorized diagnostic**, matching the entire
actual entry manifest and preserving every AU/AW6/AW7 guard. No live admission or
repeatability is claimed here. The live path must independently compute original
ROM/RAM/DTCM/save identities, with no historical adapters or normalization; any
entry drift must reject. Separately authorized diagnostic backend permission/arming
would still be necessary; the current real-bus interlock is deliberately closed.

Forbidden next remains **0x020019B4 / E1D100B0**, the eight-cycle divider status
read. Passive manifest inspection of its code word is not instruction fetch.
No twelfth instruction, read result, divider completion, compiled parity, gameplay,
save/history or timing optimization is certified. Predicted RAM/DTCM/save delta is
zero; there is no new live before/after measurement. No remaining blocker exists
within AW8's ROM-free fixture/controller scope.

All production sources, older committed helpers, prior runner executables,
AW5 capture and attempt lock retain their hashes. No ordinary runtime/timing or
scheduler semantics changed. The unrelated archive was preserved.

Local evidence: `local/task-aw8/certification-008/` (tests, provenance, commands,
success/failure audits, ignored generated source and native binary), and
`local/task-aw8/readiness-002.json`. No image/source snapshot or native binary is
committed. Stop after AW8; do not execute the prefix.
