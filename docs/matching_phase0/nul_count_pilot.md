# Phase0: bounded NUL-counter pilot at 0x02067F74

Completed: grounded C hypothesis and bounded behavioral verification PASS;
exact machine-byte comparison FAIL. **Gate0 OPEN; original-toolchain verified
matched C = 0.** No original library name, prototype or compiler is identified.

## Original evidence and behavior

The exact USA Rev1 ROM SHA-1 is
`b8a105bacc3234dede8d4465df0869f2b922a0e2`. The complete 863136-byte extracted
ARM9 main prefix equals the corresponding verified ROM bytes. All ten existing
dsd metadata files were checked against their prior initialization hashes and
are pinned in `tools/matching_phase0/nul_count_config.json`.

The inferred ARM function occupies `[02067F74,02067F9C)`: 40 bytes, ten
four-byte instructions, ending at BX LR immediately before the next inferred
function. Capstone 5.0.7 independently decodes the entire range. Its code SHA-256
is `aee45ae4f2bea37dacef15619a7d0eb553c418fc87fa032692e8c39fb9cba274`.
No outgoing relocation is recorded. The full original bytes and decode remain
in ignored `local/matching_phase0/nul-count-pilot/result.json`.

| PC | Observed instruction effect |
|---|---|
| 02067F74 | Signed byte load into r1 from r0; postincrement r0 by one |
| 02067F78 | Set r2 to zero |
| 02067F7C | Compare r1 with zero |
| 02067F80 | If zero, branch to 02067F94 |
| 02067F84 | Signed byte load into r1 from r0; postincrement r0 by one |
| 02067F88 | Increment r2 without changing flags |
| 02067F8C | Compare r1 with zero |
| 02067F90 | If nonzero, branch back to 02067F84 |
| 02067F94 | Copy r2 into return register r0 |
| 02067F98 | Return through LR |

For first NUL at offset **n**, the return is **n**, excluding the terminator.
There are exactly **n+1 single-byte reads**, at offsets 0 through n, and no
memory writes, stack accesses or calls. Empty input reads one zero and returns
zero. LDRSB sign extension does not affect equality with zero, even for 80–FF.
Byte accesses require no word alignment. The working r0 pointer advances to
p+n+1 before r0 is overwritten with the count; no caller pointer storage is
updated. Original exit scratch state is r1=0, r2=n, NZCV=0/1/1/0;
r3–r12, SP and LR are unchanged. Timing and scratch-register identity with C
codegen are not part of the equivalence claim.

## Limited caller evidence

All three inferred main/ITCM/DTCM relocation tables contain just one recorded
direct call: `020665D4`, within `020665CC..02066614`. The caller saves incoming
r0 in r4, calls the helper, and uses the returned count to address p[n-3],
p[n-2], p[n-1], comparing those bytes with 63, 6D, 70 respectively. This
supports a byte-pointer/count convention; it does not establish an original
string-library identity or signed/unsigned original return type. Indirect and
other title-module callers are not ruled out.

No n>=3 guard exists in this bounded caller body. Its suffix reads therefore
need an additional length precondition for safety. This pilot neither executes
the caller with short strings nor assumes its upstream caller guarantees that
condition. The helper itself safely handles empty input under its own contract.

## C hypothesis and preconditions

`tools/matching_phase0/nul_count.c` uses an unsigned-byte pointer, a zero
counter, one preload, then a load/increment loop while the loaded byte is
nonzero. The exported address-derived name is a diagnostic label. Pointer const
qualification and unsigned return type are hypotheses consistent with the
observed accesses, not recovered source declarations.

Required domain: p is nonnull and points into a stable readable allocated byte
object; its first zero is reachable within that object; advancing through
p+n+1 is valid, possibly one-past; no address wrap occurs; n fits 32-bit unsigned
int. Device/volatile memory, concurrent modification, invalid pointers and
unterminated objects are excluded. The C expression advances one-past only
after loading the last valid byte. No out-of-object C dereference is needed.

Static loop argument for the original: if p[0]=0, return zero immediately.
Otherwise at loop entry k>=1, the working pointer is p+k, r2=k-1, and preceding
bytes 0..k-1 are nonzero. The loop reads byte k, advances the pointer, and makes
r2=k. A zero returns k; a nonzero establishes the next iteration's invariant.
Thus it stops at exactly the first zero and cannot overread under the contract.
This also describes the authored C's preload/do-loop. It is an induction
argument over decoded ARM semantics, not a mechanically certified ARM proof.

## Actual compilation and exact comparison

One C hypothesis and one flag set were used. The identical invocation ran twice:
initial compile/decode, then the completed reproducible runner. No variant or
flag search was performed. Both compilations exited zero with empty stderr.

Compiler: official local Zig 0.15.2 / Clang 20.1.2; executable SHA-256
`d408dd38eed3e5204af841bcebf70502a4dbbb8399a3a3262be55059370bc018`.
The exact executable, version/banner, source hash and invocation are recorded
in the companion JSON and local result. Invocation, from the repository root:

```text
local/matching_phase0/toolchains/zig-x86_64-windows-0.15.2/zig.exe cc -target arm-freestanding-eabi -mcpu=arm946e_s -marm -O2 -ffreestanding -fno-builtin -fno-stack-protector -fno-unwind-tables -fno-asynchronous-unwind-tables -g0 -fomit-frame-pointer -c tools/matching_phase0/nul_count.c -o local/matching_phase0/nul-count-pilot/leaf.o
```

The existing ELF parser extracts the defined ARM STT_FUNC symbol, not the whole
section or an arbitrarily clipped 40-byte prefix. Result: .text offset 0,
44-byte symbol, ELF file offset 52. Both original and generated function code
have zero relocations. One generated type-42 `.rel.ARM.exidx` metadata relocation
lies outside the code and does not affect this comparison. No linker or
runtime-address placement claim is made; local PC-relative branches are decoded
relative to the common comparison base.

Generated 44 bytes (our C output):

```text
0010d0e5000051e30000a0031eff2f01011080e20000a0e30020d1e7010080e2000052e3fbffff1a1eff2fe1
```

Generated code SHA-256:
`19b499e34742228e770d70b5c3bc833786a89112489d11556df1b280e0c16177`.
There are **30 unequal positions in the 40-byte overlap plus 4 extra bytes**,
34 differing offsets total. The complete expected/actual byte diff is local;
the ROM-free companion JSON records every differing offset.

Clang uses unsigned byte loads, an initial conditional early return, then a
base-plus-count indexed byte load loop. Its loop starts with count=0 and
base=p+1; iteration k reads p+1+k and increments count to k+1. A zero therefore
returns its index n and produces the same ordered n+1 reads. The source sign
choice is immaterial to zero detection. Different addressing/register allocation
and early-return layout explain this instruction mismatch; no evidence supports
a particular flag that would reproduce the original. No second variant is
justified here, and assembly was not substituted for C.

## Behavioral verification and limitations

The runner decodes the actual original and generated bytes. A deliberately small
whitelisted semantic checker supports only this pilot's byte loads, MOV, ADD,
CMP, conditional branches and BX LR. Every load checks allocated-object bounds
before indexing Python bytes; stores and calls are rejected. An instruction
budget rejects nontermination. Invalid/unterminated/null objects are rejected
before modeled execution; they are not tested as guest behavior.

| Evidence | Actual result | Limit |
|---|---|---|
| Static loop induction | Same n return, reads 0..n, stop at first NUL | Assumes documented decoded ARM semantics and valid stable memory |
| 2,541 terminated words, length 1–5, alphabet {0,1,127,128,255} | Return and ordered byte traces agree | Exhaustive only within this finite alphabet/domain |
| 255 nonzero bytes, four pointer alignments | All 1,020 cases agree | One nonzero byte before NUL |
| 64 longer/embedded-zero cases, lengths through 1,024 | Agree; bytes after NUL never read | Sampled lengths, not all possible buffers |
| Eight ROM-free checker regressions | PASS | Checker tests, not an independently qualified ARM emulator |
| Seven existing ELF/comparator regressions | PASS | Symbol/relocation/byte-boundary checks |

All **3,625** differential cases check count, exact ordered one-byte read
offsets, preserved registers and final NZCV. Original/generated r1/r2 scratch
values can differ; both conform to the modeled caller-clobbered convention.
Finite tests do not prove universal real-DS/compiler behavior. There is no live
guest execution, compiled-runtime parity, original-compiler qualification,
original-source identification, or complete ABI/debug/unwind equivalence claim.

## Reproduction and preservation

```powershell
python -B tools/matching_phase0/nul_count_pilot.py
python -B -m unittest discover -s tools/matching_phase0 -p test_nul_count.py -v
python -B -m unittest discover -s tools/matching_phase0 -p test_diagnostic.py -v
```

The runner prints exact-byte FAIL and behavioral PASS distinctly, returning zero
for the completed diagnostic. The underlying exact comparator returns one for
the byte mismatch. It rechecks identity/boundaries and all ten metadata hashes,
then verifies ROM, extracted main and metadata remain byte-identical (12 inputs).
Raw code, original disassembly, caller window, object and trace details remain
under ignored `local/matching_phase0/nul-count-pilot/`. No ROM/module/metadata
edits, BIOS access, relay changes, proprietary downloads or new framework.

The next highest-information bounded step is to trace input provenance into the
single suffix-check caller to establish whether n>=3 is guaranteed. That can
improve semantic confidence without an original compiler. It has not been
started. Gate0 remains OPEN and original-toolchain matched C remains zero.
