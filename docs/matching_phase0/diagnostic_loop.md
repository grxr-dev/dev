# Working one-leaf compile/compare diagnostic

**PASS for the compiler-agnostic instruction diagnostic. Gate0 remains OPEN.
Original-toolchain verified matched C remains 0.** This supersedes #104's lack of
an executable compiler loop, not its original-toolchain uncertainty.

The authored hypothesis is `int func_020660f4(void) { return 0; }`. Neither the
original prototype, signedness, name/role nor original compiler is recovered.
The existing dsd boundary, ARM mode, 8-byte reference hash and 21 incoming calls
were revalidated. No other game function was compiled or analyzed in this task.

## What actually ran

Installed the official Zig **0.15.2 Windows x86_64** portable release, including
its LLVM-backed **Clang 20.1.2** C compiler and integrated assembler. No SDK,
proprietary compiler, system PATH/registry change or linker invocation was needed.
The included LICENSE remains with the ignored local installation.

- Official archive: <https://ziglang.org/download/0.15.2/zig-x86_64-windows-0.15.2.zip>
- Publisher index checked: <https://ziglang.org/download/index.json>
- Archive: 92,614,574 bytes, SHA-256
  `3a0ed1e8799a2f8ce2a6e6290a9ff22e6906f8227865911fb7ddedc3cc14cb0c`.
- Executable SHA-256:
  `d408dd38eed3e5204af841bcebf70502a4dbbb8399a3a3262be55059370bc018`.
- Local executable:
  `local/matching_phase0/toolchains/zig-x86_64-windows-0.15.2/zig.exe`.
- Actual banner: `clang version 20.1.2`, zig-bootstrap commit
  `7ef74e656cf8ddbd6bf891a8475892aa1afa6891`.

The full-file transfer stalled. Exact checked HTTP ranges assembled the official
archive; the whole publisher digest was verified before execution. A resumable
bootstrap now reproduces that installation. TLS/publisher checksum provenance is
established; independent source rebuild/minisign verification is not claimed.
`zig targets` emits ZON in this release, not JSON; ARM946 spelling was confirmed
from the shipped `lib/std/Target/arm.zig`: `arm946e_s` maps to LLVM `arm946e-s`.

The successful invocation, from the repository root with equivalent relative
paths (the actual absolute argv is in `diagnostic_loop.json`), was:

```powershell
& local/matching_phase0/toolchains/zig-x86_64-windows-0.15.2/zig.exe cc `
  -target arm-freestanding-eabi -mcpu=arm946e_s -marm -O2 `
  -ffreestanding -fno-builtin -fno-stack-protector `
  -fno-unwind-tables -fno-asynchronous-unwind-tables -g0 `
  -fomit-frame-pointer -c tools/matching_phase0/leaf_pilot.c `
  -o local/matching_phase0/leaf-diagnostic/leaf.o
```

Four real C compiler invocations, all compiler exit 0:

| Run | Result | Function bytes | Compare |
|---|---|---|---|
| Initial flags, default frame pointer | 16-byte framed leaf | `00482de90db0a0e10000a0e30088bde8` | FAIL; 14 differing/extra bytes |
| Add only `-fomit-frame-pointer` | 8-byte leaf | `0000a0e31eff2fe1` | PASS; 0 differences |
| Ignored negative fixture, `return 1` | 8-byte wrong value | `0100a0e31eff2fe1` | FAIL; 1 differing byte; process exit 1 |
| Repeat committed `return 0` | Same 8-byte leaf | `0000a0e31eff2fe1` | PASS; process exit 0 |

The initial driver's `-###` output explicitly showed `-mframe-pointer=all`;
omitting the frame was one evidence-based adjustment, not a version/flag sweep.
The successful compile took about 0.142 seconds; the repeat about 0.144 seconds.
Both emitted objects have SHA-256
`e4e0cfb8b288a342f01e69a18588d8e90d0f16862841ca947eaf8669608651bd`.

## Exact comparison boundary

ELF32 little-endian ARM, ET_REL; flags `0x05000200`. The defined STT_FUNC symbol
is at `.text` offset 0, size 8, object file offset `0x34`. The object contains the
`arm946e-s` CPU attribute. It is **not linked at 0x020660F4**: that address is used
only to select the verified ROM reference and annotate disassembly.

Capstone 5.0.7 decoded the compiler output in ARM mode:

```
0x020660F4: mov r0, #0
0x020660F8: bx lr
```

Function-code relocations: **0**. One separate `.rel.ARM.exidx` metadata relocation
(type 42) exists outside the compared function. Neither the extra ELF sections,
headers, unwind metadata nor padding are mistaken for function bytes. Exact
symbol length plus every byte is compared; no search for a matching subsequence.
The ELF extractor refuses unresolved function-code relocations and Thumb input.

Original reference SHA-256:
`6dcd5e75586fe6683156c0d559d4827b73bd48d501fa5781a1c6099aacd7c877`.
This trivial instruction match does not establish original compiler identity,
ABI/optimization settings, source provenance, object boundaries or linking.

## Repeat it

From `C:\Users\rustg\Documents\Codex\Muse\dev`:

```powershell
python -B tools/matching_phase0/bootstrap_zig.py
python -B -m unittest discover -s tools/matching_phase0 -p test_diagnostic.py -q
python -B tools/matching_phase0/diagnostic.py
```

The existing verified ROM/extract and `init-002` metadata are prerequisites;
the script does not recreate or alter them. Existing Capstone 5.0.7 is used.
`diagnostic_config.json` pins tool hash/version, target, flags, leaf and ROM hashes.
`--source path/to/candidate.c --output local/...` runs another C hypothesis for
this same symbol/reference. A mismatch returns 1; precondition/ELF rejection is
an error. All generated objects, disassembly, extracted bytes, compiler logs and
full reports stay under ignored `local/matching_phase0/leaf-diagnostic/`.

Seven ROM-free synthetic ELF/comparator tests passed: exact symbol boundaries,
wrong machine, Thumb, bounds, code relocations, changed/extra bytes and malformed
or missing symbols. The real negative compile independently proves the runner
returns FAIL for changed code. No objdiff-cli was installed/run; this narrow
stdlib comparator is sufficient only because the function has no code relocations.

All four runs preserved the same 12 input files: ROM, extracted ARM9 and all ten
metadata files. The metadata also matches the *prior* `metadata_init.json` hashes.
Original ROM SHA-1 remains `b8a105bacc3234dede8d4465df0869f2b922a0e2`;
SHA-256 remains `ac83193346fdca6ea449a6cb60bbe44d327eeb66f2d619d9b1bf8f73600faf5e`.
No BIOS read, ROM rebuild, runtime execution, relay edit or generated-ROM-C edit.
Prior uncommitted Phase0 evidence/scripts were reused and left untouched.

## Matching-toolchain qualification still needed

[ds-decomp](https://github.com/AetiasHax/ds-decomp) supports delinking, objdiff
configuration, mwldarm LCF generation and module checks. The installed version
remains pinned 0.12.1 / `73934550322c80b634106ad7883bbe4671f24b99`; availability of
its LCF writer is not evidence of Brain Age's original compiler.
[objdiff](https://github.com/encounter/objdiff/blob/main/README.md) compares
relocatable objects and supports ARM; it becomes valuable once original target
objects/relocations and a real build are available. It is not necessary to test
these eight relocation-free instructions.

As a current real-DS example, pret/pokeheartgold at
`e1d5a4606640e31c44d36714ad0b5cdd9c8763fd` uses
[2.0/sp2p2 for its main CodeWarrior wrapper](https://github.com/pret/pokeheartgold/blob/e1d5a4606640e31c44d36714ad0b5cdd9c8763fd/meson/cross.ini)
and [different revisions for SDK/library components](https://github.com/pret/pokeheartgold/blob/e1d5a4606640e31c44d36714ad0b5cdd9c8763fd/meson.build).
This demonstrates revision/component qualification matters; it supplies **no
Brain Age revision or flag evidence**. No binaries from that project were obtained.

No mwccarm/mwldarm was found in the previous bounded searches or current PATH/
Visual Studio LLVM checks; machine-wide absence is not claimed. Candidate family
is CodeWarrior ARM/NitroSDK, but Brain Age's actual family/revision remains
unproven. Exact revision, patches, headers/libraries, ABI, optimization and linker
settings must be established from nontrivial game evidence and lawful local tools.

Minimal lawful qualification path:

1. Keep an owner-legitimately-obtained installation under ignored
   `local/matching_phase0/toolchains/codewarrior/<family-revision>/`, with
   `mwccarm.exe`, compatible `mwldarm.exe`, manuals/release notes and a local
   provenance/license record. Do not download community proprietary archives.
2. Hash both executables and docs, read the supplied manual, run its documented
   version/help commands into a local log, and record exact banners/options.
   Do not invent one universal MW version command or infer release from this leaf.
3. Using documented ARM946/ARM-state/interworking options as explicit hypotheses,
   compile this same C leaf and inspect the symbol/relocations. Then qualify one
   nontrivial function before selecting a compiler revision. A leaf match alone
   cannot qualify it. Only afterward attempt compatible LCF/module linking and
   dsd module comparison; packaging/ARM7 obligations remain separate.

Next substantive compiler-independent step: classify how the 21 known callers
use this return value and determine whether its prototype/role can be constrained;
then select **one** nontrivial, bounded leaf for a discriminating compile pilot.
Do not expand this trivial diagnostic into an authentic matched-C count.
