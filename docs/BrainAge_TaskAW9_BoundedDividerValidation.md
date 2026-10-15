# Task AW9 - single bounded divider validation

**FULL PASS. One live attempt, admitted once, no retry.** Exactly 11 original ARM
instructions executed through Tier-3, with five divider MMIO writes and zero MMIO
reads. The process terminated nonreturningly after retiring 0x020019B0, before the
next instruction's fetch/accounting/dispatch. The one-shot authorization is consumed.

## Preflight and isolated permission

Authority: AW8 `c0ac62cae632715157fcb3db52b982cc86104baa`, certificate payload
`8381e1335266a05767982f292eb5237eb157bb5d8d9ea431c1a81d7552bae417`.

Before building or launching, `preflight.py` reserved the task-wide exclusive
`one-shot.lock`, verified the checkout, certificate, frozen source/build/evidence
identities, then reran unchanged AW8 `certify.py`. Its complete resulting
certificate was identical to the frozen AW8 certificate. Immutable checkpoint,
save, frozen AU input and actual ROM SHA-1 checks also passed. No fixture tests,
additional inference smoke or guest replay were used for this artifact preflight.

An isolated runner was built at `build/task-aw9-once/nds_runner.exe`, SHA-256
`e9cce7bc45d0e4e52e973077a91804e9397e89696a666989e40046d7984f98e2`.
It recompiles 48 native sources and reuses unchanged existing bank/support
archives. No generator or generated recomp-C edit was involved. Production source,
prior executables and old evidence remain unchanged.

Only the ignored private source overlay adds:

- Compile-scoped AW9 permission; fixture/model capabilities are forbidden.
- A one-use certificate/entry/nonce ticket and exclusive boundary claim.
- An additional handoff **after every existing AU terminal guard**, before the
  old halt/capture path. It invokes unchanged `task_aw6::entry` on original passive
  provider observations, compares the entire authenticated entry, then uses the
  unchanged AW7 repeat-sampling/owner/ledger handoff.
- Runtime callback permission only after that handoff has accepted its first
  observation. Access-before validation, all prospective checks, canonical chain,
  post-access state checks and terminal/failure disposal remain unchanged.

Expected canonical metadata is used only for comparison and first-mismatch
reporting. It is never injected into guest state or provider outputs. Original
ROM/RAM/DTCM/save identities are computed by the original live providers. There
are **no AW8 historical-identity adapters** in this runner.

Any preflight or transcript failure would flush the audit and `_Exit` without a
retry or ordinary halt. The actual attempt had no such failure.

## One actual attempt

`run.py` reserved `launch.claim` and called `Popen` exactly once, PID **67860**.
The private runtime ticket was claimed once at the guarded AU boundary. Neither
attempt lock nor ticket claim is removed; the helper cannot be reused.

The same immutable Task G `11 - 7 = 4` checkpoint and certified AU prerequisite
path were reused. Checkpoint SHA-256:
`3911c3e98f90d77916497fd82e4f7ae49e7ca825273e52a90b66fd05ce2b2f2f`.
Frozen gesture digest:
`88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`.
Ten tokened SDL-queue frontend events reproduced recognition **2 then 4**.
The original AU setup replay still passed its eight observations, nine reads,
one stack write and all CPU/full-memory/save guards. Earlier certified setup and
ordinary checkpoint preparation are distinct from the 11-instruction candidate;
this is not a claim that the whole process executed only 11 guest instructions.

At 0x02001980, before candidate fetch/accounting/dispatch, exact live admission
and repeated sampling passed all **361 scalars/five identities**, digest
`0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c`.
There was no normalization, mismatch, fallback, emergency termination or retry.

## Actual instruction and MMIO transcript

| Original PC | Cost | ARM9 commit cycle |
|---|---:|---:|
| 02001980 | 8 | 3416875729 |
| 02001984 | 1 | 3416875730 |
| 02001988 | 8 | 3416875738 |
| 0200198C | 1 | 3416875739 |
| 02001990 | 3 | 3416875742 |
| 02001994 | 8 | 3416875750 |
| 02001998 | 8 | 3416875758 |
| 0200199C | 8 | 3416875766 |
| 020019A0 | 4 | 3416875770 |
| 02001A20 | 4 | 3416875774 |
| 020019B0 | 3 | **3416875777** |

Actual MMIO writes, each before instruction-cycle commit:

| PC | Address / width / value | Divider deadline | Journal serial |
|---|---|---:|---:|
| 02001980 | 04000280 / 2 / 1 | 1708437894 | 502 |
| 02001988 | 04000290 / 4 / 0 | 1708437899 | 503 |
| 02001994 | 04000294 / 4 / 4096 | 1708437905 | 504 |
| 02001998 | 04000298 / 4 / 4096 | 1708437909 | 505 |
| 0200199C | 0400029C / 4 / 0 | 1708437913 | 506 |

The two other data accesses are the certified RAM literals at 0x020019AC and
0x020019E4. There are **zero MMIO reads**, including zero divider status reads.
Every write retains cap/fast-limit **3416875778**. Epoch 496 is unchanged;
journal records grow 1 -> 6, serial 501 -> 506. No cap-change observation or
fast-limit republish occurs. The first write fits the original cap independently;
no deadline replacement rescues an otherwise inadmissible instruction.

The actual ledger contains exactly **69 accepted observations**: 11 instruction,
18 access-before, 18 access-after, 11 cycle-commit and 11 retired. All event
metadata, **every full canonical state**, and every chain link are byte-identical
to AW8's certified reference transcript. Independent read-only analysis checks
the instruction/access order, values, costs, epochs/serials and full final state.

## Terminal state and forbidden successor

- Final ARM9 cycle **3416875777**, ordinal **281098019**: +56 cycles/+11 instructions.
- Retained cap **3416875778**: exactly one cycle remains.
- ARM7 cycle **1708437825**, ordinal **96026779**: unchanged during the candidate.
- Full final **411-scalar/five-identity** digest:
  `ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526`.
- All final registers match AW8; SP=0x027E3654, LR=0x02001A24, CPSR=0x1F,
  NZCV=0000. Divider state/deadline and all immutable/latent fields match.

**Architectural PC becomes 0x020019B4**, as required after retiring 0x020019B0.
This is not execution of that instruction. There is no instruction event, fetch
access, accounting increment or dispatch at 0x020019B4. Ordinal ends at 281098019,
not 281098020. Passive code-word inspection by the manifest is not a guest fetch.

The final event is the reduced controller's terminal callback. It flushes/closes
the audit and invokes nonreturning `_Exit(73)` **before** the next loop, IRQ check
or scheduler return. No IRQ/scheduler/device/ARM7/cap-change event occurs in the
protected ledger, and no ordinary halt/final-save output occurs. Process exit 73
was awaited normally; no forced termination or shutdown continuation was used.

## State/save safety and limits

Candidate RAM and DTCM identities are unchanged from the admitted AU entry.
The earlier certified AU prerequisite stack write is not concealed by that
candidate-only comparison. No additional RAM/DTCM write is attributable to the
11-instruction candidate. Save counts and dirty state remain zero in every
canonical observation; request and Flash trace files are empty.

Logical save requests **0**; Flash commits **0**; changed save bytes **0**.
Before/after save SHA-256:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
Original and disposable source checkpoints, original save and previous artifacts
remain unchanged. The process is disposed; it does not resume a half-run helper.

This validates the real forced-Tier-3 divider-write prefix, not compiled parity,
status-read semantics, completion events, correctness/scoring/progression, or
exercise completion. No ROM patch, generated-C edit, broad scheduler change,
guest-state forgery or save-format change was made.

## Artifacts and next safe task

Local evidence: `local/task-aw9/attempt-001/` including `preflight.json`,
`aw8-preflight-command.json`, `session.json`, `capture.jsonl`, `analysis.json`,
frontend/save traces and launch/ticket claims; task-wide `local/task-aw9/one-shot.lock`.
The capture audit SHA-256 is
`cfa3acc3e55bd2abf8504f662ded00ac4ea14c3fa617a89b9f3ae6fc0e545f8b`.
Game-containing snapshots, checkpoint/save copies, native binaries and the
private source overlay remain ignored/local. Committed helpers are ROM-free.

**Remaining authorized runs: zero.** The next safe task is ROM-free analysis and
certification of the next slice/status boundary from this captured terminal state.
The forbidden next status load costs eight cycles, while only one remains under
this cap. It is not certified by AW9; do not extend the prefix, reset a cap to
make it fit, execute the status read or replay without separate authorization.
