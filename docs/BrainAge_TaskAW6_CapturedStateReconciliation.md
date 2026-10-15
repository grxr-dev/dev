# Task AW6 - captured-state reconciliation

**FULL PASS for ROM-free reconciliation and the reduced-prefix static contract.**
The largest prefix under the preserved strict no-cap-crossing rule is **11
instructions / 56 ARM9 cycles**, ending at **0x020019B4 before its status-load
fetch/accounting/dispatch**. The full 12-instruction route remains rejected.
**No replay, guest instruction, runtime Brain Age MMIO or AX execution occurred.**
This is a static source/model certificate, not a claim that the existing runner
can already execute it: its capture-only AU guard still denies AX. Guard-preserving
runtime ownership integration and separate execution authorization remain required.

## Authority and unchanged observation

AW5 `e366a8b8811668ae9bd22bd34b661799c6058bad`, AW4
`0bb63e407f1caaa001e1e63a578547af3eddc7b9`, pinned framework
`3a57236bb23d25dcb4caad7d58d733311062ff5e`. The original AW5 failure and its
exclusive audit/attempt lock are retained. Entry is the exact **361-scalar,
five-identity AW2S v1** observation, SHA-256
`0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c`.
No ROM, save, checkpoint or retained RAM/DTCM image was opened by AW6 helpers;
only prior scalar/hash evidence, source and build artifacts were read.

The old AW2/AW3/AW4/AW5 checkers are unchanged. AW6 creates a separately named,
profile-bound contract, not a normalization or retroactive passing AW5 result.

## Source-grounded disposition

| Captured fact | Reconciliation and continued protection |
|---|---|
| `hidden.yield=1` | `nds_slice_begin` calls `request_yield_poll`, setting hint=1 and fast_limit=0. Tier-3 does not read/clear that hint or call the bank's `runtime_should_yield` path. Its independent exit scan and `publish_fast_limit` use the actual stop/IRQ/halt/DMA/debt/cap conditions. Actual extracted publisher code accepts hint=1 and publishes the cap without clearing the hint. Thus it is non-authoritative as a **Tier-3 pending-work indicator**, not globally meaningless: bank code still uses it. The new contract requires Tier-3-only ownership, the exact captured hint and direct eligibility checks; every observation keeps hint=1. |
| ARM7 debt=2 | Scheduler `switch_to` loads the incoming slot's deferred debt. Tier-3 commits only the **active** runtime debt via `runtime_deferred_cycles_take`. Active ARM9 debt and slot9 debt are zero. ARM7's debt remains parked and exact. |
| Additional captured `halt7=1` | This is guest HALT, not scheduler terminal halt. ARM7's slot is started/nonterminal. `nds_halt_wake_pending(1)` uses raw IE&IF independently of IME; captured IF7=0 gives no wake source. The model guards that raw condition, preserves halt7=1, and forbids switching/ARM7 catch-up. It does not pretend ARM7 was running or clear its debt. |
| RTC processed=1670410, legacy floor due=1670409 | `nds_tick_rtc` uses **`(((system+1)*32768)-1)/33513982`**, not `floor(system*32768/33513982)`. At system=1708437825 its true due is 1670410. No tick is pending there. Both captured fields remain unchanged, and the true due is separately derived with overflow checks. The next RTC deadline is 1708438848. |
| Timer controls 0/4/5=0xC1 | Enabled, IRQ-enabled, prescaler 64, noncascade timers; not immediately overflowing. Using the captured counters/accumulators and last timestamps, next overflows are **1711700418**, **1709382485**, **1708523673** respectively. |
| Timer7 control=0x40 | IRQ-enable alone does not enable counting; bit7 is clear. It contributes no clock-driven deadline. All its counter/reload/phase/control fields remain protected. |
| Timer catch-up | ARM9/ARM7 timer ticks are in the scheduler **after** ARM9 returns; timer-register reads/control writes also tick, but this route touches only divider MMIO and two RAM literals. The divider dispatch returns before timer handling. No timer tick is called within the prefix. Even hypothetical catch-up through final system=1708437888 cannot reach the earliest timer overflow. Stored timer fields are therefore constant, not updated in the model. |

Concrete source locations in the checked local framework: `runtime_arm.cpp`
`nds_slice_begin`, `request_yield_poll`, `publish_fast_limit`,
`runtime_deferred_cycles_take`, `nds_reschedule_slice`; `tier3.cpp`'s instruction
loop/commit/retired/IRQ/poll ordering; `scheduler.cpp` `switch_to`, `run_slice`,
`scheduler_run_round`; `io.cpp` `active_system_timestamp`, `start_div`,
`math_reg_write`, `nds_io_write`, `nds_tick_rtc`, `nds_tick_timers`,
`nds_next_timer_overflow_time`, `nds_halt_wake_pending`.
`tests.json` binds function and whole-source hashes to the AW5 runner build metadata.

## Cap, first write and maximal prefix

The actual source-0 cap journal remains epoch **496**, serial **501**, origin
**3416875650**, quantum **128**, cap **3416875778**. Entry cycle is **3416875721**:
**57 cycles remain**, not 64. Neither cap nor clocks are extended/reset.

The first STRH has prospective cost 8. Its write occurs before cycle commit,
at cycle 3416875721; the new divider deadline is `(cycle>>1)+34` = **1708437894**,
CPU-domain **3416875788**. That deadline is **later** than the existing cap.
The existing cap already admits the complete instruction through 3416875729.
Safety does not depend on the write rescuing/lengthening its own budget.
The runtime's `min(old_cap,2*deadline)` retains the old cap; no cap_change event,
fast-limit clearing or subsequent fast-limit republish occurs in this profile.

| PC | Opcode | Cost | Commit cycle |
|---|---|---:|---:|
| 02001980 | E1C130B0 | 8 | 3416875729 |
| 02001984 | E3A0C000 | 1 | 3416875730 |
| 02001988 | E582C000 | 8 | 3416875738 |
| 0200198C | E3A03A01 | 1 | 3416875739 |
| 02001990 | E59F1014 | 3 | 3416875742 |
| 02001994 | E5823004 | 8 | 3416875750 |
| 02001998 | E5810000 | 8 | 3416875758 |
| 0200199C | E581C004 | 8 | 3416875766 |
| 020019A0 | E12FFF1E | 4 | 3416875770 |
| 02001A20 | EBFFFFE2 | 4 | 3416875774 |
| 020019B0 | E59F102C | 3 | **3416875777** |

The forbidden next instruction is **0x020019B4 / E1D100B0**, a divider status
read with modeled cost 8, reaching **3416875785**, seven cycles beyond the cap.
This proves maximality among prefixes of the documented route under the existing
strict prospective `< cap` rule. It is not a claim that ordinary emulation cannot
overshoot a slice; this diagnostic certificate intentionally may not do so.
There is no 12-instruction certificate and **no status read/result is proven**.

## Static certificate and exact effects

Machine-readable certificate: `tools/task_aw6/certificate.json`, canonical payload
SHA-256 `1b3eb0981c5083d958e8811ee5cc70d73a1c538c6641a1e57ba7f120b7fb092f`.

Start 0x02001980; terminal is the **retired observation for 0x020019B0**, with
architectural PC already 0x020019B4. Dispose immediately before the IRQ check,
cap polling, another fetch, or returning to the scheduler. The exact ledger has
**69 observations**: 11 instruction, 22 fetch before/after, 14 data before/after,
11 commit, 11 retired. No cap_change or service observation is allowed.

| Write PC | MMIO address / width / value | Precommit cycle | New divider deadline | Journal serial |
|---|---|---:|---:|---:|
| 02001980 | 04000280 / 2 / 1 | 3416875721 | 1708437894 | 502 |
| 02001988 | 04000290 / 4 / 0 | 3416875730 | 1708437899 | 503 |
| 02001994 | 04000294 / 4 / 4096 | 3416875742 | 1708437905 | 504 |
| 02001998 | 04000298 / 4 / 4096 | 3416875750 | 1708437909 | 505 |
| 0200199C | 0400029C / 4 / 0 | 3416875758 | 1708437913 | 506 |

Each setup write replaces the single divider deadline, appends a source-1 journal
record and retains cap/fast_limit=3416875778. No old completion event survives.
Control is 0x8001 after each write. Numerator low/high = 0/4096 and denominator
low/high = 4096/0 throughout these repeated assignments; quotient low/high=0/1
and remainder low/high=0/0 are untouched. The two non-MMIO data reads are
0x020019AC -> 0x04000298 and 0x020019E4 -> 0x04000280, both width4.

Required prospective guards: exact trusted AW5 identity/full schema and original
AU manifest; cap journal/source/epoch; complete CP15/timing/hidden/bank state;
source-derived active-vs-parked readiness; checked cost/half-rate/deadline arithmetic;
**both pre-existing and resulting cap strictly beyond commit**; all deadlines
beyond the protected stop; exact ordered pre-access callback before any MMIO;
sticky rejection of every unknown, missing, duplicated, reordered or changed
observation. No execution may begin merely because a hash matches; schema,
manifest, journal, semantic readiness and timing predicates also run.

All original 361 cells/five identities are retained. Five ten-cell journal appends
produce **411 final cells**; the return stack pops then pushes its exact new return.
Full logical equality precedes chained hashing at every observation, including
unchanged hint/debt/RTC/timer state. No protected field was removed.

Predicted final registers are enumerated in the certificate: r0=0x1000 (not a
status result), r1=0x04000280, r2=0x04000290, r3=0x1000, r12=0,
SP=0x027E3654, LR=0x02001A24, PC=0x020019B4; others unchanged.
CPSR=0x1F, NZCV=0000. ARM9 ordinal=281098019; ARM7 ordinal=96026779 unchanged.
Final divider deadline=1708437913, cap records=6, serial=506, epoch=496.
Final modeled canonical SHA-256 is
`ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526`.
Predicted RAM/DTCM/protected-field/save deltas and logical saves/Flash commits are
zero; inherited quotient/remainder remain unchanged. This is prediction and
ROM-free evidence, **not a new guest before/after measurement**.

## Certification evidence and limits

Authoritative `local/task-aw6/certification-008/`: **56,956 assertions** and
**seven process controls**: one 69-event terminal success (73), five failure
disposals (79), one disabled normal return (0). All expected results pass.
Scheduler/device/IRQ/ARM7/guest/old-halt/destructor/persistence sentinels are absent
after both successful and failed disposal. Independent Python checks verify
canonical SHA-256 and the whole 69-event chain.

Tests reproduce the captured observation exactly, then use extracted actual
source bodies on synthetic scalar objects: divider setup, cap reschedule, slice
hint, fast-limit publisher, active-debt take, refill/combine, RTC formula, timer
deadline getter and ARM7 wake predicate. The actual AW3 cap journal implementation
records all five nonshortening replacements. No guest interpreter or bus/MMIO ABI
is linked. This is **not** a new actual-live-provider coupling run; AW4's earlier
provider proof is retained, not relabeled as AW6 evidence.

Negatives cover every entry field mutation/omission, every protected observation
field at all 69 phases, every identity, hint/debt/HALT/wakeup/IRQ distinctions,
RTC true-vs-floor phase, enabled/disabled/cascade/ready timers, cap equality and
crossing before the first write, forbidden 12th cost, unknown timing/profile,
wrong MMIO/value/cost, journal/ordinal changes, missing/extra/reordered events,
chain tamper and unexpected scheduler/device/IRQ/ARM7/cap-change events.
Earlier compile/test-only attempts are preserved: ADL ambiguity was fixed; the
initial model exposed the additional captured halt7=1 and was source-reconciled;
a test's next fetch-class expectation was corrected from 3 to 1 (combined cost
remains 8). No runtime data or old predicate was edited to hide those failures.

Current framework/AU guards, prior evidence, attempt lock and SDL/headless/capture
executables remain hash-identical. Normal runtime semantics are unchanged; no new
selector/installer/AX dispatch path exists. No ROM patch, generated-C edit,
save/checkpoint mutation, game launch or live capture occurred. Unrelated files
were preserved.

## Next safe task

Separately authorize **ROM-free guarded integration of this reduced controller**
with the actual AU handoff/access-owner/provider interfaces. Preserve all AU
guards before transfer; transfer access ownership rather than disabling guards;
use the trusted passive provider and nonreturning success/failure disposal; prove
coupled positive/negative controls before considering execution. Current AU still
terminates at entry, so the static certificate is **not permission or a claim of
readiness to run the current executable past it**. Any later run needs separate
explicit authorization and exact fresh admission. No such integration or newly
certified prefix was executed in AW6. Stop after AW6.
