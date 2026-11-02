# Address-labelled C hypotheses, not recovered source

Canonical home for the six Phase0 bodies plus four context callees. Old Phase0 `.c` paths include the original six
files; they are not duplicate forks. `cluster.c` assembles one **new authored**
translation unit for functional build/object tooling, not an inferred original
compilation unit. Do not link it into a ROM or run it as a host executable.

`contracts.h` owns shared 32-bit declarations. Every original source name,
prototype and original compilation-unit attribution remains unknown. The
external declarations express only used arguments/normal-return assumptions;
they are not authenticated library APIs. AEE8/ABBC/ACD0/AC04 have authored bodies;
A464/AD94 remain opaque along with 019024/00AA5C/00AB7C.

| Body | Known behavior and restricted domain |
|---|---|
| `func_020660f4` | r0=0; incoming arguments/prototype unknown; no meaning inferred from sentinel callers |
| `func_020660fc` | Call 02019024 with fixed alias, format and int 0x65; ignore its r0, return fixed alias. Stable valid format consuming only compatible supplied arguments; normal opaque return, sufficient nonoverlapping writable storage, no reentrancy |
| `func_0206655c` | Opaque context prepare; unsigned +24 minus +20 snapshot; suffix predicate; conditional 32-byte read initializes header[0], then unsigned >>8; cleanup. Input obeys predicate domain; normal ABI preservation, no concurrent context use |
| `func_020665cc` | Case-sensitive final `cmp` on stable terminated input of length>=3, counter count fits u32, nonwrapping valid pointer increments. No null/short-input guard is invented |
| `func_02067f74` | Ordered byte reads through first NUL; allocated stable readable object, first NUL in bounds, count fits u32, one-past increment valid; no volatile/device memory |
| `func_02068008` | Swap low-halfword bytes and zero-extend, all u32 inputs; do not assume incoming high bits are zero |
| `func_0200aee8` | Ordinary aligned writable context: zero words at +0,+4,+8,+0xc, write 14 at +0x10, zero halfword at +0x18. No object layout/name or volatility inferred; untouched gaps remain untouched |
| `func_0200abbc` | Two-word stack output from ACD0(pair,input); zero skips AC04; otherwise AC04(context,pair[0],pair[1]); booleanize nonzero. Pair must be initialized on successful ACD0, no escaping frame; nested opaque effects assumed |
| `func_0200ac04` | First zero returns zero with no context access; otherwise store raw pair values at +8,+0x2c,+0x30, dispatch command 6, return zero on failure without rollback, or set bit 0x10/clear bit 0x20 in post-dispatch +0xc and return one. Ordinary aligned storage and normal opaque dispatcher contract |
| `func_0200acd0` | Partially initialize 68-byte local reservation through AEE8; call opaque AD94(scratch,input,output_pair,0); normalize its result. No direct output-pair write or guarantee of initialization; no whole-frame zero fill or recovered context type |
| `func_0200af44` | Detach entry using its previous/next links, append to destination tail, clear next, retain entry in r0. Two-pointer prefix is an authored hypothesis, not an SDK type. Requires ordinary exclusive aligned storage, consistent links, entry != destination head and finite acyclic destination after unlink. Destination may be the same chain. No null/cycle/alias validation is invented |

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

The initializer's original reread of +0 and store order are not preserved under
Clang optimization. Its supported domain excludes volatile/device/shared-racing
storage. `void` preserves the old used-argument contract, not an authenticated
return prototype; actual original/generated r0 retention is checked separately.
The wrapper's two raw u32 words are not asserted to be pointers, handles or SDK
types. Nested calls' real effects and error domains are not proved by scenario
stubs. See `docs/matching_phase1/cluster_expansion.md` for full evidence/limits.

The current protocol expansion is documented in
`docs/matching_phase1/context_protocol_expansion.md`. A464's four-argument C
declaration preserves the observed call register values, not proof that every
register is a consumed API parameter. AD94's output/lifetime contract remains
opaque; the parent ABBC still requires two initialized words on success.

The command-4 audit is in `docs/matching_phase1/command4_contract.md`. AF44
actually publishes a caller's scratch pointer into the descriptor queue; this
does not by itself prove synchronous removal. Its C model uses typed link-prefix
objects on the supported domain only, not arbitrary host casts of ROM addresses.
The dispatcher/default handler remain audited originals, not authored C bodies.
