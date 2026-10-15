# Task AW10 - next divider/slice boundary

**PARTIAL overall; conclusive negative admission proof.** No positive next guest
instruction is certified. `dynamic_execution_ready=false`. No Brain Age execution,
replay, runtime MMIO, save/checkpoint access or mutation occurred. AW9's one-shot
permission remains consumed. No runner was launched or relinked.

## Authority and reconstruction

AW9 `fb3e417aa48cc70cc4c05f796263c9cf87b791af`, AW8
`c0ac62cae632715157fcb3db52b982cc86104baa`; framework
`3a57236bb23d25dcb4caad7d58d733311062ff5e`. State reconstruction uses only
`git show` of committed AW9 results, AW8/AW6 certificates, AV lookahead and the
AU scalar manifest. The local AW9/AW8 canonical audit payloads are not imported.

The exact committed terminal facts are:

| Property | Value |
|---|---|
| Architectural PC / last retired PC | 020019B4 / 020019B0 |
| ARM9 cycle / ordinal | 3416875777 / 281098019 |
| Retained cap / fast limit | 3416875778 / 3416875778 |
| ARM7 cycle / ordinal | 1708437825 / 96026779 |
| CPSR / NZCV | 0000001F / 0000 |
| SP / LR | 027E3654 / 02001A24 |
| Journal epoch / serial / records | 496 / 506 / 6 |
| Divider control / deadline | 8001 / 1708437913 system cycles |
| Numerator low/high; denominator low/high | 0/4096; 4096/0 |
| Quotient low/high; remainder low/high | 0/1; 0/0, still previous results |

All sixteen registers, protected AU code/RAM/DTCM scalars, final divider state,
five immutable identities and these timing facts form an **89-scalar projection**
in `tools/task_aw10/certificate.json`. It is explicitly NOT a complete snapshot.
The authoritative **411-scalar/five-identity AW2S** commitment is still
`ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526`.

Committed reports/certificates reference, hash and describe the complete local
audit, but do not serialize every canonical scalar. AW6's expected-state projector
requires the full AW5 entry; AW8 loads that entry from local authenticated evidence.
Neither a digest nor that projector recovers the unpublished input values. Thus
the complete terminal snapshot cannot honestly be reconstructed **from committed
evidence only**. No missing readiness, CP15/latch, journal or scheduler field is
filled with zero, dropped from the provider, or silently replaced by the projection.
This is one reason for PARTIAL, not a contradiction of AW9's FULL PASS.

## Next original instructions (static only)

AV's committed disassembly and the AU code manifest agree:

| PC | Opcode | Local semantics | Cached cost |
|---|---|---|---|
| 020019B4 | E1D100B0 | LDRH r0,[r1], aligned 16-bit read at 04000280 | 8 |
| 020019B8 | E2100902 | ANDS r0,r0,#8000 | 3 |
| 020019BC | 1AFFFFFC | BNE 020019B4; fallthrough 020019C0 | 4 if taken |

The status instruction has no base writeback or flags/SP/LR effect. Under the
unchanged busy state its modeled R0 is 00008001, PC becomes 020019B8, CPSR remains
1F. This is NOT a new observed read or an executable prefix. ANDS would produce
R0=00008000, N=0,Z=0,C=0,V=0; the rotated immediate supplies C=0 and V is preserved.
BNE would then return to B4. These are local opcode semantics, not a certified
contiguous path: ordinary slice polling already intervenes after B4.

`runtime_code_cycles` gives B4 numC=1: ARM prefetch address B4+8 does not cross a
32-byte cache boundary. Nonsequential, noncacheable IO halfword numD=8; the actual
`arm9_cycle_combine` yields max(1,8,1+8-6)=8. B8's prefetch address C0 gives numC=3.
The taken BNE refill to B4 costs 3+1=4. No timing-class/CP15 normalization is used.

## Read effects versus cycle commit

Exact source path: `tier3.cpp` fetch/decode and `Interpreter::step`, portable
`interpreter.cpp` LDRH memory handling, `RtBus`/`runtime_mem_cycles`,
`nds_io_read` -> `math_reg_read32`, then Tier-3 cycle commit/retirement/polling.
Data timing and access occur before committing the instruction's cost.

At the hypothetical read, active system time would be floor(3416875777/2) =
1708437888, **25 system cycles before** divider deadline 1708437913. The math
selector returns DIVCNT masked to 16 bits, 8001. It does not finish the divide,
acknowledge/clear busy, restart/reschedule it, or alter operands/results. Divider
completion is in `nds_run_system_events`, not this read. Fetch/data timing latches,
instruction ordinals and audit/accounting would nevertheless change; the entire
instruction is not a state no-op. Even the hypothetical commit's system time
1708437892 is still before divider completion. This does NOT rescue its slice cap.

## Mechanical cap rejection

Entry C=3416875777, cap=fast_limit=3416875778: remaining budget **1**.
Read cost **8**, active ARM9 debt zero in the previously certified profile:

`C + 8 = 3416875785 > 3416875778`, an overrun of **7**.

AW6/AW7's retained prospective contract requires commit **strictly below** the
existing cap and every protected service boundary. Equal-to-cap also rejects.
The negative proof needs only the committed cycle/cap/cost facts; unknown missing
fields can cause additional rejection but cannot turn this inequality into safety.
The first next instruction already fails, so the largest preserved-contract prefix
is **zero instructions / zero MMIO accesses**, with no new post-read state digest.

## Why a scheduler transition cannot simply be assumed

`tier3.cpp:400` computes `poll_exits = cycles >= fast_limit`, which is **false** at
AW9 terminal. It does not pre-charge prospective cost or select a new slice at this
point. It accounts/fetches/executes the atomic instruction, commits cycles at 564,
computes `poll_after` at 570, emits retired at 653, may accept IRQ at 657, and only
then tests slice expiry at 680. Absent AW9's terminal controller, B4 would normally
overshoot the old cap before returning. Ordinary atomic overshoot is runtime
behavior, not permission to relax the diagnostic contract.

An interpreter-only early return is also insufficient: `run_slice` restores unwind
state and redispatches while C remains below its local cap, absent a genuine
terminal/DMA/HALT/event/expired-cap cause. Neither a stale yield hint nor calling
`nds_preserve_unwind_state` alone establishes a new slice. No clock rounding,
one-cycle charge, cap replacement, fake event or `nds_halt` is introduced here.

For a genuinely certified early-yield transfer, the existing scheduler would have
to observe the real return, save ARM9 cycle/debt, tick ARM9 timers and GPU3D, perform
ARM7 catch-up/timers, check power-off, then service display/SPU/Wifi/RTC/system
events and publish the rendezvous timestamp. A later round selects its event-bound
target and `nds_slice_begin` records a new cap/epoch. At unchanged C the rendezvous
would be 1708437888, not the expired-cap value 1708437889. Current ARM7 timestamp
1708437825 is behind it by 63 system cycles. Parked HALT/debt does not authorize
skipping catch-up/timer service. Latent timers/RTC and deadline replacement must
be re-projected through that actual tail, not treated as immutable forever.

This maps the necessary ordering, **not** an executable scheduler certificate.
No task-scoped pre-dispatch early-yield escape through `run_slice`, complete
all-field tail transition or resulting new-cap admission is certified. The
preserved zero-service controller would fail on that tail. A hypothetical divider
deadline is not a license to call `nds_slice_begin` directly. The currently
certified boundary remains AW9's nonreturning disposal before B4.

## Tests and preservation

`python -B tools/task_aw10/check.py --out local/task-aw10/certification-007` passed:

- **148 Python tests**: exact committed projection/identities and digest commitment;
  every one of 89 projected scalar mutations; wrong B4 opcode/status/busy/deadline;
  timing/cap margins 0..10, cost/debt/overflow, unknown readiness fields, and
  missing/reordered/extra events including IRQ/ARM7/device/scheduler/forbidden fetch.
- **38 native scalar checks** use extracted original clock conversion, cap
  predicate, math selector and cycle-combine bodies on synthetic globals. No
  interpreter, runtime IO, bus or scheduler body is called.
- **Two disposal children**, success-of-negative-proof exit 73 and failure exit 79,
  flush/close their audit and call the unchanged nonreturning primitive. Guest,
  scheduler/device/IRQ/ARM7, destructor and persistence tail sentinels are absent.
  These recheck the primitive, not a new live controller coupling.
- Default observer remains null; the ordinary scalar child returns normally and
  its destructor executes. All original full-state/chain/owner/readiness/disposal
  code, runtime files and AW9 attempt/permission locks retain their hashes.

Source checks bind the unchanged AW6 runtime files, AW7-installed Tier-3/AU hook
files against retained AW9 build/source metadata, the pinned portable interpreter,
the original combiner identity and explicit event/access/commit/scheduler ordering.
That local build metadata is source provenance, not an imported terminal snapshot.
Initial test preparations caught a pre-AW7 file-hash expectation, an anchor spelling,
unsupported MSVCRT `fopen("wx")` and a dynamically composed IRQ-key check. They were
fixed in this new offline checker only; guards/caps/old checkers were not weakened.
All preparations remain ignored; none launched guest code.

There is **no new complete provider/readiness/scheduler certification**. Unknown
IRQ/ARM7/device evolution still rejects; the old tests/protected observations are
not replaced by these smaller tests. No post-read canonical digest, positive
scheduler prefix, compiled parity, real hardware timing or gameplay claim is made.
No new save before/after measurement is claimed: historical save identity remains
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb` and AW10 executes
no guest/save path. No normal runtime/timing semantics change; no activation exists.

## Next safe task

A separately authorized **ROM-free evidence and early-yield/scheduler-boundary
certification**: first promote/verify the allowed scalar-only terminal metadata
from the already-authenticated AW9 audit into a lossless committed fixture (not a
new capture); then prove a task-scoped pre-dispatch return through the actual
`run_slice`/round tail, full protected-state evolution and new-slice admission.
If that cannot preserve the diagnostic guarantees without a broad semantic change,
stop there. No B4 execution, replay, cap normalization or dynamic retry is justified
by AW10. Stopped after AW10.
