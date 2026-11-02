# Phase1: connected context/pair protocol expansion

**PASS: two additional C hypotheses and a real ten-object authored partial link.**
Authentic original-toolchain matched C remains **0; Gate0 OPEN**. This is not an
original compilation unit/module, original-object objdiff or executable rebuild.

## Verified original facts and chosen scope

The 12 pinned inputs were verified before decoding the two selected ranges:

| Symbol | Inferred main .text / ARM LE extent | Reference SHA-256 |
|---|---|---|
| 0200AC04 | [0200AC04,0200AC80), 124 code bytes, no pool | `47cf08e752daa201b3ffc4419e63659b130118c9d4ebb7eeb41101901430c851` |
| 0200ACD0 | [0200ACD0,0200AD10), 64 code bytes, no pool | `92bbee4f88a2abd1d62110b6c7b61359063e6c8bf5e127479837ec7af6bf3e63` |

Both are directly connected to existing ABBC's two-word protocol, not unrelated
leaves chosen to reach ten. All instructions/conditional returns, bounds,
outgoing relocations and direct callers were independently rechecked against
actual ROM/extracted ARM9 and pinned metadata. Neither has a data relocation,
literal load or indirect call; BX/POP returns are the only indirect control.
Each has two verified direct callers (ABBC and a second main function); no
ITCM/DTCM direct references were found. Details and hashes, not code snapshots:
[context_protocol_evidence.json](context_protocol_evidence.json).

### AC04: pair consumption and post-dispatch flags

Original entry spills r0-r3 (16 bytes), saves r4/LR (8), retains context in r4,
and tests the first raw pair word. Zero restores the frame and returns 0,
without dereferencing context or calling the dispatcher. On nonzero:

1. Store first at context +8, first at +0x2c, second at +0x30 (all u32).
2. At 0200AC40 call opaque 0200A464 with observed registers
   `(context, 6, second, first)` in r0-r3.
3. Zero dispatcher result returns 0: earlier stores and dispatcher effects are
   **not rolled back**. Nonzero reads the **post-call** word at +0xc, sets bit
   0x10, stores, rereads, clears bit 0x20, stores, returns 1.

All three returns restore SP/r4 and return through saved LR. Original NZCV is
from the relevant CMP(value,0): Z reflects zero, N its sign, C=1,V=0. Logical
operations do not set flags. Generated-code NZCV is checked for this compiler;
the C interface does not promise flags, scratch registers, LR scratch or timing.

`func_0200ac04.c` uses existing raw u32 offsets, not invented SDK field names or
a recovered struct. Context need not be valid on first=0; otherwise its typed
ordinary aligned accesses and opaque dispatch contract must be valid. At least
52 bytes are touched by direct stores; that is not total object-size proof.
Clang reorders independent stores and merges the two flag updates into one
read/write; volatile/MMIO/concurrent-memory equivalence is outside the domain.

Dispatcher boundary 0200A464 is 384 bytes. Only its bounded entry window and
inferred boundary/hash were inspected, not its complete state machine. Its
initial context accesses confirm it is not a pure function. The four-argument
declaration preserves **observed registers**, not proof all four are consumed
arguments or any particular API identity. No dispatcher implementation or
resource/error behavior was fabricated. Scenario mutations used in tests are
explicit permitted opaque effects, not assertions of what it actually does.

### ACD0: partial scratch initialization, not pair synthesis

Original saves r4/r5/LR, reserves 0x44 bytes (68), retains output pointer and
input, calls AEE8(scratch) at 0200ACE4, then calls opaque AD94 at 0200ACF8 with
`(scratch,input,output_pair,0)`. It normalizes that call's zero/nonzero result
and restores its total 80-byte frame. No direct pair reads/writes, cleanup,
extra validation or whole-frame zeroing occur in this body.

`func_0200acd0.c` reserves 17 u32 words solely to represent that 68-byte aligned
reservation, **not** an original type/array declaration. AEE8 initializes only
22 bytes at verified word/halfword offsets. The other 46 bytes stay unknown;
tests reject any opaque read of an uninitialized word, including a u32 read at
+0x18 where only the low half was initialized. Clang's total frame is 88 bytes
with scratch at SP+4, not the original 80-byte frame: stack restoration and
pointer/lifetime protocol are checked, not byte-exact stack layout.

AD94 is a 340-byte opaque routine; its entry reads input[0] and saves all four
observed arguments. Input/output/scratch must meet its unknown wider contract;
no universal string length/termination or resource rule is inferred. Output
initialization on successful AD94 is **still unproved**. The forwarder can
return 1 without itself writing the pair; ABBC's two-initialized-words
assumption remains an obligation at this opaque frontier. Failure-side output
mutations are retained, not erased. No stack pointer may escape its lifetime.

## Same workflow, data-driven link identity/baselines

```powershell
python -B tools/matching_phase1/context_evidence.py --group protocol --publish
python -B tools/matching_phase1/batch.py --publish-status
python -B tools/matching_phase1/partial_link.py --publish-status
```

No duplicate pilot framework was introduced. New symbols reuse the minimal
comparison configs, existing diagnostic/resolver, context trace checker,
object auditor and batch regression discovery. The reference-audit script now
selects an explicit bounded group; the link output/status and immutable baseline
chain are manifest data instead of task-specific runner clones. Actual parser
call whitelists derive from the validated manifest; unsupported kinds still
reject. Coverage bound is ten, not an unbounded scan.

The checksum-qualified Zig 0.15.2 / Clang and LLD 20.1.2 profile is unchanged.
Exactly one new LLD `-r -m armelf` invocation used the same retention/no-COMDAT/
no-duplicate/ICF-disabled flags as #122/#123; no final link. Output:
`local/matching_phase1/runs/partial-link-context-protocol-v1/linked-authored.o`,
2,704 bytes, SHA-256
`2ef77b6890261cab00cb5469ab3a9e3ee7b92f9248e37d74603f6b6e5dffe251`.
See [context_protocol_expansion_status.json](context_protocol_expansion_status.json)
for tool/hash/flags, every symbol, section, call/addend, exidx and map identity.

ELF32 LE ARM ET_REL/EABI5 soft-float/base PCS, arm946e-s/ARMv5TE, ARM `$a`
entries; `.text` 528 bytes at file 0x34, `.ARM.exidx` 80 bytes at file 0x244,
both alignment 4. No allocated .data/.bss/named static objects; old `$d` pools
remain at .text+0x28/+0x9c, no new pools. All ten STT_FUNC definitions unique.
New AC04 is .text+0x184, 76 bytes; ACD0 .text+0x1d0, 64 bytes.

Graph: **8 -> 10 definitions, 9 -> 12 CALLs, 4 -> 7 internal edges**.
ABBC's ACD0/AC04 imports become internal; ACD0->AEE8 is an additional internal
edge. New opaque imports are A464 and AD94. Five imports remain:
`func_02019024`, `func_0200aa5c`, `func_0200ab7c`, `func_0200a464`, `func_0200ad94`.
New generated CALLs: AC04 local +40/.text+428 -> A464; ACD0 local +24/.text+488
-> AEE8 and +44/.text+508 -> AD94. All twelve use REL R_ARM_CALL(28), raw
implicit addend -8 / normalized entry addend 0. Ten PREL31(42) exidx entries
retain CANTUNWIND, ordered addends 0,8,44,160,216,260,288,324,388,464.
No new relocation kind, relocation masking or inline assembly was needed.

Both prior linked objects and public JSON reports are immutable: hashes remain
`36acd51a...ad4de4c` (#122) and `e4672ae0...7426613` (#123), full pins in the
manifest. Report identities use LF-normalized text; object hashes are raw bytes.
Every old eight independent .o hash, raw function body and byte verdict agrees
with #123. Both baseline directories/status destinations reject overwrites.
Validated reruns reuse/re-audit the new artifact; failures never silently relink.

## Tests, integrity, exact-vs-functional status

**135 regressions PASS**, zero failures/errors/skips (prior 110 plus 25 protocol
tests). All ten independent compile and bounded-model checks PASS. AC04 has
1,536 explicit pair/result/flag/mutation/alignment scenarios; ACD0 48 result/
output/alignment scenarios. Tests cover all conditional paths, pre/post call
fields and arguments, failure mutations, NZCV observations, partial scratch,
uninitialized/out-of-bounds/unaligned access rejection, wrong command/mode/call,
saved registers/SP/returns, original-vs-generated frame sizes, exact baseline
chain/object identities, protected publication and manifest call whitelists.
These are small decoded-operation models, not an independent ARM emulator or
proof of opaque dispatcher/producer semantics. No host C pointers are executed.

New original/generated extents: AC04 **124/76**, byte MISMATCH (115 differing
offsets); ACD0 **64/64**, byte MISMATCH (36 differing offsets). Overall **one
trivial Clang MATCH / nine MISMATCH**. Model success is never authentic match.
All 12 pinned ROM/extract/metadata inputs unchanged. No guest execution, BIOS,
ROM patch/rebuild, proprietary retrieval, relay edits or binary/asset commits;
unrelated local work remains untouched.

**One next milestone:** establish AD94's successful pair-write/failure/lifetime
contract with a bounded branch-complete audit before claiming ABBC's output
initialization obligation is discharged. That is the meaningful next frontier
for this connected Clang functional cluster. Original compilation-unit partitions
and authentic CodeWarrior family/version qualification remain separate unknowns;
neither this link nor source coverage settles them.
