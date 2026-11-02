# Command 4: default pair stores, unresolved callback/initialization contracts

## Outcome and reproducibility

The investigation resolves the **default operation identity** and its mode-0
pair-store coverage. It does **not** prove unconditional ABBC safety. A selected
descriptor can override command 4, and the default handler itself consumes
records produced by still-opaque commands 2/3. A useful directly connected C
hypothesis, `func_0200af44`, is added instead of speculative dispatcher/handler C.
The canonical batch grows from 10 to **11** independent authored functions.

```powershell
python -B tools/matching_phase1/batch.py --publish-status
python -B tools/matching_phase1/partial_link.py --publish-status
python -B tools/matching_phase1/command4_contract.py --publish
```

The link command creates its own one-attempt artifact, then only validates/reuses
it. It never relinks the old six/eight/ten-object outputs. Public machine evidence:
`command4_contract_status.json`, `command4_link_status.json`, `batch_status.json`.
Raw decoded listings/bytes, compiler objects and maps remain under ignored
`local/matching_phase1/`; no guest execution or live descriptor sampling occurs.

## Verified scope, not a subsystem reconstruction

Inputs remain the exact USA Rev1 ROM, extracted ARM9 and ten pinned metadata
files in `tools/matching_phase1/batch.json`. Inferred ARM boundaries are verified
against actual bytes and outgoing relocations, not treated as original objects:

| Original range | Extent / code / pool | Role |
|---|---:|---|
| `0200A464..0200A5E4` | 384 / 384 / 0 | dispatcher, 96 instructions, 114 labelled CFG edges, four exits |
| `020097B8..020099BC` | 516 / 516 / 0 | **one selected default command-4 operation**, 129 instructions, 170 CFG edges, six exits |
| `02009CFC..02009E88` | 396 / 392 / 4 | selector/status scaffold; computed result switch and one table literal |
| `0200A5E4..0200A628` | 68 / 68 / 0 | completion scaffold linking dispatcher to selector |
| `02009E88..02009EC8` | 64 / 64 / 0 | status/unlink scaffold |
| `0200AF44..0200AF8C` | 72 / 72 / 0 | directly invoked queue insertion, new C |
| `0200AF8C..0200AFB8` | 44 / 44 / 0 | minimal unlink/lifetime scaffold |

All seven range hashes, calls and literal relocations are in the audit JSON.
No pools are counted as instructions. A628's small completion loop was triaged,
but its callees/semantics remain opaque; A6BC's 540-byte inferred extent was
identified, not recursively audited. Commands 2/3, 9C1C, 9BC0 and general
descriptor initialization remain explicit boundaries. This is dispatcher + one
default operation with selector/queue/cleanup scaffolding, not all-command work.

## Exact route and selection

AD94 supplies scratch, command 4 and descriptor-derived register values. A464
actually consumes r0/r1 here; no use of AD94's incoming r2/r3 is established.
It loads the descriptor pointer from scratch+8, writes command to +0x10 and
initial status 2 to +0x14, sets scratch+0xc bit 1, then calls opaque 6E9C.
Descriptor+0x10 bit 0x80 causes explicit return zero via 9E88. Otherwise
`(1 << 4) & 0x1fc != 0` sets scratch+0xc bit **4** before AF44 appends scratch
to the list rooted at descriptor+0x14.

Descriptor bits 8/0x10 select the wait route; otherwise A464 sets bit 0x10 and
restores the saved helper token via 6EB0. Descriptor+0x4c bit 0x200 optionally
invokes **descriptor+0x48 with (scratch,9)** at A540. This is a notification-like
call by observed arguments, **not** the default command-4 operation. Its actual
identity/effects are not statically established. Wait loops and helper progress
are not assumed to terminate. The machine audit inventories direct scratch-root
reads/writes by PC, offset, width and predicate, separately from indirect
descriptor, local-record and pair accesses.

On the stable synchronous route, A5E4 calls 9CFC(scratch, scratch+0x10), then
9E88 with its result, then opaque A6BC and possibly A628, and finally returns
`scratch[+0x14] == 0`. Normal completed-status preservation is an explicit
external requirement; a nonzero dispatcher result is not the raw operation code.

9CFC selects a custom callback from descriptor+0x48 if descriptor+0x4c contains
`1 << command`. For command 4 the gate is **0x10**, distinct from notification
9's gate. Custom result 7 falls back; result 8 clears this enable bit and falls
back; result 6 has deferred-completion/wait behavior. Other statuses feed the
status machinery. In particular **custom result zero can yield success with no
proved pair writes**. No runtime descriptor callback address or gate value was
observed in this task; global BSS-derived descriptor identity cannot be guessed.

Fallback uses the literal at **02009E84 = 020C606C**. The verified data relocation
at **020C607C** (slot 4) points to **020097B8**. The audit checks both original
words, metadata ownership and relocation targets. No other table handler is
decoded recursively. This resolves the precise default target without falsely
identifying the optional runtime override.

## Default operation: path-sensitive output contract

97B8 caches scratch+0x3c (mode) in its own stack word, loads suffix pointer +0x38,
and calls selector command 2 **without checking its return**. It parses components
separated by slash/backslash. Dot advances; dotdot conditionally reads halfword
scratch+0x20 and word +0x28 and may invoke opaque 9C1C. Components over 127 bytes
fail on the nonwrapping, signed-nonnegative length domain (the comparison is
signed GT, not a universal overflow guard). It publishes its local stack+8 in
scratch+0x2c, clears +0x30, and repeatedly
calls selector command 3. A nonzero command-3 result fails; otherwise it reads
local record kind/length and compares the component through opaque 9BC0. An
intermediate match copies three local words into scratch+0x2c..+0x37 and calls
command 2 again, also ignoring its result.

| Branch family | Operation result / direct pair effect in mode 0 |
|---|---|
| empty/end suffix; zero-length component | 1; no direct pair write |
| component length >127 | 1; no direct pair write |
| command 3 returns nonzero | 1; no direct pair write |
| kind/length/name mismatch | retry enumeration; may not terminate |
| dot/dotdot/intermediate component | continue; depends on opaque context/parent operations |
| terminal matching record | **0; two word stores**, then return |

The six physical return sites are 9854, 98BC, 98E4, 9954, 9974 and 99B8 (all
in ARM9 0200xxxx). 9954's nonzero-mode guard is impossible for cached mode zero;
the mode-zero 99B8 exit returns 1. The **only mode-zero zero exit** is 9974.
CFG cut tests independently establish that both stores at **02009968** and
**0200996C** dominate this exit. Destination comes from scratch+0x40 at 9958;
values come from local stack+8/+0xc. Their byte write mask is **0xff**, assuming
normal valid, nonaliasing storage and no opaque stack corruption. Nonzero mode
also has a distinct **12-byte** output copy; it must not be applied to ACD0's
eight-byte mode-zero pair.

**Writing eight bytes is not proof their source values are initialized.** The
record+0xc/+0x10 metadata are read first; the name comparator then needs the
record+0x14 name buffer for the component length. A terminal match additionally
needs record+0..7; an intermediate match needs record+0..11. These are separate,
path-sensitive command-3 initialization requirements. Record capacity is 20
bytes plus a 128-byte local name area; the checked component bound is 127.
9BC0's count/read/lifetime behavior remains opaque, not a guessed string API.

Default failure paths have no direct pair store, but **opaque nested calls may
write partially**. There is no rollback proof. Nor does default operation status
zero prove the outer dispatcher ultimately returns nonzero after all other work.

## Scratch initialization and stack lifetime

AD94/AEE8 establish 46/68 scratch bytes. A464 writes the previously unknown full
word +0x14, bringing directly known bytes to 50 before opaque work. Offsets
**0x1a..0x2b remain unknown**. The handler's dotdot halfword+0x20 and word+0x28
are in that unknown region; only command-2 behavior can qualify them. Because
command-2 return is ignored, a status check cannot be invented to prove them.
Wait/signal helpers receive scratch+0x18, where only the first halfword is known;
their actual read widths/initialization obligations remain unproved.

AF44 establishes **real pointer publication**, not nonretention: it stores the
scratch pointer into the descriptor list/tail's next field. 9E88 calls AF8C to
unlink and clear both scratch link words before writing the status and calling
5598. That shows a removal mechanism, not that every custom/deferred path uses
it in time or that other opaque recipients retained no copy.

97B8 also stores **its own stack+8** in scratch+0x2c before command 3; the terminal
match does not restore that field. This is safe only if no later work dereferences
that now-dead local pointer. It is not evidence of a title bug: scratch itself
may be dead synchronously. Required contract: no callback, enumeration/parent/
comparison helper, queue worker or completion path may retain or dereference
scratch/output/handler-local stack pointers beyond their valid lifetime.

Null/short/unterminated inputs, invalid link graphs, cross-region aliases,
out-of-bounds external writes, concurrent mutation and invalid descriptor fields
are not silently made safe. No host dereference of a game address is performed.

## Actual source progress and object evidence

`func_0200af44.c` is a readable unlink-and-append hypothesis, with a shared
**hypothesis-only two-pointer prefix** in `contracts.h`. Its known r0 retention
is represented as returning entry. All old ten C bodies remain unchanged; the
shared declaration addition does not change their independent objects or raw
function bytes. No dispatcher/default-operation/AD94 C body is fabricated.

The queue model reuses the existing virtual-byte checker for original and
compiled instructions: **90 cases** cover detached and attached entries, each
position in source chains of length 0..4, destination lengths 0..4 and same-list
reinsertion. Invalid storage, null/unaligned heads and cyclic traversal are
negative-tested without unsafe host memory access. Bounded checks are not
whole-title runtime parity.

The real new LLD 20.1.2 `-r` output is
`local/matching_phase1/runs/partial-link-command4-queue-v1/linked-authored.o`,
SHA-256 **a8030d1e292bc21990153130c8877744cbcea886bf7e6b7da3090f71f31036c5**.
It has 11 unique global STT_FUNC definitions, ARM EABI5/v5TE ARM conventions,
12 R_ARM_CALL relocations (7 internal / 5 external) and 11 owned exidx entries.
The five imports remain **19024, AA5C, AB7C, A464, AD94** (020xxxxx); none is
falsely claimed resolved. AF44 connects through the audited but still opaque
dispatcher, not a newly closed compiled edge. No static data, COMDAT, fabricated
API body or original object was introduced. Section/symbol offsets, addends,
hashes, unresolved inventory and all three preserved baselines are in link JSON.

All 11 functions compile and pass their bounded models. AF44 is original 72 /
generated **64 bytes**, **MISMATCH**. Old diagnostics remain one trivial Clang
match and nine mismatches; total now one trivial match / ten mismatches.
**Authentic original-toolchain matches = 0; Gate0 OPEN.** Original compiler,
revision, prototypes and compilation-unit partitions remain unqualified.

Regression discovery runs the prior **160** tests plus **23** new contract/queue
tests: **183 PASS**, no skips/errors. Tests enforce pinned CFG nodes/exits,
selector/table distinctions, pair-store dominance, early-zero/store mutation
rejection, unknown scratch preservation, record-read requirements, nonretention
limits, queue effects/domains and unchanged exact-vs-semantic classification.
The twelve original inputs and all old baseline objects/reports remain unchanged.

## One next increment

Audit **only the default command-3 table operation's local record/name-buffer
write coverage**, including its descriptor override gate and whether result zero
guarantees initialization of the exact fields above. This directly attacks the
remaining default-path read-before-write obligation. Runtime custom callback
selection and synchronous ownership/lifetime still need independent provenance;
do not label the current conditional contract as complete ABBC safety. Continue
functional C reconstruction separately from future CodeWarrior/toolchain and
original-unit qualification; no original module/ROM link is claimed.
