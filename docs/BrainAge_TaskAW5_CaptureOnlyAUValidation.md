# Task AW5 ? single capture-only AU validation

**PARTIAL: the authorized capture completed safely; actual AU admission rejected.
AX remains uncertified, unauthorized and unexecuted.** No second replay occurred.

## Authorization and implementation

AW4 `0bb63e407f1caaa001e1e63a578547af3eddc7b9` explicitly justified one
separately authorized capture-only replay to 0x02001980, before successor
accounting/fetch/dispatch. AW5 performs only that intermediate validation.
Framework remains `3a57236bb23d25dcb4caad7d58d733311062ff5e`; loader-derived
ROM SHA-1 remains `b8a105bacc3234dede8d4465df0869f2b922a0e2`.

`tools/task_aw5/capture.h` wraps the existing guarded AU handoff. All original
AU CPU/opcode/order/budget/read/write/full-memory/save guards still dominate it.
It records the real journal and passive canonical observation, invokes unchanged
AW4 admission and (only on successful admission) the pure 77-observation projection,
then seals/rechecks and disposes. It never starts/installs an AX controller or
candidate observer. Both success and failure flush/close the exclusive audit and
use nonreturning `_Exit`; no ordinary halt, scheduler return, destructor or
persistence shutdown is a protected terminal route.

The new selector `NDS_TASK_AW5_CAPTURE_ONLY=1` is effective only inside the
existing armed AW3/AU handoff. AW3's loader-derived title check and fresh exclusive
audit remain required. AW3-only capture and the fully disabled old AU path remain
available. No original guard, readiness predicate, expected state or timing
semantic was relaxed to admit the live observation.

An isolated SDL runner at `build/task-aw5-capture-002/nds_runner.exe` recompiles
48 native runner sources using the existing Ninja compilation flags and relinks
existing compiled bank/support archives. No generator or generated ROM-derived C
edit was used. Its SHA-256 is
`472f65b691ae62d2cc47adef78f0f71045bcb7800eb52bf261e4cf8f215bd483`.
Existing SDL/headless executables and imported original objects/archives remain
hash-identical. The first build packaging attempt rejected a linker flag mistaken
for an input archive; it launched nothing. The isolated second build succeeded.

## Preflight and bounded replay

Before the only replay, ROM-free tests established wrapper success/failure
disposal, original AU guard dominance, single underlying bus calls, canonical
identity checks and retained AU images. Historical AU/AS/AO guards and title
policy tests pass. AW4 certification artifacts/source remain bound and unchanged.
The historical read checker assumed `return bus_read` spelling; AW observers now
store/read/emit/return instead. AW5 checks the equivalent dominating read guard,
exactly one real bus call and write-guard ordering in current source; no historical
source or evidence was rewritten.

The immutable Task G checkpoint is
`local/task-g/session-001/11-answer-01-63/checkpoint.state`, SHA-256
`3911c3e98f90d77916497fd82e4f7ae49e7ca825273e52a90b66fd05ce2b2f2f`.
Only disposable state/save copies were used. The exact frozen AU input definition
remains SHA-256 `88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`.
The existing SDL queue path reproduced recognition 2 then 4 and the already
certified guarded publication/helper prefixes. This is the historical AU Tier-3
diagnostic route, not compiled-parity evidence or a new answer/progression task.

## Actual boundary result

The runner (PID 113588) reached **PC 0x02001980**. All eight AU observations
(entry, seven instructions, terminal) match. The seven instructions performed
nine allowed reads and one allowed DTCM stack write; no MMIO access occurred
in that protected AU prefix. The final observation is before the first candidate
instruction's runtime fetch/accounting/dispatch. Reading its code word passively
for the AU opcode/manifest guard is not an interpreter instruction fetch.

- ARM9 ordinal **281098008**, cycle **3416875721**; ARM7 ordinal **96026779**,
  cycle **1708437825**. AU ARM9 delta: seven instructions, 21 cycles; ARM7 unchanged.
- Full **361-scalar/five-identity** canonical snapshot, SHA-256
  `0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c`.
  Schema size legitimately includes the actual seven-entry return stack.
- Independent offline checks pass full schema, exact AU CPU/code/protected
  scalar/ROM/framework/RAM/DTCM/save manifest, canonical round-trip/hash and
  runtime-owned cap journal validation.
- The live check rejects **`pending yield/unclassified poll mode`** because
  `hidden.yield=1`. Failure audit is flushed; process exits **79** without forced
  termination. No live immutable seal or 77-event admission is claimed.

## Concrete admission contradictions, not repaired here

Read-only analysis applies the unchanged predicates to the saved observation;
it neither normalizes the state nor launches another runner.

| Observation | Consequence |
|---|---|
| `hidden.yield=1`, CPU polling enabled | Fails AW3 entry predicate requiring zero. `runtime_arm.cpp` sets this hint at slice begin; its source comments explicitly state Tier-3 does not maintain it. Therefore this observation alone is **not proof of an eligible IRQ/service**. Its semantics require a new ROM-free certification, not clearing it. |
| Slice origin cycle 3416875650, quantum 128, cap **3416875778** | Trusted source-0 journal record, epoch 496, serial 501; only **57 cycles** remain at entry. |
| Copied-state costs **8,1,8,1,3,8,8,8,4,4,3,8**, total **64** | Nominal terminal cycle 3416875785 exceeds the actual cap by seven. Unchanged core preflight independently rejects `retained slice cap would return to scheduler`. |
| Hypothetical first divider deadline 1708437894, CPU cap 3416875788 | Later than the already earlier cap 3416875778. It would **not shorten** that cap; AW4's 77-event first-shortening admission is not satisfied. This is an ordinary retained slice-origin cap, not evidence of an inherited divider event. No write was performed. |
| ARM7 parked deferred debt **2** | Unchanged first prospective check independently rejects `ready/stale state: deferred7`; this is not evidence that ARM7 actually ran. |
| RTC processed **1670410**, floor-derived due **1670409** | Fails unchanged equality; no catch-up or RTC adjustment was performed. |
| Timer controls 0/4/5 = **0xC1**, 7 = **0x40** | Outside the current all-control-zero timer certificate. Enabled/IRQ-enabled controls do not by themselves prove an overflow before terminal; no such stronger claim is made. |

The earlier-cap constraint alone disproves eligibility of the current full
12-instruction/64-cycle contract for this actual entry. Eleven modeled costs sum
to 56, but **no reduced prefix is certified or authorized**: yield/debt/timer/RTC
classification and a different strict transcript would still require proof.

## Disposal and state safety

The final flushed events are `aw5_handoff`, journal, canonical snapshot, failure.
There is no AU `decision_stopped`, legacy `disposable_exit`, or `final.sav`.
The handoff and fail path contain no guest/service invocation and terminate via
the tested nonreturning primitive, so no post-boundary instruction, scheduler
tail, IRQ acceptance, ARM7 catch-up, device service or persistence shutdown can
follow it. Candidate fetches/instructions and protected MMIO accesses: **zero**.
This is not a claim that the entire earlier ordinary game/checkpoint replay
performed no normal device I/O.

Actual RAM SHA-256 remains AU's
`84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340`;
DTCM is AU's exact post-stack-write
`a5313aa2084674d767307c09ebd86fb888ebf992b8f486602412f9499c55496f`.
The known AU write is 0x027E3658: 0x02067AE0 -> 0x02067568. Earlier certified
prefix transient guest RAM changes remain disposable; they were not undone or
mistaken for unchanged RAM from initial startup.

Logical save requests **0**, Flash commits **0**, changed save bytes **0**.
Source save, disposable save and passive live save hash all equal
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
Original checkpoint/save and copied source checkpoint remain unchanged. No
normal persistence shutdown runs. No ROM patch or generated-C edit occurred.

## Tests and evidence

- Pre-live `local/task-aw5/check-001/`: nine wrapper children (success, seven
  failures, disabled) and AU/AS/AO/policy regressions pass.
- Final focused `check-002/`: **ten** children ? AW5 success, seven independent
  failures, historical AW3 success, disabled legacy control. All expected exits
  and absent post-terminal/destructor/persistence sentinels pass. The disabled
  control alone reaches its deliberately modeled old-halt sentinel.
- AU/AS/AO tests: **237 + 404 + 11 = 652** assertions; policy regression also
  passes (does not print an assertion count). AW4's broader proof was bound,
  not rerun or counted as new AW5 assertions.
- `capture-001/`: only live attempt, SDL provenance, original AU audit, exclusive
  `capture.jsonl`, immutable/disposable-file checks and process exit.
- `analysis-003/`: independent Python canonical decoding plus native unchanged
  schema/manifest/journal/cost/preflight checks. The first offline analyzer
  expected debt to reject first; the real retained-cap check correctly rejected
  earlier. Its assertion was corrected to the observed guard order, without
  changing runtime checks or replaying.

All snapshots/save/state/captures/binaries remain local and ignored. The attempt
lock is preserved. Unrelated `jarvis-inbox-v1.zip` is untouched.

## Following-step decision

**No executable AX certificate. Do not execute AX or repeat the live capture.**
The exact next recommendation is a separately authorized **ROM-free reconciliation
of this captured AU profile**: classify the Tier-3 hint, parked ARM7 debt,
timer/RTC phases and earlier cap without discarding observations or changing normal
semantics; prove an exact safe transcript (or demonstrate none exists) using the
captured cap rather than extending/clearing it. Only after that proof should a
later capture/certificate be reconsidered. AW5 implements none of that following
work and stops here.
