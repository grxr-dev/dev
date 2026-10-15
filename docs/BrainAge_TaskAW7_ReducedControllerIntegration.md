# Task AW7 - reduced-controller integration

**PARTIAL. `dynamic_execution_ready=false`. No Brain Age execution, replay,
runtime Brain Age MMIO, or AX/prefix execution occurred.** The reduced ownership
path is installed in local diagnostic source, but is deliberately dormant and
its real-bus interlock is closed. No dynamic execution certificate is issued.

## Authority and scope

AW6 `1d4aeb1e17486b1db2276931f43a9c5d9a540f1b`, AW5
`e366a8b8811668ae9bd22bd34b661799c6058bad`, AW4
`0bb63e407f1caaa001e1e63a578547af3eddc7b9`; framework remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`. All committed AU/AW/AW2-AW6
helpers are unchanged. AW5's capture, exclusive attempt lock, capture executable,
old SDL executable and headless executable retain their prior SHA-256 values.
No ROM, save, checkpoint or retained RAM/DTCM image was opened by this task.

The unchanged AW6 certificate payload SHA-256 is
`1b3eb0981c5083d958e8811ee5cc70d73a1c538c6641a1e57ba7f120b7fb092f`.
It describes 11 instructions, 56 cycles, five divider writes and zero MMIO reads.
Entry cycle is 3416875721; terminal cycle is 3416875777, one cycle below retained
cap 3416875778. Terminal is the retired observation for 0x020019B0, with PC
0x020019B4, **before** the forbidden status read's fetch/accounting/dispatch.
There is no extension to the twelfth instruction or change to ordinary timing.

## Installed task-scoped path

`tools/task_aw7/install.py` applies only these dormant additions to local source:

- Copy unchanged AW6 `prefix.h` and the new `aw7/integration.h`.
- Include the new owner from `brainage_task_au.h`.
- Add a waiting-owner handoff to `task_au_setup.inc` **after every existing AU
  entry CPU/opcode/order/read/write/full-memory/save/terminal guard**, before
  AW5/AW3 capture and the legacy halt path. Once owned, further dispatch guards
  delegate to the strict reduced ledger, rather than reusing AU's exhausted
  seven-instruction budget.
- Add owned branches to the six `RtBus` read/write methods in `tier3.cpp`.
  Unowned execution retains the complete existing AH-through-AU access guards
  and bus calls. The returned-handoff rejection exempts only the owned path.

`arm_diagnostic()` requires the compile-time `AW7_DIAGNOSTIC_HARNESS` capability,
an existing AW3 exclusive audit/armed session, no observer, and exclusive owner
thread. Normal builds cannot arm it. No environment selector, CLI switch, replay
helper or gameplay activation is installed.

At handoff the real `task_aw3::passive()` interface is sampled twice, with full
value equality required. AW6 admission binds all 361 entry scalars/five identities,
canonical entry digest, AU manifest, journal provenance and source-derived
readiness/cost predicates. The entry digest is
`0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c`.
Nothing is normalized or removed. Handoff primes exactly one instruction event
for 0x02001980: Tier-3 emitted its original event before the AU control/handoff,
while this observer was still absent. Subsequent events use the existing observer.

Each access must match the next ledger event's PC/address/width/direction/value
before its callback. It emits access-before, checks complete passive state, then
access-after and its resulting model/journal state. Every instruction event
checks prospective cost/debt/cap/readiness before dispatch; `check_dispatch()`
also rejects any intervening provider change. Full AW2S semantic comparison,
immutable seal, journal rules and chained canonical identity remain enforced.
Missing/extra/reordered events or unexplained state changes sticky-fail.

**Actual runtime callbacks remain blocked before the underlying bus call**, even
for an otherwise valid access. Only a separately compiled `AW7_ROMFREE_MODEL`
test executable can invoke the scalar/model callback rail. This is a safety
interlock, not a claim that real access ownership has been positively certified.

On the 69th accepted observation, success requires 18 access pairs (11 instruction
fetches, two literals, five writes), no active callback, exact final cycle and
canonical digest. Success flushes/closes the audit and calls `std::_Exit(73)`;
failure uses the same nonreturning primitive with exit 79 (78 on audit failure).
No ordinary halt, return to scheduler, destructor or persistence shutdown is a
terminal fallback. No success-path fetch/account/dispatch of 0x020019B4 is possible
after this terminal callback. Existing AU exceptions while AW3 is armed still
route through its nonreturning failure path.

## What the tests establish, and what they do not

Command: `python tools/task_aw7/check.py --out local/task-aw7/certification-006`.
This launches native ROM-free test executables only, never a game runner.

### Positive source/model rail

The exact retained AW5 canonical profile initializes the AW6 scalar rail. Real
AW3 passive aggregation/journal code and the installed AU guard fragment drive
the new handoff/owner, prospective checks, modeled accesses and 69-observation
ledger. Extracted source bodies implement divider writes, rescheduling and costs.
The component getters here are **test replacements**, not actual live getters;
the AU fragment's memory/save suppliers are synthetic test doubles.

All 11 costs are `[8,1,8,1,3,8,8,8,4,4,3]`. The five modeled writes preserve cap
3416875778 and append journal serials 502..506 in epoch 496:

| PC | Address / width / value | Precommit cycle | Divider deadline |
|---|---|---:|---:|
| 02001980 | 04000280 / 2 / 1 | 3416875721 | 1708437894 |
| 02001988 | 04000290 / 4 / 0 | 3416875730 | 1708437899 |
| 02001994 | 04000294 / 4 / 4096 | 3416875742 | 1708437905 |
| 02001998 | 04000298 / 4 / 4096 | 3416875750 | 1708437909 |
| 0200199C | 0400029C / 4 / 0 | 3416875758 | 1708437913 |

The full final canonical digest matches AW6:
`ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526`.
Independent Python checks recompute canonical hashes/chains, write transitions,
costs and the final cycle. This is a modeled result, **not actual-provider success**.

### Actual-provider rejection rail

`provider.cpp` links the existing AW4 ROM-free fixture objects containing the
actual runtime/bus/CP15/IO/scheduler/SPU/GPU/Wifi getters, without replacing those
getters in the new translation unit or overriding AW6's authority manifest. The
objects were built with AW4's synthetic-fixture configuration. No guest execution
or real MMIO is invoked. The installed AU fragment remains in a modeled harness;
this is not a full real AU replay or complete actual guard/provider success proof.

Two real passive observations of that fixture are identical. Handoff then rejects
before observer installation, ownership or protected dispatch with:
`AW7: AU ROM/RAM/DTCM/save/framework hashes`.
The fixture has 356 scalars versus the required 361; independently decoded
observations differ in **103 scalar cells including missing cells**, plus four
identity classes: ROM, main RAM, DTCM and save. Framework identity matches.
Differences also include cap/epoch, timing/CP15, return stack, IRQ/ARM7, RTC/timers
and divider state. Thus this is **not merely one hash mismatch** that can safely
be waived. The first hash rejection does not certify the later readiness checks.
Actual fixture digest:
`836bbba9c07b5754110aa477b59f7c1468764da727eee48b477aabb865b52ed8`.

No expected digest was copied into actual buffer observations. Loading images,
injecting expected identities, removing fields or weakening equality to turn this
negative into a positive would not establish the requested proof.

## Tests and disabled behavior

- 366 independent entry mutations rejected: 361 scalars and five identities.
- 49 model process controls pass: one 69-observation success, 46 fail-closed
  negatives, one diagnostic-disabled AU legacy-route control, one default normal
  return with shutdown/persistence sentinels expected and observed.
- Negatives cover entry/cap-shortening, hint/bank, debt/ARM7 wake, IRQ, RTC,
  timer/device/scheduler readiness, hidden latch, divider/journal transitions,
  ordinal/cap drift, wrong address/width/value/order/duplicate access, all 11
  individual cycle drifts, missing/extra/reordered observations, forbidden next
  fetch/account/dispatch, old halt and the real-bus interlock.
- One additional actual-provider rejection process exits 79 before ownership.
- One separately compiled **default-mode** executable rejects arming and leaves
  observer/owner/AW3 activation absent. Default Tier-3 object compilation passes;
  no game runner executable was relinked or launched.
- Success/failure audits are complete after process exit. No scheduler/device/
  IRQ/ARM7/guest/old-halt/shutdown/persistence sentinel is reached after terminal
  disposal; attempted actual-MMIO and forbidden-fetch callbacks are not invoked.
- Source comparison proves the original AU setup body and all earlier guards
  remain intact after removing only the new ownership additions and historical
  AW3/AW5 additions. Dormant branches do not alter ordinary timing/scheduler
  semantics. This is focused source/compile/default testing, not gameplay parity.

## Remaining certification decision

**Dynamic execution is not ready.** Actual-provider-compatible exact AW5 admission
and a complete actual-provider/access-owner 69-observation success have not been
proved. The existing AW4 synthetic fixture is not the captured profile, and its
computed immutable image/loader/save identities are not authoritative AU images.
That is the smallest remaining integration work, not a newly disproven cap model.
Until a trusted fixture/immutable-observation binding and full actual-provider
success/failure coupling are demonstrated without bypassing guards, the runtime
bus interlock must remain closed. No positive execution authorization follows
from this task. The full 12-instruction route remains rejected.

Next task should resolve that **ROM-free provider-fixture/identity-binding proof**
and full coupling first; do not substitute another live replay or inferred hashes.
Any access to retained image data or dynamic run needs separate authorization.
Stop after AW7; neither the reduced prefix nor AX was executed.

## Artifacts

Committed source: `tools/task_aw7/{integration.h,install.py,au_guard_model.h,
test.cpp,provider.cpp,disabled.cpp,check.py,README.md}` and this report/result.
Local only: `local/task-aw7/certification-006/{tests.json,commands.json,
actual-provider-mismatches.json,success/audit.jsonl,actual-provider/audit.jsonl}`
and `local/task-aw7/installation.json`. Earlier numbered attempts are retained;
initial fixture compile/disabled-mock issues were corrected without guest runs.
Only dormant local runner source and one default Tier-3 object were changed;
previous executables/evidence remain hash-identical. No generated recomp C,
ROM, save/checkpoint, ordinary scheduler logic or unrelated change was modified.
