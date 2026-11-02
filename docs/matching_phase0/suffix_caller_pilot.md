# Phase0: suffix caller and bounded input provenance

Completed the one-caller investigation. Safe-domain behavior PASS; exact-byte
comparison FAIL. **A universal minimum-length guarantee is still unproven.**
Gate0 remains OPEN; original-toolchain verified matched C remains ZERO.

## Function behavior, independently re-read

The verified USA Rev1 ARM9 has the inferred ARM function
`[020665CC,02066614)`, 72 bytes / 18 instructions. Its SHA-256 is
`ca96760748f67d4787c0f0b046fb5d4df7c8cdbe4cbf420b59c42f6446a04aca`.
All 18 instructions were decoded from the original extract, which equals the
verified ROM prefix. Complete original bytes/decode are kept locally in
`local/matching_phase0/suffix-caller-pilot/result.json`; the report does not
commit ROM content. The next inferred function begins exactly at 02066614.

| Original PC(s) | Effect |
|---|---|
| 020665CC–D4 | PUSH r4/LR; retain incoming r0 pointer in r4; call counter 02067F74 |
| 020665D8–E4 | Compute n-3; signed-byte load from p+n-3; compare 63; branch to false on mismatch |
| 020665E8–F4 | Compute n-2; signed-byte load from p+n-2; compare 6D; branch to false on mismatch |
| 020665F8–02066600 | Compute n-1; signed-byte load from p+n-1 into r0; compare 70 |
| 02066604–08 | On equality set r0=1 and POP r4/PC |
| 0206660C–10 | Otherwise set r0=0 and POP r4/PC |

For valid inputs this is a **case-sensitive trailing-three-byte predicate** for
63 6D 70 (`cmp`). It does not check a preceding dot, parse a file extension,
change the string or establish a particular format/compression algorithm.
`cmp` alone returns one; any preceding nonzero prefix is irrelevant. A mismatch
at the first or second suffix byte prevents later suffix reads.

The counter first reads p[0..n], including NUL. The predicate then reads p[n-3],
optionally p[n-2], optionally p[n-1]. It writes no input/global memory, but PUSH
writes two four-byte stack slots. SP and r4 are restored; return PC comes from
the saved caller LR. The LR register itself remains 020665D8 after the nested
call. r1/r2 and flags are scratch, r3 and r5–r12 are untouched in the decoded
original. Return flags derive from the last executed suffix CMP; the C compiler
need not reproduce them under the assumed caller-clobbered ABI.

## Four direct callers: no local minimum-length guard

The main/ITCM/DTCM relocation maps contain exactly these four direct references
to 020665CC. Only their entry-to-call slices were analyzed, plus the directly
relevant preparation routines below. No recursive caller sweep was performed.

| Call PC | Containing function | Input provenance and preceding preparation |
|---|---|---|
| 020661E4 | 020661B8 | Incoming r0 saved in r8; r0 restored from r8 at E0. Calls 020664F8 first with global context 020DCBF4 and that pointer. |
| 020662DC | 020662AC | Incoming r0 saved in r7; restored at D8. Calls 0200AEE8 and 0200ABBC with the global context / incoming pointer. |
| 02066408 | 020663E0 | Incoming r0 saved in r6; restored at 404. Same preparation call pattern. |
| 02066590 | 0206655C | Incoming r0 saved in r4; restored at 580 before r4 is reused for a context-field difference. Same preparation call pattern. |

None of these straight-line entry slices branches on pointer nullness or string
length. Under the callee-saved register convention, they forward their incoming
pointer, rather than constructing or extending a string. Preparation call
results are not checked before the suffix test.

020664F8 was decoded in full (100 bytes): it initializes the context, invokes
0200ABBC, subtracts context +20 from +24, saves that quantity at +48, allocates
storage through 0205092C and invokes further calls using it. **That allocation
is not a construction of the pointer later passed to the suffix predicate.**
It supplies no n>=3 guard on that pointer. The complete 40-byte 0200AEE8 body
initializes fields in its r0 context. The complete 72-byte 0200ABBC body uses a
local stack area and nested calls, returns zero/one, and has no explicit string
length comparison. Those nested API bodies are not certified here; no hidden
length guarantee, string mutation rule or documented API contract is assumed.

### One concrete upstream producer, with limited scope

At 020275BC, a PC-relative load through pool 020278F8 supplies r0=020C8C14.
There is no intervening r0 write before the call to parent 020661B8 at 020275D4.
The verified initialized bytes at that address have their first NUL at offset
**36**, and their final three bytes are `cmp`. The path-like literal is recorded
by address, length and SHA-256 in the companion JSON, without copying its full
body into public artifacts. The inferred section map places it in **.data**,
not immutable .rodata.

Thus a real producer supplies a sufficiently long terminated literal. Under
stable-data and normal callee-saved/argument assumptions, this particular
forwarding path is safe and would return one. This is not a dynamic execution
claim or a proof that all other inputs are long enough. In particular, preceding
opaque calls and arbitrary writes to mutable .data are not exhaustively modeled.
No stronger minimum-length contract is recovered from the four forwarding paths.
Indirect references and other title modules also remain outside the census.

### Concrete proof gap, without an unsafe test

Take an allocated one-byte object containing only NUL, with p at its first byte.
The counter legitimately returns zero. The first suffix operation computes
`0-3` modulo 2^32 and adds p, requesting address **p-3**, outside that object.
Lengths one and two similarly request p-2 or p-1 on the first suffix load.
This is a symbolic address derivation, not an executed invalid host/guest read
or evidence that the game actually supplies those inputs. A null pointer also
has no portable valid-memory contract for the counter's first byte load.

Strictly, n>=3 is a sufficient safety contract, not necessary for every possible
machine allocation: a short string whose p lies inside a larger readable object
could have readable preceding bytes, and those bytes could affect the result.
There is no basis for treating all short inputs as a defined false result.

## C hypothesis and actual code generation

`tools/matching_phase0/suffix_caller.c` declares the already-observed counter
call, then performs the three byte comparisons in order and returns unsigned
zero/one. It deliberately adds **no short/null guard**. Its explicit comparison
domain requires stable, nonnull, readable NUL-terminated bytes, n>=3, a
representable count and nonwrapping valid pointer arithmetic, including the
counter's one-past increment. Short/null/unterminated objects are rejected by
the test harness before any modeled execution, not converted into a new C API.
Unsigned byte comparisons preserve the original signed-load zero/equality
decisions against the positive ASCII constants. Original source declarations,
signedness and library identity remain unknown.

Exactly **one compilation**, one hypothesis, no flag variant: existing official
Zig 0.15.2 / Clang 20.1.2 exited **0** with empty stderr. Executable SHA-256:
`d408dd38eed3e5204af841bcebf70502a4dbbb8399a3a3262be55059370bc018`.
Flags are the existing ARM946E-S ARM set:

```text
-target arm-freestanding-eabi -mcpu=arm946e_s -marm -O2 -ffreestanding -fno-builtin -fno-stack-protector -fno-unwind-tables -fno-asynchronous-unwind-tables -g0 -fomit-frame-pointer
```

This function has a real external call. The existing ELF helper was extended
with an opt-in, pinned **REL R_ARM_CALL / canonical ARM BL** resolver, not a
general linker. Other code relocations still fail closed by default. It checks
the undefined symbol name, exact approved target, canonical -8 addend, word
alignment/range and relocation bounds. Original relocation metadata and the
ROM BL target are independently cross-checked before compilation/comparison.
The supported subset uses Arm's documented
[R_ARM_CALL relocation rule](https://github.com/ARM-software/abi-aa/blob/main/aaelf32/aaelf32.rst#call-and-jump-relocations);
Thumb interworking, veneers and other addends are intentionally not supported.

One compiled call at symbol offset +8 resolves to 02067F74; at comparison PC
020665D4 its resolved word is EB000666, the same target/PC as the original call.
No relocation bytes are ignored or masked. Raw unresolved object bytes and
resolved function bytes are both retained locally. One type-42 .ARM.exidx
metadata relocation is outside code; no full linker/ROM rebuild is claimed.

ELF .text symbol offset 0, file offset 52, actual size **56 bytes / 14 ARM
instructions**, versus original 72 / 18. There are **37 unequal bytes in the
56-byte overlap plus 16 missing bytes**, 53 differing offsets. Result: exact-byte
**FAIL**, not an inability to compare. Generated resolved code SHA-256:
`8aca8d6cd11d36c7c8307f91429f29550011ea5e6e575d957b07bf0dd29d9e16`.
The generated machine bytes and all mismatch offsets are in the companion JSON;
the complete expected/actual comparison remains in ignored local evidence.

Clang replaces explicit mismatch branches/early returns with conditional LDRB,
CMP and arithmetic instructions. It builds p+n once, conditionally loads each
negative suffix offset, then uses SUB/CLZ/LSR to produce the final boolean. It
still suppresses the second/third loads on earlier mismatches. This explains
meaningful codegen differences without blaming the linker or inferring an
original compiler version. No assembly substitution or second experiment.

## Behavioral verification, reproduction and next step

The bounded checker interprets only the operations present in the two decoded
predicate bodies and reuses the prior counter checker at the one allowed call.
It bounds-checks each modeled byte access and records two stack word writes,
one counter call, suffix read order, return and preserved register/SP state.
It is **not** an independently qualified ARM emulator or live guest execution.
Static reasoning shows the three original branches implement the stated suffix
predicate on the safe domain; Clang's predication implements the same decision
tree. Scratch register values, flags and timing need not match.

**1,064 safe differential cases PASS**: 216 triples over six nonzero byte values;
768 prefixed cases varying all 256 values in each suffix position (including
embedded-NUL cases that remain n>=3); and 80 prefix-length/alignment/result
cases through 255 prefix bytes. Both actual decoded bodies return the expected
zero/one and perform exactly the same ordered input byte reads. The finite tests
are not a universal real-hardware/compiler proof.

**20 focused unit tests PASS**: five new relocation/domain checks, seven existing
ELF/comparison tests, eight prior counter-checker regressions. Reproduce with:

```powershell
python -B tools/matching_phase0/suffix_caller_pilot.py
python -B -m unittest discover -s tools/matching_phase0 -p test_suffix_caller.py -v
python -B -m unittest discover -s tools/matching_phase0 -p test_diagnostic.py -v
python -B -m unittest discover -s tools/matching_phase0 -p test_nul_count.py -v
```

The first command compiles once and reruns the bounded provenance/behavior audit;
it reports exact-byte FAIL separately from behavioral PASS and returns zero for
the completed diagnostic. For this investigation its analysis and verification
components were run around the single initial compilation; no second compile
was needed. Local evidence is `local/matching_phase0/suffix-caller-pilot/`.

The verified ROM, extracted ARM9 and all ten pinned metadata files remain
byte-identical (12 inputs). No other modules, BIOS, relay/VM state or proprietary
toolchains were changed or accessed for analysis. Unrelated work was preserved.

Next useful bounded milestone: trace one constructed/dynamic input into
0206655C, establishing buffer extent, termination and minimum length; the one
literal example cannot settle that question. That task has not been started.
