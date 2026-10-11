# Task AV — divider MMIO and timed polling safety map

**PARTIAL.** AU state, original ARM bytes, the actual divider implementation, and scheduler ordering are re-established by file-only checks. A precise **conditional 12-instruction AW candidate** is specified below. It is not ready to execute: AU did not capture the live cycle cap, code/data timing state, or divider peripheral state, and its terminal halt still returns through the scheduler tail. Those missing facts prevent certifying a safe executable continuation under the current harness. No AW execution or runtime changes were made.

AU: `f17f95ae2b2a15f7fced6f04d82d2593350d37a4`; AT: `6478bd11b386799a3f4e03f923c39227e982c51d`. Branch `codex/brainage`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`. ndsrecomp baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Evidence is committed forced Tier-3 exact-context original ARM plus static ROM/runtime-source inspection. No compiled parity or real-DS timing claim. Astra Medium/fresh-thread selection was unavailable; this report does not claim that setting.

## Re-established AU stop

The helper compares AU/AT reports and every tracked helper to their authoritative commits, reads the retained AU audit and complete terminal images, checks CPU observations and bus-read ledger against AU, checks the non-fetch/non-dispatch terminal event, and checks every mapped field. ROM header ARM9 mapping independently verifies all candidate/lookahead instructions and five pointer literals against both ROM and retained main RAM. The JSON records input hashes, disassembly, conditional full register states and access ledger. Input hashes are unchanged after checking.

Pending PC/opcode is `02001980 / E1C130B0 / STRH r3,[r1]`. AU did not fetch or execute it. r0-r12:

`00001000,04000280,04000290,00000001,020EA1BC,00000000,000000DA,020E9A00,00001000,00001000,020FD00C,00000000,0000048C`.

SP=`027E3654`, LR=`02001A20`; NZCV=`0000`, T/mode/I/F=`0/31/0/0`. DTCM `[027E3658]=02067568`. ARM9 ordinal=`281098008`, live ARM9 cycles **C0=3416875721**, ARM7 ordinal=`96026779`, slot cycles=`1708437825`. The recorded ARM7 cycle count is a slot observation, not proof of the next rendezvous behavior.

| Full terminal image | SHA-256 |
|---|---|
| Main RAM | `84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340` |
| DTCM | `a5313aa2084674d767307c09ebd86fb888ebf992b8f486602412f9499c55496f` |
| Save | `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb` |

All 35 mapped fields equal AU: phase/delay/correct-count/result=`1/1/1/1`; +7BC=`020E9F70`, +7C0=`02132750`, +7C4=0, +7C8=`00080000`, +7CC=`00060000`, +7F4=1. The JSON includes all 35 exact address/width/value triples. AU's seven-instruction ledger has nine reads, one DTCM write, no MMIO, zero logical save requests and Flash commits. AV also verifies the empty request/Flash logs and initial/session/terminal/final save hashes.

**Absent from the AU certificate:** DIVCNT, numerator/denominator/quotient/remainder arrays, divider deadline, live `g_cycle_cap`, `g_nds_fast_limit`, code-timing latch, complete CP15 timing state, deferred-cycle debt, pending IRQ/DMA/device deadlines, and a post-scheduler-tail peripheral audit. CPU/RAM/save equality cannot substitute for these. No checkpoint reconstruction or guest replay was used to invent them.

## Exact ARM path

Hexadecimal PCs, words and values below. Every instruction is AL except the stated NE branch. All fetches are Read32 from ROM-loaded **main RAM**; literals are also main RAM, not MMIO. All candidate instructions preserve NZCV. Unlisted registers and memory are unchanged. No stack access occurs in this candidate.

The cycle column is a **conditional timing certificate**, not an observed AU peripheral/timing state: code is Cached at each PC and both branch targets; literal data numD=3; MMIO numD=8; no deferred debt or exception. These conditions must be checked before any AW write.

| PC / opcode | Decode | Register/access/call effect | Cycles; end offset from C0 |
|---|---|---|---|
| 02001980 / E1C130B0 | STRH r3,[r1] | Write16 MMIO [04000280]=0001; no writeback | 8; +8 |
| 02001984 / E3A0C000 | MOV r12,#0 | r12=0 | 1; +9 |
| 02001988 / E582C000 | STR r12,[r2] | Write32 MMIO [04000290]=0; no writeback | 8; +17 |
| 0200198C / E3A03A01 | MOV r3,#1000 | r3=1000 | 1; +18 |
| 02001990 / E59F1014 | LDR r1,[pc,#14] | Read32 literal [020019AC]=04000298; r1=04000298 | 3; +21 |
| 02001994 / E5823004 | STR r3,[r2,#4] | Write32 MMIO [04000294]=1000 | 8; +29 |
| 02001998 / E5810000 | STR r0,[r1] | Write32 MMIO [04000298]=1000 | 8; +37 |
| 0200199C / E581C004 | STR r12,[r1,#4] | Write32 MMIO [0400029C]=0 | 8; +45 |
| 020019A0 / E12FFF1E | BX lr | Return to 02001A20, T=0, LR unchanged; runtime return-stack pop | 4; +49 |
| 02001A20 / EBFFFFE2 | BL 020019B0 | LR=02001A24; PC=020019B0; runtime return-stack push | 4; +53 |
| 020019B0 / E59F102C | LDR r1,[pc,#2C] | Read32 literal [020019E4]=04000280; r1=04000280 | 3; +56 |
| 020019B4 / E1D100B0 | LDRH r0,[r1] | Read16 MMIO [04000280]; r0=00008001 **only under candidate guards** | 8; +64 |
| **020019B8 / E2100902** | **ANDS r0,r0,#8000** | **Candidate stops BEFORE fetch/accounting/dispatch.** If executed with 8001: r0=8000, NZCV=0000 | 3; +67, excluded |
| 020019BC / 1AFFFFFC | BNE 020019B4 | Z=0 -> taken to read again; Z=1 -> 020019C0. Under the guarded first sample it would be taken | taken 4; excluded |
| 020019C0 / E59F1020 | LDR r1,[pc,#20] | On busy-clear exit: Read32 literal [020019E8]=040002A0; r1=040002A0 | excluded |
| 020019C4 / E3A00702 | MOV r0,#80000 | r0=80000, no flags | excluded |
| 020019C8 / E5912000 | LDR r2,[r1] | Read32 MMIO [040002A0], quotient low -> r2 | excluded |
| 020019CC / E5911004 | LDR r1,[r1,#4] | Read32 MMIO [040002A4], quotient high -> r1; old r1 addresses read | excluded |

The NE target is PC+8+(-4*4)=020019B4. The ANDS rotated immediate is 8000, with shifter carry 0; N=0, Z reflects the sampled bit15, V preserved. Completion after LDRH but before ANDS does not change the already sampled register value. No wrapper return, DTCM pop, caller continuation or gameplay resumption is included. AT maps those later conditional returns; AV does not authorize them.

ROM/data literals checked: `020019A4=04000280`, `020019A8=04000290`, `020019AC=04000298`, `020019E4=04000280`, `020019E8=040002A0`.

## Actual current runtime MMIO model

Paths are relative to `local/ndsrecomp`. Source hashes are in the JSON. Relevant divider function bodies are compared byte-for-byte after text newline normalization with the pinned baseline; the current diagnostic/runtime source is separately hashed. Local historical instrumentation is preserved.

* `external/arm-recomp-core/common/interpreter.cpp:667`: single load/store effective address; `access_cycles(effective_addr,access_w,false)`; STRH calls write16, STR calls write32, LDRH calls read16. Timing is accumulated, not committed to the clock during the access.
* `runner/src/tier3.cpp:148`: RtBus read/write adapters surround the underlying bus operation with existing diagnostic guards; each underlying access is made once. **AU's existing guards still reject these writes.** A successor cannot simply reuse AU's authorization.
* `runner/src/bus.cpp:419,903,931,951`: aligned I/O addresses are outside RAM/TCM resolution under the required address-map guard, route through `io_read/io_write`, preserve width, and reach `nds_io_read/nds_io_write`. Bus tracing/profiling may record the access; that is host instrumentation, not a guest IRQ or DMA.
* `runner/src/io.cpp:3284,3455`: **cpu==0 (ARM9)** and `math_addr` route to `math_reg_read32` or `math_reg_write`, then return. ARM7 does not enter these divider handlers. These math accesses do not enter timer, FIFO, SPI, card, Flash, DMA or IRQ register handling.

| Instruction PC | Address | Access/value | Stored state / handler effect |
|---|---|---|---|
| 02001980 | 04000280 | Write16 0001 | Replace all 16 DIVCNT bits with 0001, then `start_div`: DIVCNT=8001 |
| 02001988 | 04000290 | Write32 00000000 | `g_div_numer[0]=0`; `start_div` |
| 02001994 | 04000294 | Write32 00001000 | `g_div_numer[1]=1000`; `start_div` |
| 02001998 | 04000298 | Write32 00001000 | `g_div_denom[0]=1000`; `start_div` |
| 0200199C | 0400029C | Write32 00000000 | `g_div_denom[1]=0`; `start_div` even though mode 1 ignores high word for division |
| 020019B4 | 04000280 | Read16 status; conditional 8001 | Return current DIVCNT masked to 16 bits; no compute or service |
| 020019C8 | 040002A0 | Read32 quotient low | Return `g_div_quot[0]`; conditional completed value 0; excluded |
| 020019CC | 040002A4 | Read32 quotient high | Return `g_div_quot[1]`; conditional completed value 1; excluded |

`math_reg_read32` (`io.cpp:491`) also directly reads numerator/denominator words at 290/294/298/29C. Reads of **all seven requested addresses** are passive: no state change, deadline update, IRQ, DMA or time advance. Result-register writes have no handler case and are ignored. `math_reg_write` merges by width/offset, so the aligned 32-bit operand writes fully replace their words; the aligned control halfword replaces all stored control bits. It does not implement a hardware-style writable-mode-bits-only mask. AV describes this implementation, not undocumented real hardware behavior.

`start_div` (`io.cpp:406`) only sets busy bit15, replaces `g_div_deadline`, and calls `nds_reschedule_slice`. It does **not** calculate quotient/remainder, clear them, latch a separate operand copy, or immediately raise an IRQ/DMA. Control write 0001 clears any inherited bit14 as part of replacement; operand writes merely OR busy and otherwise preserve control. Under no intervening completion, DIVCNT remains 8001 throughout setup.

For ARM9 the write sees the **pre-instruction-commit** clock: `active_system_timestamp()=g_runtime_cycles>>1`. Delay is 18 system cycles for mode0 and 34 for modes1/2/3. Here mode1 means deadline `floor(Cwrite/2)+34`, corresponding to 67 ARM9 cycles from an odd Cwrite or 68 from an even Cwrite. This is a deadline distance from the MMIO handler's clock, not 68 additional cycles after store retirement.

There is exactly **one scalar divider deadline**, not a queued event per write. Each of the five setup writes replaces it, even for an idempotent write. Previous divider events cannot survive as separate callbacks. A previously shortened **slice cap can survive**: `runtime_arm.cpp:1186` converts the deadline to active-CPU cycles, updates `g_cycle_cap` and invalidates `g_nds_fast_limit` only if the cap was zero or the new deadline is earlier. Later writes with later deadlines do not lengthen that cap. An early rendezvous caused by that stale cap checks the **latest** divider deadline; it does not complete an old operation.

`nds_next_system_event_time` (`io.cpp:2233`) includes the current divider deadline in the device minimum. `nds_run_system_events` (`io.cpp:2283,2328`) checks auxiliary SPI, SPI, card, divider, then square root; when divider is due, it sets the deadline to UINT64_MAX and calls `finish_div`. `finish_div` clears bits15/14, computes from **current** mode and operand arrays, and sets bit14 iff both denominator words are zero. Mode1 uses signed 64-bit numerator and signed low32 denominator. It handles zero divisor and INT64_MIN/-1 explicitly. Thus no divide-by-zero C++ trap is required by intermediate operands, even if serviced early. It has no IRQ/DMA/save effect. The surrounding event-service function may service other devices with IRQ/DMA effects.

Final operands are numerator `00001000:00000000` (2^44), denominator `00000000:00001000`; after a properly serviced completion without other writers: quotient `00000001:00000000`, remainder zero, DIVCNT=0001, deadline=UINT64_MAX. Until completion, quotient/remainder retain inherited values. Those values are **not known from AU**; they must not be replaced with the eventual answer in an AW expected-state table.

ARM7 cannot directly write this divider model through its CPU math-address path, and no ARM7 cooperation is needed to compute it. ARM7 catch-up, other devices, DMA and ARM9 interrupt handlers may nevertheless affect the wider experiment, timing, memory or future operand writes. Exclude them for the candidate instead of claiming whole-console noninterference.

## Scheduler/time contract and the AU halt gap

1. `scheduler.cpp:198` loads the active slot clock, establishes a slice cap, and dispatches. Forced Tier-3 is selected by the experiment's frontend setup; inspect `main.cpp:2270` and AU installer/build inputs. No new build or installer ran in AV.
2. `tier3.cpp:341-355` synchronizes architectural state and calls the AU control hook before bank lookup, instruction accounting, fetch and `Interpreter::step`. RtBus data timing accumulates separately. Math writes use the still-uncommitted clock.
3. `tier3.cpp:525-556` combines instruction code/data/internal costs and then commits `cyc + runtime_deferred_cycles_take()` to `g_runtime_cycles`. There is **no `nds_run_system_events` call per instruction**.
4. After that commit, Tier-3 tests halt/DMA, updates its runtime call-return stack for BX/BL, can accept an IRQ **before the next top-of-loop guard**, then tests instruction-stop and slice expiry (`646-676`). If the cap is reached, it unwinds immediately; a guard at the next PC need not get control first.
5. `scheduler.cpp:225-280` restores unwind state, observes active terminal halt, and copies live cycles into the CPU slot. Returning because of terminal halt does **not** exit `scheduler_run_round`.
6. The round ticks ARM9 timers, runs GPU3D, derives rendezvous from actual ARM9 slot cycles>>1, catches ARM7 up, then ticks display/SPU/Wi-Fi/RTC and runs system events (`437-525`). ARM7 catches up to actual time, not the original plan; both CPUs can overshoot by their final atomic instruction. A power-off check can skip the later device service, so fairness is conditional on normal ongoing operation.
7. `tools/task_au/diagnostic.h:28` calls `nds_halt`; `runtime_arm.cpp:1211` sets the active terminal flag and requests yield. It does not halt both slots, suppress device ticks or abort the round. The AU frontend checks terminal status **after** `scheduler_run_round` returns (`frontend.cpp:3887-3893`). Even halting both slots would not itself skip the device-service tail.

Therefore **a pre-next-PC stop is not automatically a pre-event stop**. A store can commit enough cycles to expire a cap, and scheduler service can run before its successor's control hook. A snapshot taken in that hook also does not prove nothing runs after the snapshot. A single mode1 store with ordinary small cost cannot itself reach its new 67/68-cycle deadline, but a large deferred debt can; existing cap expiry still exposes unrelated scheduler activity. Do not infer an event-free prefix from PC/ordinal or unchanged RAM alone.

The current source has read-only state-copy facilities (`io_savestate_export`, divider fields at `io.cpp:2601-2606`; scheduler debug/state accessors), but AU did not record the required fields. Do not invoke full checkpoint export from an in-round hook: scheduler savestate quiescence rejects an active round. A future diagnostic needs passive field-copy access and guards without changing live state or calling runtime MMIO. Merely calling timing helpers for inspection can update timing latches/last-access fields; inspect copies/explicit passive diagnostics instead.

## Poll boundedness

ROM loop: Read16 280 at B4; ANDS 8000 at B8; BNE at BC. There is no ROM-local count bound. A status read never completes division. If instructions are stepped without event service, busy can remain set indefinitely despite advancing instruction/cycle counters.

Under normal fair scheduler service, ongoing ARM9 time, no repeated operand writes/IRQ interference and no terminal/power-off state, the finite latest deadline is included in scheduling and `finish_div` eventually clears busy. Deadline service occurs at a rendezvous at or after that timestamp, not necessarily exactly when a read retires. Other CPU/device execution can intervene; this is not a unconditional wall-clock, instruction-count or whole-call bound in AU's exact state.

For the **explicit cached/no-interference arithmetic case only**, final write starts at C0+37, retires at +45, deadline converts to C0+105. Earliest service is 34 system cycles after its pre-write timestamp, or 60 ARM9 cycles after its retirement. Setup reaches B4 at +56. Busy-loop costs are LDRH=8, ANDS=3, taken BNE=4. Poll reads begin at offsets 56,71,86,101,116. Read4 samples busy before the deadline, retires at +109 and can trigger the due rendezvous; read5 then sees clear. The exit is at +128 after 5 reads, if those timing/fairness/noninterference assumptions hold. This is arithmetic lookahead, **not an executable AV/AW loop certificate**. Missing live timing/cap/IRQ/event state and the scheduler tail prevent asserting this count for AU.

Stopping before the first poll read (11 instructions, +56) removes dependence on the returned status. One deterministic read (12 instructions, +64) can be isolated if no event service/interrupt can occur and the timing/cap gates below pass. A full first poll iteration is not approved: ANDS would retire at +67, at the first write's retained cap, causing a scheduler exit before the BNE guard. A normal instruction-budget stop alone is insufficient.

## Selected AW candidate, pending eligibility proof

**Candidate:** start AU PC `02001980`; execute exactly the first 12 rows; stop at `020019B8` **after the one status Read16, before ANDS fetch/accounting/dispatch and before any scheduler/device tail**. This is the largest no-rendezvous prefix under the explicitly gated timing configuration: +64 < first-write cap +67; the next instruction reaches that cap. This does not establish that AU's actual entry cap satisfies the gate. No live fields may be changed to make the gate pass. If a gate fails or cannot be inspected, stop before the first write and report failure; do not shorten/extend/retry the experiment ad hoc.

Exact executed PCs:

`02001980,02001984,02001988,0200198C,02001990,02001994,02001998,0200199C,020019A0,02001A20,020019B0,020019B4`.

12 instruction fetches plus two literal Read32 operations plus one status Read16 = **15 reads**, and exactly five MMIO writes. All underlying operations are single calls, with no diagnostic MMIO readback. Stop opcode inspection uses frozen code bytes. Quotient registers are not read.

Let entry numerator words be N0/N1, denominator D0/D1, quotient Q0/Q1 and remainder R0/R1. These are required passive snapshots, **not invented constants**. With no completion/interference:

| Write PC | Pre-write ARM9 cycle | DIVCNT | Numerator high:low | Denominator high:low | Replaced system deadline |
|---|---:|---|---|---|---:|
| 02001980 | 3416875721 | 8001 | N1:N0 | D1:D0 | 1708437894 |
| 02001988 | 3416875730 | 8001 | N1:00000000 | D1:D0 | 1708437899 |
| 02001994 | 3416875742 | 8001 | 00001000:00000000 | D1:D0 | 1708437905 |
| 02001998 | 3416875750 | 8001 | 00001000:00000000 | D1:00001000 | 1708437909 |
| 0200199C | 3416875758 | 8001 | 00001000:00000000 | 00000000:00001000 | 1708437913 |

Q0/Q1/R0/R1 remain identical to the entry snapshot after every access. First write removes any old divider deadline; subsequent writes replace the new one. The live cap becomes `min(nonzero entry cap,3416875788)` (zero entry cap becomes 3416875788) and is not extended by later writes. Fast limit is invalidated by rescheduling only when cap is shortened, then can be republished by Tier-3. `runtime_arm.cpp:1356` publishes the cap only if fast polling is enabled and there is no breakpoint, terminal/stop/event flag, deferred debt, changed active code, halt, DMA stall or pending IRQ; otherwise it publishes zero. Audit this rule and its instrumentation count; do not require the fast limit to remain zero. At the first read the clock is 3416875777; it returns 8001 and retires at **3416875785**, with current divider deadline still 1708437913. Scheduler system timestamp and inactive slot state must stay at their captured entry values until terminal diagnostic disposal.

Predicted final r0-r12 under these gates:

`00008001,04000280,04000290,00001000,020EA1BC,00000000,000000DA,020E9A00,00001000,00001000,020FD00C,00000000,00000000`.

SP=`027E3654`, LR=`02001A24`, PC=`020019B8`; NZCV=`0000`; T/mode/I/F=`0/31/0/0`; ARM9 ordinal=`281098020`, ARM7 ordinal/cycles unchanged. The setup return pops its internal runtime return entry; BL pushes 02001A24. Architectural stack is untouched. The JSON gives every intermediate register state and cycle offset.

Main RAM/DTCM/save must remain byte-identical to AU, including saved LR at 027E3658 and all 35 fields. Zero logical save requests, Flash commits or dirty transition. No game-level meaning or completion is inferred. DIVCNT/operand/deadline/cap state changes are the intended modeled effects; quotient/remainder must not change. Instruction/bus trace counters and timing instrumentation changes are expected and must be separately accounted for.

### Mandatory fail-closed AW gates (specification only)

1. Reconstruct exact AU causal provenance in a separately authorized AW harness; verify all committed identities, ROM, full CPU/flags/mode/ordinal/cycles, code/literals and complete RAM/DTCM/save/field equality. No fabricated CPU/peripheral state. Existing AU denies MMIO; successor guards must be separately reviewed.
2. **Before the first write**, passively snapshot divider fields, live clock/cap/fast limit/deferred debt, active CPU, both slot states/clocks, scheduler timestamp/round state, code latch and CP15 timing classification/maps, IRQ pending state/masks, halt/wake, DMA/GX stall, event-break/insn-stop/terminal flags and runtime return stack. Record pending system/device deadlines and timer state. AU's architectural I=0 makes IRQ exclusion essential.
3. Establish current and branch-target code Cached timing; literal numD=3; math MMIO numD=8 and correct I/O address routing; debt=0. Assert live entry cap zero or **strictly greater than 3416875785**. Any unknown timing/cap or pending IRQ/halt/DMA/stall/stop is a pre-write rejection. Do not disable IRQs, lengthen caps, clear events, reset the divider or patch CP15 to satisfy this.
4. Before each dispatch require exact PC/opcode, entire CPU/flags and cumulative cycle/ordinal state from JSON. Validate the complete ordered ledger, address/width/source/value; only the five listed writes and three data reads are allowed. Reject all extra MMIO, data accesses, save/Flash calls, or wrong active CPU before the underlying operation. Underlying math writes return directly; never verify by MMIO readback.
5. Passively verify divider operands/control/deadline after each write; Q/R equal entry snapshot, exact restart count five, completion count zero. Pre/post service counters must show **zero** ARM7 dispatch, IRQ acceptance, scheduler rendezvous/event-handler/timer/GPU/device service since arming. Guard those entry points before side effects: a post-hoc counter mismatch is evidence of failure, not prevention. Include all-event monitoring because unchanged divider results cannot exclude unrelated hidden events.
6. Check prospective next instruction cost/debt and current cap before dispatch; reject any step that can yield before the next guard. At B8 require exactly 12 dispatches/15 reads/5 writes and terminal state above. No fetch of B8, no ANDS, BNE, second status read, quotient read or divider completion.
7. **Do not reuse `finish()->nds_halt()` as an event barrier.** AW must arrange diagnostic-only terminal disposal that cannot return into the scheduler tail, or prove and enforce a pre-side-effect scheduler fence on every exit path, including errors. Capture/flush ROM-free audit and permitted disposable evidence before disposal; prevent shutdown save/Flash commits. Normal runtime behavior must not be refactored. If this cannot be provided, keep the AU boundary and do not dispatch any AW instruction.
8. Re-audit full RAM/DTCM/save/fields, retained return-stack relationship, CPU/clock and complete peripheral/event snapshots at the true end. Preserve source checkpoint/save and failure evidence; no state repair, counter rollback or retry past a mismatch.

The first-write-only alternative has fewer MMIO effects, but **the same stop-tail and missing-cap issue**; it is not automatically certified by an instruction budget of one. Complete setup/pre-read is safer with respect to status sampling but likewise needs the event fence. For this reason AV does not silently promote either fallback to an unconditional safe AW run.

## Validation, outcome and limits

Run `python -B tools/task_av/check.py`. It checks committed provenance and retained full images; ROM words/literals and disassembly; baseline divider-function identity; current source ordering; exact conditional register/deadline/cycle arithmetic; and ten negative certificate mutations. All focused checks passed. No AU preflight/install/build/run script, emulator, runtime device function or scheduler is executed. The checker is file-only Python plus read-only Git and Capstone decoding. `--export` writes only the AV JSON. Input SHA-256 before/after checks cover retained evidence/ROM/current source.

The focused helper initially caught an off-by-one in drafted absolute deadlines caused by floor(C/2) at odd/even write clocks; corrected expected deadlines are in the table and checked independently. No guest run was used to resolve it.

PARTIAL is deliberate: the model is identified reliably (so not BLOCKED), and its scheduler ordering is mechanically established. The missing exact entry/tail proof prevents claiming an eligible, safely executable AW prefix in the current harness (so not FULL PASS). The conditional 12-instruction design provides a concrete review target; its entry gates might reject the reconstructed AU state. No loop entry or exact poll-count claim is authorized. No runtime sources, generated recomp-C, ROM, checkpoint or save were modified. The unrelated `jarvis-inbox-v1.zip` is preserved.

**Stopped after AV. AW was not started.**
