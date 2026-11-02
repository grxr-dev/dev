# Phase0: 020660FC fixed-buffer helper and decompilation status

Completed the bounded C reconstruction. **P is now identified: a fixed alias
to shared .bss at 020DCBB4, with delegated formatting-like writes.** It is not
the callee's returned pointer, a table-selected pointer, or the nearby object O.
Exact-code diagnostic FAIL; Gate0 OPEN; authentic matched C remains ZERO.

## Revalidated code, call and storage

The verified USA Rev1 ROM/extracted ARM9 and ten pinned metadata hashes were
rechecked. The inferred ARM function is `[020660FC,02066124)`, SHA-256
`dcbdf9c0b79cf4bcb93cd63faf271892bff2c65c9f5243de536c9bbbdb7cb744`.
Its **40 bytes are nine instructions / 36 code bytes plus one literal word**
at 02066120. The independent next function boundary is 02066124. No conditional
branches or loops occur; there is one external BL and one return.

| PC(s) | Original effect |
|---|---|
| 020660FC–02066100 | Save LR, reserve four more stack bytes: total frame eight |
| 02066104 | Replace r1 with incoming r0 |
| 02066108–0C | Load r0=020DCBB4; set r2=65 |
| 02066110 | BL 02019024 with those values; LR becomes 02066114 |
| 02066114 | Reload r0=020DCBB4, discarding the callee's r0 result |
| 02066118–1C | Release reserved four bytes; load saved PC and restore SP |
| 02066120 | Data: 020DCBB4, targeted by both PC-relative loads |

The helper itself writes only saved LR on its stack; it delegates destination
writes. Callee-saved registers are otherwise untouched under normal ARM ABI
preservation. Flags and r1–r3 after the call are caller-clobbered. Incoming r1
is unconditionally overwritten: **the caller's FFFFFFFF is not a selector or
capacity argument for this helper**. Incoming r2 is also overwritten. Incoming
r3 is forwarded unchanged at BL: additional conversions could observe it (and
further saved/stack words). Its validity/type is not established, so the C
hypothesis restricts formats to the one known compatible supplied argument;
it does not recover the full original prototype for every other caller.

At 02085BE0, the pool at 02086004 yields r0=020D1E94; BE4 sets r1=FFFFFFFF;
the original BL at BE8 reaches this exact helper. Its fixed r0 return P is
forwarded at BEC/BF4 through 02083660 into the earlier parent. O is a separate
register value throughout. No O allocation bound applies to P.

Metadata labels 020DCBB4 and next symbol 020DCBF4 as .bss. Their gap is **64
bytes**, but an inferred next-symbol boundary is not a recovered `char[64]`
declaration or a proved allocated object extent. No bound is enforced here.
Repeated calls return the same address; callers do not own a fresh allocation.
Contents can be overwritten by later calls; reentrancy/overlap is not protected.

## What the adjacent wrappers actually establish

Only two small directly relevant wrapper bodies were additionally decoded:
02019024..02019058 (52 code bytes) and 02019058..020190BC (100 code bytes, with
a separate callback literal at 020190BC). The opaque engine at **0201910C** and
callback body were not recursively decompiled.

02019024 spills incoming r0–r3, reloads its second argument as the format,
points its fourth outgoing argument at the saved r2 slot, and supplies a new
**FFFFFFFF limit** to 02019058. Thus r2=65 from our helper is the **first
variadic argument**. It is ASCII `e`, not a destination capacity of 101.
The incoming helper r1=-1 was discarded; the inner wrapper creates its own -1.

02019058 constructs a local destination/limit/count descriptor, invokes the
engine with a callback and the saved format/argument-list pointers, and appends
a NUL after normal return for a nonnull destination: at offset count when
`count < limit` unsigned, otherwise at `limit-1` when limit is nonzero.
That establishes the wrapper's termination decision, **not** the engine's
correct output count or safety. In this path the limit is UINT32_MAX, so it
does not protect the inferred 64-byte gap. A large/error-like count can select
an invalid/wrapping address; no such operation was executed in this task.

The observed initialized format at 020D1E94 is readable through a NUL after
**29 bytes**, contains one `%c` at offset 23, and ends with the bytes `bmg`.
Its hash including NUL is
`4361be0697b518d4884c05e60f955324fd7b4dafd9596f00ed993bac24460fec`.
Under conventional printf `%c` behavior, replacing those two format bytes by
`e` predicts **28 bytes plus NUL**, with NUL at P+28. That would be n>=3 and
the lowercase `cmp` predicate would be false on this particular output.
**This is conditional interpretation, not original-engine execution proof.**
The engine's `%c` implementation, successful output count, runtime stability of
the mutable .data template and true writable object capacity remain unproved.

The practical input contract is therefore: a valid, stable, terminated format
consuming only the provided compatible argument(s), sufficient nonoverlapping
writable shared destination storage for actual writes plus NUL, and normal
ABI-preserving/non-reentrant execution. The helper does not check any of these.
For generic callers there is still no unconditional output length, NUL or n>=3
guarantee. What changed is that storage identity and intended argument flow are
concrete, rather than another unknown pointer-return dependency.

## C, exact comparison and checks

`tools/matching_phase0/pointer_helper.c` expresses the observed operation:
call address-labelled 02019024 with `(shared, format, 0x65)`, ignore its return,
return shared. The variadic prototype is inferred from the spill/list wrapper;
no original library symbol, source name or precise return type is claimed.

One compilation, no microvariant: existing official Zig 0.15.2 / Clang 20.1.2,
ARM946E-S ARM -O2/freestanding/no-builtin flags, exit **0**, empty stderr.
Executable SHA-256:
`d408dd38eed3e5204af841bcebf70502a4dbbb8399a3a3262be55059370bc018`.
The one REL R_ARM_CALL resolves at the same BL PC 02066110 to 02019024 using
the existing checked policy. Type-42 .ARM.exidx metadata is outside code.
No unsupported relocation, byte masking or full linker was involved.

Original **40 bytes (9 instructions + literal)** versus generated **36 bytes
(8 instructions + literal)**: **22 unequal overlap bytes and four missing bytes,
26 differing offsets**. The literal is at 0206611C in generated code versus
02066120 originally. Clang PUSHes r4/LR, retains the shared address in r4 and
returns via POP, while the original saves LR, reserves four bytes and loads
the address twice. Both consume eight stack bytes, but original/compiled stack
word writes are one/two. Exact byte match **FAIL**. Generated resolved SHA-256:
`17aa9c7dbafafd81ea88496077ed396f5dd9e715c89a9320d71424efe3338c59`.

The bounded decoded-operation check passed **24 normal-return scenarios**:
two abstract valid format pointers, three incoming r1 values, four opaque callee
r0 returns. Both bodies pass the same three meaningful arguments and return
020DCBB4 regardless of that return. Stack and preserved registers restore.
This is not an independent CPU emulator, formatter memory-effect proof, actual
runtime call or universal ABI/behavioral equivalence claim. Five new ROM-free
tests plus seven ELF and five call-relocation regressions: **17 PASS**.

```powershell
python -B tools/matching_phase0/pointer_helper_pilot.py
python -B -m unittest discover -s tools/matching_phase0 -p test_pointer_helper.py -v
python -B -m unittest discover -s tools/matching_phase0 -p test_diagnostic.py -v
python -B -m unittest discover -s tools/matching_phase0 -p test_suffix_caller.py -v
```

The runner compiles once, reports exact-byte FAIL separately and returns zero
for completed bounded checks. This task used its components around the single
initial compile. Raw original bytes, selected wrapper decodes, object, full
comparison and cases remain ignored under `local/matching_phase0/pointer-helper-pilot/`.
ROM, extracted main and ten metadata files are byte-identical (12 inputs).
No BIOS, proprietary downloads, relay changes or follow-on tasks.

## Actual status and next scalable phase

Current pinned metadata has **2,977 main ARM9 function records, 11 ITCM records,
zero DTCM functions**. These are inferred boundaries, not recovered originals
or 2,988 reconstructed functions. Main/ITCM original compilation-unit boundaries
are unknown. ARM7 is an inventoried ROM image, not reconstructed by these pilots;
the existing header census has two CPU images and empty overlay tables.
**No source-reconstructed matching module exists.** Generated native-recompiler
C and original-byte packaging roundtrips do not count as decompiled matching C.

| Phase0 C pilot | Evidence level | Exact diagnostic code |
|---|---|---|
| 020660F4, return-zero | Trivial instruction behavior; prototype unknown | 8/8 bytes match |
| 02068008, byte exchange | r0 bit-map argument for all 32-bit inputs | FAIL |
| 02067F74, NUL counter | Valid-memory induction + bounded read traces | FAIL |
| 020665CC, suffix predicate | Safe-domain decision/read trace checks | FAIL |
| 0206655C, parent | Conditional opaque-call/control scenarios | FAIL |
| 020660FC, this helper | Fixed alias/argument proof, opaque formatting | FAIL |

That is **six authored C hypotheses**, four strong leaf/predicate models in
their stated domains and two conditional opaque-call wrappers. Only one trivial
compiler-agnostic byte match; **zero authenticated original-toolchain matches**.
This ledger is for these Phase0 pilots, not a whole-game semantic census.

The next phase should be **one cohesive 5–10-function source batch**, not another
issue per function: consolidate this small utility/formatting boundary group
under shared address-labelled declarations, mark opaque callees/contracts once,
and keep a manifest with per-symbol bounds, literal/data ownership, relocation
policy and separate behavior/exact-byte status. Compile the batch repeatably;
reuse bounded tests and reject unsupported relocations. Validate the limited
formatter contract needed by real templates rather than chasing every caller.
This can advance functional C reconstruction with the existing Clang toolchain.

For scalable comparison, use expected relocatable objects and a real object-diff
workflow instead of extending the tiny resolver into a general linker.
[ds-decomp](https://github.com/AetiasHax/ds-decomp#delink) documents delinking,
objdiff configuration and module/symbol checks;
[objdiff](https://github.com/encounter/objdiff#usage) compares relocatable objects.
These are proposed next tools/steps, **not installed or run by this task**.
Keep the project's pinned dsd version until a separate qualification warrants
an update; current upstream features do not establish local build success.

Before a module relink can be credible, establish object partitions and shared
data/BSS types, section placement/alignment, ARM/Thumb/entry conventions,
startup/static initialization, all required relocations and external symbols,
and a compatible real linker. Compare the linked module's complete bytes and
symbols against the private verified extract; label any retained original code
as unreconstructed. One cluster object is a useful intermediate milestone, not
a full-module match or ROM rebuild.

Original compiler qualification remains separate: a lawfully obtained local
`mwccarm` plus compatible `mwldarm`, license provenance, banners/hashes/docs,
and representative nontrivial code/ABI/section evidence for Brain Age's still
unknown revision/settings. The existing untracked qualification location is
`local/matching_phase0/toolchains/codewarrior/<family-revision>/`.
dsd's mwldarm LCF support does not identify Brain Age's compiler. No proprietary
download or version sweep is required to start the proposed functional batch.
No batch, module link, additional task or automated child work was initiated.
