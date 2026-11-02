# Address-labelled C hypotheses, not recovered source

Canonical home for the six Phase0 bodies. Old Phase0 `.c` paths include these
files; they are not duplicate forks. `cluster.c` assembles one **new authored**
translation unit for functional build/object tooling, not an inferred original
compilation unit. Do not link it into a ROM or run it as a host executable.

`contracts.h` owns shared 32-bit declarations. Every original source name,
prototype and original compilation-unit attribution remains unknown. The
five external declarations express only used arguments/normal-return assumptions;
they are not authenticated library APIs. No opaque implementation is supplied.

| Body | Known behavior and restricted domain |
|---|---|
| `func_020660f4` | r0=0; incoming arguments/prototype unknown; no meaning inferred from sentinel callers |
| `func_020660fc` | Call 02019024 with fixed alias, format and int 0x65; ignore its r0, return fixed alias. Stable valid format consuming only compatible supplied arguments; normal opaque return, sufficient nonoverlapping writable storage, no reentrancy |
| `func_0206655c` | Opaque context prepare; unsigned +24 minus +20 snapshot; suffix predicate; conditional 32-byte read initializes header[0], then unsigned >>8; cleanup. Input obeys predicate domain; normal ABI preservation, no concurrent context use |
| `func_020665cc` | Case-sensitive final `cmp` on stable terminated input of length>=3, counter count fits u32, nonwrapping valid pointer increments. No null/short-input guard is invented |
| `func_02067f74` | Ordered byte reads through first NUL; allocated stable readable object, first NUL in bounds, count fits u32, one-past increment valid; no volatile/device memory |
| `func_02068008` | Swap low-halfword bytes and zero-extend, all u32 inputs; do not assume incoming high bits are zero |

`data_020dcbb4` and `data_020dcbf4` are **address aliases**, not allocated C
definitions. Metadata labels both .bss; their 64-byte separation does not prove
either object size. No array[64], context struct, capacity guard, allocator,
ownership, format engine semantics or missing error handling is invented.
Context +20/+24 word loads assume appropriately aligned readable words. The
format wrapper's incoming r1 is overwritten; 0x65 is a vararg, NOT capacity.
Other forwarded register/stack varargs are outside this hypothesis's domain.

ARM ABI, literals, exact object sizes, input hashes, relocations, evidence tiers
and build/test results live in `tools/matching_phase1/batch.json` and
`docs/matching_phase1/batch_status.json`. Exact diagnostic bytes are not an
original-toolchain qualification. Genuine original matches:0; Gate0:OPEN.
