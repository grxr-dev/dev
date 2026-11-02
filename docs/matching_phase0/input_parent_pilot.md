# Phase0: parent 0206655C and a bounded runtime-pointer path

Completed one parent reconstruction and a fixed-depth provenance investigation.
The C compiled and conditional call/return checks passed; exact bytes differ.
**Dynamic string extent, termination and n>=3 remain unproven. Gate0 OPEN;
authentic original-toolchain matched C ZERO.** No live game/guest calls ran.

## Independently checked parent

Verified ROM SHA-1: `b8a105bacc3234dede8d4465df0869f2b922a0e2`.
Inferred ARM range `[0206655C,020665CC)` is **112 bytes**, SHA-256
`129e38b34454c88cd7334148db8244ad7dccaab85839bbb75dc21a52b9ec0897`.
It contains **27 instructions / 108 code bytes plus a four-byte literal at
020665C8**, not 28 instructions. That word is 020DCBF4, an address in inferred
.bss. The actual runtime context contents are not present in this ROM extract.

| PC(s) | Actual original behavior |
|---|---|
| 0206655C–64 | PUSH r4/LR, reserve 32 stack bytes, save input r0 in r4 |
| 02066568–78 | Load context address; call 0200AEE8(context); call 0200ABBC(context,input); ignore their return values |
| 0206657C–90 | Read context +24, then +20; retain 32-bit difference +24 minus +20 in r4; pass original input pointer to 020665CC |
| 02066594–98 | Compare predicate result with zero; zero branches to 020665B4 |
| 0206659C–B0 | Nonzero: call 0200AA5C(context, SP, 0x20); ignore returned r0; load word at SP and logically shift it right eight into r4 |
| 020665B4–C4 | Both paths call 0200AB7C(context), ignore its result, return retained r4 in r0; release frame and restore r4/return PC |
| 020665C8 | Shared context literal, data only; all five original PC-relative loads target it |

The frame consumes 40 bytes including saved registers. Explicit parent writes
are the two PUSH words; its reserved 32-byte area is passed to an external call.
External calls can have additional effects, not certified by this body. SP/r4
are restored. LR remains the last BL return address 020665BC; return PC is loaded
from the saved incoming LR. The body itself does not use incoming r1–r3 or stack
arguments. The fully rechecked 0200AEE8 initializer overwrites r1/r2/r3 before the
next call, further excluding those incoming values on this observed path.
The normal ARM call-preservation convention is still an ABI assumption.

On predicate **zero**, result is the saved difference modulo 2^32. On predicate
**one**, result is the post-call stack word shifted logically by eight. The
snapshot is taken before the predicate call. These are word operations; calling
the difference a file size, the stack word a format header, or the final call a
specific close API would require additional callee evidence. Lowercase `cmp`
remains an observed suffix, not an established compression/file-format identity.

Only the pointer in r0 is an explicit parent parameter. Address-derived external
labels and minimal used-argument prototypes in `input_parent.c` are hypotheses,
not recovered library signatures. Opaque caller-clobbered registers and
unobserved external API requirements are not claimed equivalent.

## Bounded input provenance

All three inferred main/ITCM/DTCM relocation maps give eight direct call sites:

| Site | Immediately observed pointer source |
|---|---|
| 020431C4 | r7 selected by nearby PC-relative loads |
| 02058C9C | PC-relative load directly into r0 |
| 0206AF6C | Incoming r2 saved in r4, forwarded in r0 |
| 0206AFD8 | Incoming r1 saved in r6, forwarded in r0 |
| 0206B1AC | Stack word at current SP+5C after a 48-byte local frame and 24-byte PUSH; incoming SP+14 |
| 0207B898 | PC-relative load into r8, forwarded in r0 |
| **02083670** | **Incoming r1 saved in r6, forwarded in r0: selected path** |
| 02085C68 | Conditional PC-relative loads into r8, forwarded in r0 |

Screening used only short, function-bounded pre-call windows, not eight full
function decompilations. Two alternative forwarding candidates were rejected
after short producer checks found literal pointers (0206AFC0 via 0206C328 and
0206B184 via 0202BC40). They establish no dynamic-buffer safety invariant.

The selected investigation has **two caller edges** from the parent: first
02083660's entry-to-call slice, then only the entry prefix of 02085BA8 through
02085BF4. It stops at the return-producing helper call; no traversal of its
body or its callers was undertaken.

1. At 02085BD0–D8, r0=0x14 is passed to 020508F0; its return **O** is saved in
   r5 and checked for zero. Allocation is a plausible interpretation, not a
   newly proved allocator contract or proof of a readable 20-byte string.
2. On the nonzero-O path, 02085BE0 loads argument r0=020D1E94 via pool 02086004;
   02085BE4 sets r1=FFFFFFFF; 02085BE8 calls **020660FC**. Call its returned r0
   value **P**; no buffer base/extent or termination contract is known here.
3. 02085BEC copies P to r1; 02085BF0 copies O to r0; 02085BF4 calls 02083660.
4. At 02083664, r6=r1=P; at 0208366C, r0=r6=P; 02083670 calls our parent.
   The wrapper's incoming object argument O is separately saved in r4.

Thus this is a concrete **runtime-returned, non-literal register-forwarding
path**. It does not prove that P was dynamically allocated/constructed: 020660FC
might select existing storage. In particular **O is not P**, so a purported
20-byte allocation cannot be used as the string's extent. No dominating n>=3
or terminator guard occurs in the decoded path after P is produced. No known
terminator index or allocated readable extent can be assigned to P at this
depth limit. No global invariant or reachable short-string failure is claimed.
The full selected windows and xref evidence remain local in `behavior.json`.

## C hypothesis, compilation and exact comparison

`tools/matching_phase0/input_parent.c` preserves the context address, both return
paths, call order, ignored return values and unsigned word arithmetic. Its valid
comparison domain includes: stable readable nonnull NUL-terminated input with
n>=3, no address/count wrap, ordinary nonvolatile context storage and
non-reentrant execution. For the nonzero branch, the opaque call with r2=32 must
initialize the first stack word before it is read. **No error guard is added.**
The original likewise does not check that call's result; an actual short/failed
operation may leave stale/unknown stack data. Our C does not claim defined
behavior when its local word remains uninitialized, and no value is fabricated
for such a test. It is a freestanding target hypothesis, not host-executed C
dereferencing a Windows address.

One C hypothesis, **one compilation**, no flag variant or assembly substitution:
official local Zig 0.15.2 / Clang 20.1.2, ARM946E-S ARM, exit **0**, empty stderr.
Executable SHA-256:
`d408dd38eed3e5204af841bcebf70502a4dbbb8399a3a3262be55059370bc018`.
The existing -O2/freestanding/no-builtin flags and full invocation/source hash
are recorded in the companion JSON and local result.

All **five REL R_ARM_CALL (28)** relocations are handled by the existing narrow
resolver, with exact symbol/target/addend and range checks. No unsupported
compiled relocation occurred. A type-42 .ARM.exidx relocation is outside code.
The original's sixth metadata entry is **kind:load**, marking its literal word;
it is not a sixth ELF call or a compiled ABS32 relocation. The comparator now
allows only this explicitly configured original word after checking its address,
alignment and value. It does not implement new data-linker relocation types or
mask any comparison bytes. The C's explicit constant needs no ABS32 relocation.

Generated symbol: .text offset 0, ELF file offset 52, **116 bytes**: 28 ARM
instructions / 112 code bytes, then the same four-byte context literal. Its one
literal load targets 020665CC at the common comparison base; the original's
five loads target 020665C8. The dedicated pilot classifies these as data; the
common comparator's linear listings carry an explicit literal-data warning.

Exact symbol comparison **FAIL**: **97 unequal positions in the 112-byte overlap
plus four extra bytes = 101 differing offsets**. Generated resolved SHA-256:
`b0ff6973e7bfe03f61b0278df821b91a2ba500024e8c97c83915740fd194fbd7`.
Complete original/generated bytes, raw unresolved ELF bytes, every relocation
and every byte difference are retained in ignored local evidence, not game
assets in git. This is not an original-toolchain match or a complete link.

Clang saves six registers rather than two, keeps the context address in r4, and
reverses the two context-field read orders (+20 then +24). It delays subtraction
until the zero-result branch, using values already loaded before the predicate
call. Its nonzero branch jumps over that subtraction before the shared final
call. This preserves the modeled result for stable ordinary storage; **memory
read traces, scratch registers, flags and stack layout are not identical**.

## Checks, limits and reproduction

The small decoded-operation checker tests **24 declared external-call scenarios**:
predicate 0/1, four pairs of context words including wraparound differences,
and three stack words including zero/all-ones/high-bit values. Both real decoded
bodies have identical modeled returns and meaningful call arguments/order.
Both ignore zero preparation and transfer return codes when the scenario still
provides the required state. The test deliberately changes context words at the
predicate stub to check that the earlier snapshot, not later values, is used.

These are **conditional control/ABI checks**, not proof of the real external
callees, their side effects, successful I/O, runtime input safety, or full C
behavioral equivalence. No live ARM/DS execution or compiled-runtime parity.

Six new ROM-free tests plus seven ELF regressions and five prior call-relocation
tests: **18 PASS**. A new zero-offset literal fixture initially exposed that the
classifier omitted Capstone's `[pc]` spelling; the parser was corrected and all
six new tests rerun successfully. The production function uses nonzero offsets.

```powershell
python -B tools/matching_phase0/input_parent_pilot.py
python -B -m unittest discover -s tools/matching_phase0 -p test_input_parent.py -v
python -B -m unittest discover -s tools/matching_phase0 -p test_diagnostic.py -v
python -B -m unittest discover -s tools/matching_phase0 -p test_suffix_caller.py -v
```

The first command compiles once and repeats the selected-path and scenario
checks, reporting exact-byte FAIL independently. This investigation ran its
analysis/verification components with the one initial compilation; no second
compiler invocation was needed. Raw evidence is under ignored
`local/matching_phase0/input-parent-pilot/`.

ROM, extracted ARM9 and all ten pinned metadata files are unchanged (12 inputs).
No BIOS, other module payload, proprietary compiler, relay/VM state or unrelated
user work was modified. No mass sweep or subsequent task was started.

**Next substantive decompilation milestone:** reconstruct the small inferred
40-byte 020660FC return-producing helper itself, with its local data references.
That bounded C pilot can determine whether it selects or constructs P and may
provide a concrete producer contract, rather than extending an unbounded graph.
