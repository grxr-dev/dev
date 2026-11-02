# Phase1: authored six-object relocatable partial link

**PASS for an authored-cluster object only.** No original compilation-unit,
original-object objdiff, original module, ROM rebuild or runtime-parity claim.
Original-toolchain verified matched C remains **0; Gate0 OPEN**.

## Preservation before experimentation

The uncommitted #121 work was present. Before linker investigation, the batch
and all 63 then-existing regressions passed, and only its 24 source/header,
manifest/runner/test/documentation and necessary Phase0 include-wrapper files
were committed as `234671ea4194fe37283b4fa9ec38c0a96a1fd494` and pushed to
`origin/codex/brainage`. Remote branch readback confirmed that SHA and both
`source_batch.md` and `batch_status.json`. Unrelated untracked work was not staged.

## Commands and qualified tool

From the repository root:

```powershell
python -B tools/matching_phase1/batch.py --publish-status
python -B tools/matching_phase1/partial_link.py --publish-status
```

The first command creates **six independent** `leaf.o` inputs, one per canonical
source. Its separately compiled unity `cluster.c` object is NOT a link input.
The second command validates those input identities and performs one real link
when its dedicated output directory is new. A validated unchanged artifact is
re-audited on rerun without invoking the linker. Changed input/tool identity,
changed output, existing unexplained artifacts, failed or interrupted attempts
stop with an explicit error; there is no automatic retry or overwrite fallback.
Use `--output` only for an intentional separately reviewed experiment below
ignored `local/matching_phase1/runs/`, not to bypass an error.

No download was necessary. The already checksum-verified Zig 0.15.2 executable
contains Clang/LLD 20.1.2. Its SHA-256 is
`d408dd38eed3e5204af841bcebf70502a4dbbb8399a3a3262be55059370bc018`.
The actual `zig ld.lld --version` banner is:

```text
LLD 20.1.2 (https://github.com/ziglang/zig-bootstrap 7ef74e656cf8ddbd6bf891a8475892aa1afa6891) (compatible with GNU linkers)
```

Exact argument structure (the six paths follow manifest order):

```text
zig.exe ld.lld -r -m armelf --build-id=none --no-gc-sections --icf=none
  --no-merge-exidx-entries --no-allow-multiple-definition
  --Map=<output>/linked-authored.map -o <output>/linked-authored.o
  <utility-batch>/func_020660f4/leaf.o <utility-batch>/func_020660fc/leaf.o
  <utility-batch>/func_0206655c/leaf.o <utility-batch>/func_020665cc/leaf.o
  <utility-batch>/func_02067f74/leaf.o <utility-batch>/func_02068008/leaf.o
```

Exactly **one actual -r invocation**, exit 0, empty stderr; subsequent audit reuse
reported **0** new invocations and the same output hash. Version/help/Clang
`-###` qualification did not create linked objects. No final link was attempted.

## Actual object inventory

`local/matching_phase1/runs/partial-link/linked-authored.o`: 2,036 bytes;
SHA-256 `36acd51ab2f5d1f14490e5ad3b5e660e24a054efe794216757c0b2d66ad4de4c`.
ELF32 little-endian ARM **ET_REL**, entry 0, no program headers, zero section
virtual addresses, flags `0x05000200` (EABI5/soft-float). All input/output AEABI
attribute values agree: CPU `arm946e-s`, architecture ARMv5TE, base PCS, not VFP
register arguments. CPU Thumb1 capability is recorded, but actual function
entries and instruction mappings are **ARM**, never Thumb.

| Global STT_FUNC | .text offset | Size | Original isolated byte diagnostic |
|---|---:|---:|---|
| func_020660f4 | 0x000 | 8 | MATCH (trivial Clang leaf only) |
| func_020660fc | 0x008 | 36 | MISMATCH |
| func_0206655c | 0x02c | 116 | MISMATCH |
| func_020665cc | 0x0a0 | 56 | MISMATCH |
| func_02067f74 | 0x0d8 | 44 | MISMATCH |
| func_02068008 | 0x104 | 28 | MISMATCH |

Six unique, global function definitions; no common/weak/hidden/GNU-unique
definitions, COMDAT groups, ICF or duplicate-definition acceptance. `.text` is
288 bytes, alignment 4, file offset 0x34. `.ARM.exidx` is 48 bytes, alignment 4,
file offset 0x154. Remaining sections/offsets/flags/alignments are fully listed
in [partial_link_status.json](partial_link_status.json).

Literal ownership is retained: wrapper local +32 (`.text+0x28`) contains the
address alias 0x020DCBB4; parent local +112 (`.text+0x9c`) contains 0x020DCBF4.
Both are four-byte `$d` pools, not instructions. **No .bss/.data storage or named
STT_OBJECT/static global is allocated.** Shared header macros are address aliases,
not definitions or evidence of original global extent. No ABI body was invented
for an opaque import.

Exactly five unresolved symbols remain:
`func_02019024`, `func_0200aee8`, `func_0200abbc`, `func_0200aa5c`, `func_0200ab7c`.

Seven retained `.rel.text` **R_ARM_CALL (28)** REL relocations:

| Owner | Local offset | .text offset | Target | Definition present |
|---|---:|---:|---|---|
| func_020660fc | 20 | 28 | func_02019024 | no |
| func_0206655c | 20 | 64 | func_0200aee8 | no |
| func_0206655c | 32 | 76 | func_0200abbc | no |
| func_0206655c | 48 | 92 | func_020665cc | yes |
| func_0206655c | 72 | 116 | func_0200aa5c | no |
| func_0206655c | 96 | 140 | func_0200ab7c | no |
| func_020665cc | 8 | 168 | func_02067f74 | yes |

Each call has raw implicit addend -8 / normalized function-entry addend 0.
The two internal definitions bind in the output symbol table; their relocations
are deliberately retained, not final executable branch placement.
Six `.rel.ARM.exidx` **R_ARM_PREL31 (42)** entries at offsets 0,8,16,24,32,40
reference `.text` through its unnamed section symbol with adjusted implicit
addends 0,8,44,160,216,260. Each second word is 1 (CANTUNWIND).
These are linker-generated section-relative metadata updates, not ROM code.

All six raw function bodies are byte-identical to their own compiler input
bodies; code/pool mappings and call ownership match. This equality is **not**
against original bytes. The existing isolated ROM-placement comparison remains
independent: one trivial MATCH, five MISMATCH; offsets in this object cannot
promote mismatches to matches.

## Tests, integrity and local evidence

- Full batch: 6/6 compile, 6/6 bounded behavioral-model checks; 90 regressions,
  zero failures/errors/skips (63 preserved + 27 partial-link tests).
- Focused tests: `python -B -m unittest discover -s tools/matching_phase1 -p test_partial_link.py -v`.
  They use actual authored input ELF plus in-memory malformed/expected-state
  fixtures, never fabricate an original/linked .o. Coverage includes missing or
  unexpected undefineds, duplicate/unity input, wrong CPU/EABI/Thumb/COMDAT/weak
  policy, call kind/target/addend/binding, pool/code drift, exidx order/coverage,
  function offsets/sizes/layout, section extents and unchanged original verdicts.
- Real linked-output success is separately audited by `partial_link.py`; unit
  fixture acceptance is not substituted for that actual link evidence.
- All 12 protected inputs (ROM, extracted ARM9, ten metadata files) hash-identical
  before/after; all six input object hashes unchanged. No guest execution,
  uncontrolled/final link, ROM mutation, BIOS or relay/VM change.
- Only metadata/source/docs are committed. Objects, map, per-invocation argv,
  attempt marker and local reused audit remain in ignored
  `local/matching_phase1/runs/partial-link/`. Public status records the initial
  one-invocation success; local latest status records reuse without relinking.

This is a repeatable **authored-cluster object proof**, not recovery of any
authentic original object partition or module. Functional Clang reconstruction
can next qualify one opaque import's contract/body and extend this checked link;
original CodeWarrior family/revision qualification and evidence-backed original
compilation-unit delinking remain separate future work, not done here.
