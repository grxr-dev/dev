# Phase1: two context callees added to the actual authored link

**PASS for bounded source reconstruction and an authored eight-object -r link.**
Eight C hypotheses, not eight original-source matches. Authentic matched C=0;
Gate0 OPEN. Original compiler family/revision, original prototypes/source names
and original compilation-unit partitions remain unqualified.

## Selection and original evidence

All 12 pinned inputs were verified before inspecting bytes. The five-import
frontier was audited only at its known boundaries; no mass or recursive sweep:

| Import | Original code + pool | Decision |
|---|---:|---|
| 02019024 | 52 + 0 | Keep opaque: vararg forwarding into 02019058; formatter effects unproved |
| 0200AEE8 | 40 + 0 | Reconstruct: establishes concrete context field initialization used by the existing parent |
| 0200ABBC | 72 + 0 | Reconstruct: parent preparation protocol, two nested calls, local output consumption and boolean result |
| 0200AA5C | 12 + 4 | Keep opaque: indirect tail dispatch through literal 0200AD10, not four instructions or an ordinary BL wrapper |
| 0200AB7C | 64 + 0 | Keep opaque: conditional dispatcher 0200A464 effects remain unproved |

The selected bodies are ARM little-endian in inferred main `.text`, sizes from
checksum-pinned metadata independently compared to verified ROM/extracted ARM9.
No literal pools or data relocations occur in either selected body.
Reference hashes:

- AEE8: `4d44502d3b3c4da7dd79a515c87ba0e4a2c5519af0c804aa0abe740f5feffc7b`.
- ABBC: `43925e1d149c89bccd67fecfd80d04592da0a155617fb4bcf394fdf570dab7be`.

[context_evidence.json](context_evidence.json) contains hashes, full relocation
metadata and all 17/9 direct caller sites with inferred containing functions.
Every direct-call opcode/target was rechecked; ITCM/DTCM metadata adds no direct
sites. Indirect callers and universal input validity are not established.
The existing parent at 0206655C passes the same context alias in r0 to both;
its original input is in r1 for ABBC. The parent ignores both returns.

### AEE8 facts vs C hypothesis

Original: zero word +0; reread +0 into r2; store that word to +4; zero halfword
+0x18; zero word +8; write 14 to word +0x10; zero word +0xc; BX LR. No stack,
calls or branches; SP/LR/callee-saved registers unchanged, r0 remains the input.
Bytes +0x14..17 and +0x1a onward are not written. Minimum touched extent is
26 bytes, **not** a recovered 26-byte structure or a proof of total capacity.

`func_0200aee8.c` uses u32 word offsets and one u16 access, no named struct or SDK
identity. Supported storage is ordinary, aligned, writable and nonconcurrent;
the required typed accesses must be valid. Clang may eliminate the reread and
reorder independent writes. Thus final bytes, touched widths and preserved state
are checked, not volatile/MMIO/access-order equivalence. `void` is the retained
used-argument hypothesis; r0 retention is also checked at generated-code level.

### ABBC facts vs C hypothesis

Original saves r4/LR, reserves 8 bytes (16-byte total frame), retains context in
r4 and calls 0200ACD0(SP,input) at 0200ABCC. Zero returns 0 without reading the
scratch pair. Nonzero loads the two words into r1/r2 and calls
0200AC04(context,word0,word1) at 0200ABE4; its nonzero result becomes 1, else 0.
All paths restore SP/r4 and return through saved LR; caller-clobbered registers,
NZCV, exact LR scratch value and timing are not a C equivalence claim.

The actual ACD0 boundary is 64 bytes, AC04 is 124. Their inspected bodies support
the used r0/r1 and r0/r1/r2 arguments respectively, without requiring incoming
r2/r3 for ACD0 or incoming r3 for AC04. Their deeper calls, global effects,
resource/error contracts and pair initialization are **not** reconstructed.
`func_0200abbc.c` therefore keeps both external. Its conditional scenario contract
requires ACD0 to initialize both output words on nonzero return, normal ABI
preservation, disjoint context/frame and no escaped frame pointer. Failure need
not initialize the pair. No host pointer addresses are dereferenced in tests.

## Repeatable checks and link

```powershell
python -B tools/matching_phase1/context_evidence.py --publish
python -B tools/matching_phase1/batch.py --publish-status
python -B tools/matching_phase1/partial_link.py --publish-status
```

New minimal comparison configs inherit the manifest's checksum-verified input
and tool profile; the six Phase0 configs/wrappers remain intact. Eight independent
`leaf.o` inputs are built, not the separately authored unity object. The unchanged
Zig 0.15.2 / Clang and LLD 20.1.2 executable and retained -r flags are documented
in [partial_link.md](partial_link.md). No new relocation kind or masking was added:
only canonical ARM CALL(28) and exidx PREL31(42) are accepted.

The runner explicitly refuses the #122 output directory. It requires that
preserved local baseline object to be present with its pinned hash; it never
regenerates it silently. All six new input object hashes AND all six raw function
bodies agree with #122. Baseline output SHA-256 remains
`36acd51ab2f5d1f14490e5ad3b5e660e24a054efe794216757c0b2d66ad4de4c`.

Exactly one new LLD -r invocation, exit 0, no warnings/errors, into distinct
`local/matching_phase1/runs/partial-link-context-v1/linked-authored.o`:
2,348 bytes, SHA-256
`e4672ae07e9a15b76d3f974123327bbef33c9ac74b07fb200e66200927426613`.
Reruns re-audit/reuse the validated artifact, never silently relink changed inputs.
Full output/inputs/map identity and inventory:
[cluster_expansion_status.json](cluster_expansion_status.json).

ELF32 LE ARM ET_REL, EABI5 soft-float/base PCS, CPU arm946e-s/v5TE; all function
entries `$a` ARM, zero section virtual addresses/no program headers.
`.text`: offset 0x34, 388 bytes, alignment 4. `.ARM.exidx`: offset 0x1b8,
64 bytes, alignment 4. No allocated data/bss or named static data definitions.
Old `$d` pools remain at .text+0x28 and +0x9c; new bodies have no pools.
Weak/common/duplicate/COMDAT definitions and unsupported relocation kinds reject.

| Defined STT_FUNC | .text offset | Reference / generated size | Original byte verdict |
|---|---:|---:|---|
| func_020660f4 | 0x000 | 8 / 8 | MATCH, trivial Clang only |
| func_020660fc | 0x008 | 40 / 36 | MISMATCH |
| func_0206655c | 0x02c | 112 / 116 | MISMATCH |
| func_020665cc | 0x0a0 | 72 / 56 | MISMATCH |
| func_02067f74 | 0x0d8 | 40 / 44 | MISMATCH |
| func_02068008 | 0x104 | 28 / 28 | MISMATCH |
| func_0200aee8 | 0x120 | 40 / 36 | MISMATCH, 28 differing offsets |
| func_0200abbc | 0x144 | 72 / 64 | MISMATCH, 40 differing offsets |

## Dependency graph and relocation ownership

Before: six definitions, seven CALL relocations, two internal call edges;
imports {019024,00AEE8,00ABBC,00AA5C,00AB7C}.
After: eight definitions, nine CALL relocations, four internal call edges;
imports {019024,00AA5C,00AB7C,00ACD0,00AC04} (all prefixed `func_02`).
**Two previous imports became defined; total unresolved count remains five.**
No opaque bodies were fabricated to force that number down.

All old seven CALL offsets/targets are retained. Parent calls to AEE8/ABBC now
reference definitions. New ABBC CALLs at local +16/.text+340 and +44/.text+368
target ACD0 and AC04 respectively. All nine retain raw implicit addend -8,
normalized entry addend 0. Eight PREL31 exidx entries at offsets 0..56 by 8
reference .text with addends 0,8,44,160,216,260,288,324; CANTUNWIND retained.
No final relocation/absolute placement is claimed. All eight raw input/output
function bodies are equal, not equal to original code; original comparison
continues to resolve only pinned isolated calls without rebasing away mismatches.

## Tests and limits

8/8 compile and bounded models PASS. **110 regressions PASS**, zero errors,
failures or skips: all prior 90 retained/adapted for manifest coverage plus 20
new callee tests. AEE8: 512 ordinary-memory scenarios, canaries/halfword extent,
alignment/short-buffer failures, original reread vs optimized elimination.
ABBC: 320 opaque pair scenarios covering both zero paths, high-bit nonzero
returns, forwarding, frame/callee-saved preservation and no uninitialized reads
on failure; missing successful outputs, wrong calls/arguments/returns reject.
Config/profile/hash/range, dependency graph, unchanged six bodies and byte-vs-
behavior separation are also checked. These are bounded decoded-operation
models, not an independent ARM emulator or proof of nested API effects.

All 12 original inputs remain hash-identical; baseline object/status preserved;
unrelated working files left untouched. No guest/host C execution, final link,
ROM patch, proprietary download, relay change or Nintendo asset committed.

**One next increment:** reconstruct/qualify 0200AC04's context-consumption and
flag-update contract while retaining its 0200A464 dispatcher as opaque. This
would connect the newly explicit pair protocol to verified context fields,
rather than adding unrelated easy leaves. Original object partition recovery
and original CodeWarrior qualification remain separate evidence tracks; this
authored cluster is not an original compilation unit or module.
