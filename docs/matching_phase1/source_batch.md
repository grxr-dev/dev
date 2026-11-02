# Phase1: six-source utility/formatting batch

**Batch/workflow delivered; no authentic match or reconstructed module claimed.**
Six existing C hypotheses now share declarations, contracts and a manifest.
No extra functions were selected to fill a quota. Original compiler family/revision,
source names/types, ABI details outside the stated domains and original object
partitions remain unqualified. Authentic matched C=0; Gate0 OPEN.

## One command

From the dev repository:

```powershell
python -B tools/matching_phase1/batch.py --publish-status
```

This validates all12 pinned inputs, builds/tests/checks six symbols, builds the
authored cluster/repeat/negative objects, runs real objdiff and 63 regressions,
then rechecks all12 input hashes. The command needs the existing qualified
Zig0.15.2/Clang20.1.2 and Capstone; it does not download anything implicitly.
The optional explicit official CLI installer is
`python -B tools/matching_phase1/install_objdiff.py` (network approval may be
required). Without that optional tool the source/byte batch still runs and clearly
reports NOT_INSTALLED, not object-diff PASS.

`--require-exact` returns1 for a completed batch with byte mismatches; ordinary
completed diagnostics return0; compilation/model/tool/integrity errors return2.
An input preflight failure replaces stale local success with BATCH_ERROR evidence.
Actual compile stdout/stderr and exceptions are retained per symbol, never hidden
behind a behavioral PASS. `--publish-status` writes metadata only to
`docs/matching_phase1/batch_status.json`; without it, output is ignored local only.

## Source and contract consolidation

Canonical bodies: `src/arm9/utility_hypotheses/func_<address>.c`.
`contracts.h` owns the shared u32 type, minimal address-labelled opaque calls and
two .bss address aliases. `cluster.c` includes the six canonical bodies into one
new authored TU. Old six Phase0 source paths are one-line compatibility includes;
old configs/runners/tests remain available with no duplicate implementations.
The shared README distinguishes verified instruction effects, safe-domain
assumptions, opaque-call scenarios and unknown original prototypes.

In particular, no `char[64]` or recovered context structure was invented. The
020DCBB4/020DCBF4 gap is not object-capacity proof. Formatting effects remain
opaque and the wrapper returns its fixed alias, not the callee's returned pointer.
The suffix predicate still requires n>=3; no null/short-input guard was added.
No native-recomp integration, linking, guest/runtime execution or relay change.

## Per-symbol results

All references are inferred main ARM9 .text symbols in ARM little-endian mode.
Sizes below include literal data. Raw bytes/disassembly remain private/local.

| Address | Reference code+pool / total | Generated code+pool / total | Behavior evidence rerun | Exact diagnostic |
|---|---:|---:|---|---|
| 020660F4 | 8+0 /8 | 8+0 /8 | Constant r0,1 check; prototype unknown | MATCH,0 differing offsets |
| 020660FC | 36+4 /40 | 32+4 /36 | 24 conditional formatter ABI/alias scenarios | MISMATCH,26 offsets |
| 0206655C | 108+4 /112 | 112+4 /116 | 24 opaque context/control scenarios | MISMATCH,101 offsets |
| 020665CC | 72+0 /72 | 56+0 /56 | 1,064 safe-domain predicate/read traces | MISMATCH,53 offsets |
| 02067F74 | 40+0 /40 | 44+0 /44 | 3,625 bounded byte-read traces plus existing induction argument | MISMATCH,34 offsets |
| 02068008 | 28+0 /28 | 28+0 /28 | Symbolic r0 bit-origin map for all2^32 words | MISMATCH,19 offsets |

Thus6/6 compile,6/6 bounded model checks pass,1/6 diagnostic byte matches,5/6
exact-byte failures. There are4,738 finite model cases plus the symbolic word
domain, NOT billions of executed CPU tests. These reuse the Phase0 small decoded
operation models, not an independently qualified emulator or original formatter.
No universal external-memory-effect/flag/scratch/timing equivalence is claimed.

Original literal words:02066120->020DCBB4 and020665C8->020DCBF4. Generated mapping
symbols place those at0206611C and020665CC respectively under the *isolated*
assumed comparison addresses. The latter collides with the original predicate
entry; the NUL counter also exceeds its original symbol extent by4bytes. These
objects CANNOT simply be placed into the original gaps or called a linked module.
The manifest and result report raw/resolved symbol hashes separately, exact
symbol sizes, ARM/code-vs-data spans, section names and explicit call relocations.
Generated ELF flags0x05000200 identify these Clang objects as EABI5 with the
soft-float ABI flag; that is not
qualification of the original title's complete ABI/compiler settings. Original
.text section alignment is32; inferred function entries are word-aligned ARM.

## Relocations and a legitimate object-diff pilot

Isolated comparisons retain the existing deliberately limited resolver: only
REL R_ARM_CALL(28), canonical ARM BL addend-8, explicitly pinned undefined symbol
and aligned in-range ARM destination. Unsupported code relocations reject; no
masking, relaxed byte equality or custom general linker was added. Original
literal-load metadata is checked against actual pinned pool words. Type42
R_ARM_PREL31 .ARM.exidx metadata is reported outside the function byte comparison.
ELF $a/$d mappings now establish generated code/data spans rather than guessing
that literal words are instructions.

Official [objdiff v3.8.3](https://github.com/encounter/objdiff/releases/tag/v3.8.3),
tag commit9aeec9cbab1a056ade7dc1f1625aacc41b0f8511, was downloaded only into
ignored `local/matching_phase1/tools/objdiff-v3.8.3/`. Windows x86_64 CLI SHA-256
`dd12dfb5e9e94a7f6c949a37e1815963cf2cffe4c87b4999b7ebc8c15b398a1f`
matches the publisher release API digest; size7,164,416; banner3.8.3. MIT/Apache
open-source upstream; no proprietary compiler, system/PATH install or independent
reproducible-source-build/signature claim. Installer also checks the exact tag
commit/asset URL/size before execution. See `objdiff_installation.json`.

The [official interface](https://github.com/encounter/objdiff#usage) compares
relocatable objects. We actually compared legitimate independently compiled
**authored** ARM ET_REL objects, not a binary wrapped into an ELF:

- A/B: same six-source cluster, unchanged baseline flags plus `-fno-inline
  -ffunction-sections`; two independent compiles byte-identical,3,308bytes,
  SHA256`c1074b4766615875d29aef2c43a247abcb4a13f48ccf8d8b09b3a2216746f0f7`.
- Both have exactly six function definitions; five explicit opaque externs;
  seven R_ARM_CALL relocations (including two defined intra-cluster calls) and
  six PREL31 exidx relocations. No link or fixed-address placement performed.
- CLI authored-repeat control reports all six at100%. This is **rebuild control
  success, NOT100% Brain Age or original-object match**.
- A separately compiled O0/no-sanitizers negative control is3,572bytes,
  SHA256`fcd03658a16b2a225680119ac00f4ce99d90013dd30678eafa2df29a1cd66dd9`.
  CLI distinguishes five nontrivial functions (0%,41.689655%,0%,0%,0%) while the
  trivial leaf stays100%. These scores are not semantic/exact-byte verdicts.
- Initial O0 control was rejected for extra Zig UBSan imports; explicit
  `-fno-sanitize=all` is confined to this negative tooling control. No external-
  symbol guard was loosened and no matching optimization sweep was performed.
- Generated local `objdiff.json` labels both units AUTHORED/NOT_ORIGINAL and
  disables automatic builds. The CLI project/unit route was also exercised with
  the authored-repeat unit; all six scores100%, exit0.

Full objects, inventories, commands, stderr and diff JSON remain under
`local/matching_phase1/runs/utility-batch/`. No original Nintendo .o was created,
uploaded or committed. No raw-binary comparison is called objdiff matching.

## Why an original-object comparison remains blocked

The pinned dsd0.12.1 `arm9/delinks.txt` contains only inferred section spans:
.text[02000000,020C1C18), alignment32, followed by other section ranges. There are
no named original object partitions. The six functions form several separated
islands, not evidence for a common original compilation unit. Dsd
[delink/objdiff support](https://github.com/AetiasHax/ds-decomp#delink) does not
authenticate a proposed split. No pinned metadata was edited or delink invoked.

Smallest useful **candidate for qualification**, not a claimed original object:
the adjacent leaf/wrapper pair[020660F4,02066124),48bytes,44 ARM code+4 literal,
one external call02019024 and one .bss target020DCBB4. Boundaries, call and pool
are pinned already. Before treating it as an expected object, establish a real
object-boundary rationale (map/symbol/section/compiler evidence), ARM mapping,
literal ownership, external symbol identities and proper relocations, alignment,
and roundtrip/relink preservation. If used sooner, it must be explicitly labelled
an inferred analysis partition, never an authentic original TU. An arbitrary split
and fabricated original .o are not prerequisites we can silently manufacture.

## Regression and integrity evidence

63 tests:37 existing Phase0 regressions +26 focused batch/tool tests;0 failures,
0 errors,0 skipped. Coverage includes manifest coverage/duplicates, code/pool
boundaries, addresses/sizes/hashes/compiler flags, explicit call/literal policy,
unsupported relocations, duplicate actual ELF definitions, malformed ELF,
compile/model/exact status separation, stale-success replacement on preflight
failure, official tool provenance and objdiff control coverage/score validation.
All12 protected inputs (ROM, extracted ARM9, ten metadata files) were independently
hash-checked before/after; synthetic mutation of each protected-input cell rejects.
`--require-exact` was also run and returned the expected1, not a misleading PASS.

## Material progress and exactly one next increment

This adds **no newly reverse-engineered symbols**: it turns six isolated pilots
into one canonical source cluster, explicit shared/opaque contracts, a reusable
manifest, per-symbol compile/model/byte ledger and tested real object tooling.
That is a scalable unit of Clang-backed functional source work, not a recovered
module. Coverage:6 hypotheses; inferred metadata:2,977 main functions +11 ITCM
records; those counts are not reconstructed source. Authentic matched C remains0.

**One next increment:** make a checked relocatable partial link of the six
separately compiled authored objects (not a ROM link), with a symbol/relocation
map resolving the two internal edges and leaving exactly five opaque externs.
Compare it against the authored single-TU cluster at symbol/section/relocation
level, preserving code/pool ownership and explicitly retaining size collisions
as fixed-address-placement blockers. This advances reproducible functional
cluster linking without pretending the current objects fit the original image.

Original CodeWarrior qualification is a separate track: lawfully provisioned
mwccarm/mwldarm, provenance/banners/hashes and representative nontrivial ABI,
section/flags evidence for the still-unknown original family/revision. No
proprietary download or compiler-version sweep was performed. Neither that
qualification nor the next partial-link increment was started in this task.
