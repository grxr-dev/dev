# One nontrivial reverse-engineering pilot

**Completed: real behavior learned and C compiled; exact-byte match FAIL.
Gate0 OPEN; original-toolchain verified matched C remains ZERO.**

## Return-zero leaf: 21 callers

The independently re-read body at 0x020660F4 still ignores incoming registers,
sets r0=0, returns through LR, and touches no memory/stack. Every inspected local
pre-call sequence explicitly sets r0=0xFFFFFFFF using `MVN r0,#0`. This weakens
any original `int(void)` claim: the previous void-parameter C was diagnostic only.
An ignored selector argument is plausible, but neither argument count/type nor
source name is recovered. Callee behavior alone cannot distinguish prototypes.

The 21 actual BLs, inferred containing functions and latest visible r0 definitions
are reproduced by `bounded_pilot.py` and `selector_call_sites.csv`. Scope is bounded
static windows, not complete caller CFG/dynamic reachability; possible remote
entries into those windows were not exhaustively analyzed. No game meaning is
assigned to selector constants or later callees.

| Call | Inferred caller start | First use | Class / grounded observation |
|---|---|---|---|
| 0x020258D8 | 0x020258A0 | 0x020258E4 | forwarded: Result remains r0 at the call to 0x0206810C; r1=0, r2=3. Callee argument meaning unqualified. |
| 0x02025AB0 | 0x020258A0 | 0x02025AB4 | index: Copy to r4, then load [sp+r4*4]. |
| 0x02042B24 | 0x020429D8 | 0x02042B28 | arithmetic: Shift left 11; form (result<<11)+0x800. |
| 0x0205AEC4 | 0x0205AEB8 | 0x0205AEC8 | predicate: MOVS into r6; zero immediately causes conditional return. |
| 0x0205B018 | 0x0205AFEC | 0x0205B020 | saved: Store to [sp+0x1C]; ultimate use beyond this window not established. |
| 0x0205EB6C | 0x0205CDBC | 0x0205EB70 | predicate: Compare with 4; equality branches to 0x0205EB88. |
| 0x0205EB8C | 0x0205CDBC | 0x0205EB90 | predicate: Compare with 4; inequality branches to 0x0205EED0. |
| 0x020601F0 | 0x0205CDBC | 0x020601F8 | index: Save to fp; at 0x02060264 used in [lr+fp*4]. |
| 0x02061618 | 0x020610B4 | 0x0206161C | predicate: Signed compare with 1; choose r2=2 for <=1, else 0. |
| 0x020617BC | 0x020610B4 | 0x020617C0 | predicate: Signed compare with 1; branch for >1. |
| 0x02063A74 | 0x020610B4 | 0x02063A78 | predicate: Compare with 4; choose r2=0 for equality, else 2. |
| 0x02069A40 | 0x02069874 | 0x02069A44 | arithmetic: Form r3=r7+(result<<2). |
| 0x0206B724 | 0x0206B66C | 0x0206B728 | arithmetic: Copy to r2, then shift left 12 before a later call. |
| 0x0206B790 | 0x0206B66C | 0x0206B794 | arithmetic: Shift result left 12 into r2 before call to 0x020661B8. |
| 0x0206CF1C | 0x0206CEF8 | 0x0206CFAC | arithmetic: r0 survives two bounded initialization loops; shift left 1 at 0x0206CFAC. |
| 0x0206DC7C | 0x0206DBD4 | 0x0206DC80 | saved: Copy to r4 before r0 overwritten; ultimate path-specific use unresolved. |
| 0x020708EC | 0x020708DC | 0x020708F4 | arithmetic: Save to r5; multiply using r5 at 0x020709C0. |
| 0x020731C8 | 0x02072CE8 | 0x020731CC | arithmetic: Shift left 11; form (result<<11)+0x800. |
| 0x020735E8 | 0x02072CE8 | 0x020735EC | predicate: Compare with 2; equality branches to 0x02073604. |
| 0x020735F8 | 0x02072CE8 | 0x020735FC | predicate: Compare with 4; inequality branches to 0x02073660. |
| 0x02074380 | 0x02074350 | 0x02074384 | saved: Copy to r5 before another call; ultimate path-specific use unresolved. |

Counts: **8 predicates, 7 arithmetic, 2 indices, 1 forwarded, 3 saved**. No
immediate overwrite-before-use/discard was observed. Forwarded means r0 is left
as argument0 at the next ABI boundary; that callee's consumption was not proved.
For three saved values the ultimate path-specific use remains unresolved; a
register/stack copy is not a claim about eventual C-level liveness.

Callers compare against 1, 2 and 4, use signed `GT/LE` tests, and form shift-scaled
indices/arguments. This is more than Boolean-only use, but does not prove those
other values are obtainable: **this exact retail body always returns zero**.
For example, its zero makes 0x0205AEC8's zero-return arm and 0x02061624's `<=1`
selection predictable if reached. No broad gameplay-path claim follows. r0 carries
the result; preservation/copy patterns are consistent with ordinary ARM caller/
callee-save conventions, not evidence for a particular compiler revision.

## Selection based on actual binary characteristics

Metadata inspection was limited to two small helper neighborhoods reached from
these local functions/xrefs. Seven small candidates were decoded, not a mass sweep:

| Candidate | Inferred bytes | Selection observation |
|---|---:|---|
| 0x020660AC | 72 | Calls plus a PC-relative literal word; not a pure leaf. |
| 0x020660FC | 40 | Call and literal pool; unknown callee effects. |
| 0x02066290 | 28 | Two external calls and object data use. |
| 0x020665CC | 72 | Three trailing-byte tests after a length call; pointer/length preconditions unresolved. |
| 0x02067F50 | 36 | Three external calls on related object offsets. |
| 0x02067F74 | 40 | NUL-byte-count loop; requires readable, terminating input. |
| **0x02068008** | **28** | **Pure seven-instruction low-halfword byte exchange; selected.** |

The adjacent inferred ranges meet exactly: preceding 0x02067F9C+0x6C ends at
0x02068008; selected +0x1C ends at next start0x02068024. All seven words decode as
straight-line ARM instructions, ending in BX LR, with no literal loads, embedded
pool, memory access, call or original outgoing relocation. There is one recorded
ARM9-main direct caller at0x0206C44C; immediately before it,0x0206C448 loads r0
with LDRH. Afterward0x0206C450 copies the result into r2. This supports halfword
use, not an original typedef/name. No `htons`/SDK identity is asserted.

## C hypothesis and actual comparison

`tools/matching_phase0/byte_exchange.c` uses a full-width unsigned argument:

```c
unsigned int func_02068008(unsigned int value)
{
    unsigned int low_byte = value & 0xffu;
    unsigned int high_byte = (value >> 8) & 0xffu;
    return (high_byte | (low_byte << 8)) & 0xffffu;
}
```

Full width avoids requiring callers to pre-clear upper bits. Original ASR sign
extension is removed by the subsequent byte mask, so it does not uniquely prove
a signed source argument. A 16-bit versus 32-bit unsigned return is likewise not
recoverable from zero-extension alone.

Existing official Zig0.15.2 / Clang20.1.2 was reused; **no installation or download**.
Executable SHA-256:
`d408dd38eed3e5204af841bcebf70502a4dbbb8399a3a3262be55059370bc018`.
Same ARM946E-S ARM/EABI flags as #115:
`-target arm-freestanding-eabi -mcpu=arm946e_s -marm -O2 -ffreestanding
-fno-builtin -fno-stack-protector -fno-unwind-tables
-fno-asynchronous-unwind-tables -g0 -fomit-frame-pointer`.

One C hypothesis, one flag profile, two actual nontrivial compiler invocations
(initial and scripted repeat), both exit0 and same generated code/object hash.
No second flag experiment was justified: the observed difference is an optimizer
representation choice, not a frame/mode/relocation mistake. No volatile/assembly
forcing or optimization-level/version search was used.

| Measurement | Observed |
|---|---|
| Reference range | 0x02068008..0x02068024 (exclusive), 28 bytes |
| Reference SHA-256 | `934912b08186e4338985ea82639e6b926b4965199850f4688c19792278790c4c` |
| Generated symbol | `.text` +0, size28, ELF file offset0x34, ARM ET_REL |
| Generated code | `ff10a0e3ff1c81e3012000e00004a0e1220480e1010000e01eff2fe1` |
| Generated SHA-256 | `83207b506456471942793769f8e9a5052a0ec5ab66c84a9620c52e048efb549a` |
| Object SHA-256 | `df7477fb53cc957f37a8973dc43079800a060b9fdbd00b1112f39c033665ff04` |
| Exact comparison | **FAIL: 19/28 differing byte positions; final BX LR matches** |
| Original/generated code relocations | 0 / 0 |
| Other generated relocation | One type42 `.rel.ARM.exidx` metadata relocation, outside function |
| Compiler time | Initial about0.145s; scripted repeat about0.088s |
| Linker/guest execution | None |

Exact original/generated bytes, original disassembly and every byte diff are
recorded in ignored `local/matching_phase0/byte-exchange-pilot/result.json`.
Full original call windows remain in local `call-windows.json`. They are not
committed as ROM-derived asset/disassembly files. Public JSON contains the
reference hash, changed offsets and our C-generated bytes, not a ROM byte dump.

The original constructs two byte masks then zero-extends using left/right shifts.
Clang constructs a0xFFFF mask, combines shifted masked data, then masks again.
Both have seven instructions, but their first six encodings/allocations differ.
That is a useful codegen mismatch; it neither disproves the C return-value
hypothesis nor identifies an original CodeWarrior family/version.

## Behavioral proof, regression and reproduction

The bounded static bit-origin analyzer consumes the actual Capstone-decoded
original and generated instructions. Only MOV, AND, ORR, fixed shifts and final
BX LR are supported; memory, calls, conditionals, missing return, undefined
scratch reads and unrepresentable mixed Boolean expressions are rejected.
Both output mappings are exactly:

- output bits0..7 = input bits8..15;
- output bits8..15 = input bits0..7;
- output bits16..31 = zero.

Thus **r0 return values agree for all2^32 input words**, not just sample cases.
This is a static proof within that small transfer model, not dynamic ARM execution
or proof of original source/ABI/timing. Scratch r1/r2 values differ; no exact
scratch-register equivalence is claimed. Both inspected sequences have no memory
or callee-saved/stack effects. This does not increase authentic matched-C count.

From repository root:

```powershell
python -B tools/matching_phase0/bounded_pilot.py
python -B -m unittest discover -s tools/matching_phase0 -p "test_*.py" -q
```

The first prints exact-byte FAIL and bit-mapping PASS, returning0 when the bounded
census/proof succeeds. For byte-match-only exit status, use the shared runner:

```powershell
python -B tools/matching_phase0/diagnostic.py --config tools/matching_phase0/byte_exchange_config.json --source tools/matching_phase0/byte_exchange.c --output local/matching_phase0/byte-exchange-pilot
```

It returns1 for this genuine mismatch. The shared comparator changed only to
accept the configured ARM function size and explicitly reject original code
relocations; its default eight-byte pilot is unchanged and still passed a real
regression compile. Thirteen ROM-free tests passed (7 ELF/comparator,6 bit proof),
including65536 halfword cases,5 high-bit cases and deliberately wrong/unsupported
transforms. No new nontrivial function was attempted after this candidate.

The exact ROM SHA-1/SHA-256 gates pass. Entire extracted main module matches the
corresponding ROM prefix. All12 input files remain byte-identical, including all
ten maps/config files independently rechecked against prior metadata evidence.
No BIOS, runtime/gameplay/save work, proprietary tools, relay changes or old
uncommitted-file edits. Raw binaries and generated artifacts remain ignored.

Next narrow milestone: reconstruct/test the already-observed40-byte NUL-count
helper at0x02067F74 with explicit readable/terminated-buffer preconditions, while
keeping original compiler qualification separate. Further selector-interface
constraints can also advance from consumers without CodeWarrior. Neither starts
in this task. **Gate0 OPEN; original-toolchain verified matched C=0.**
