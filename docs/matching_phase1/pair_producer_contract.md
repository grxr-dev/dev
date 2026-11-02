# AD94 success/failure and output-lifetime contract audit

**Branch-complete bounded audit completed; ABBC pair safety remains UNRESOLVED.**
No AD94/helper C was added. The existing ten C hypotheses, headers, manifest,
byte verdicts and six/eight/ten-object link baselines are unchanged. No new or
cosmetic partial link was run. Authentic matches=0; Gate0 OPEN.

Recovered the interrupted #125's uncommitted analyzer, checker extension,
tests and report at HEAD `a7e8d5700200f406e26f5292d47252f170f2c631`.
The authoritative issue and actual working tree were read; useful work was
reused and revalidated, without resetting the branch or replacing unrelated edits.

## Budget and verified boundary

New full-function inspection: AD94 340 bytes plus directly necessary A8D8
76 bytes (416 total including two four-byte pools). Only 16 bytes of existing
ABBC/ACD0 frame prologues were rechecked. No A464 dispatcher body or deeper
helper was decoded. Prior source/model regressions were rerun, not re-engineered.

- AD94: inferred main `.text`, ARM little-endian, [0200AD94,0200AEE8).
  **336 code bytes / 84 instructions**, final pool at 0200AEE4, not 85 instructions.
  SHA-256 `c536d8986a58164efd05d54598aa774b5ad63f2a1b8c6442df467c2ba791be80`.
- Both PC-relative loads (0200ADC0/0200ADE4) target that pool, value 020D4B6C.
  Its pointee is labelled **.bss**: runtime contents, object extent and valid
  resources are unobserved, not ROM bytes or an assumed initialized descriptor.
- Exact relocations: BL at 0200AE24 -> 0200A8D8; BL at 0200AED8 -> 0200A464;
  pool load metadata at 0200AEE4 -> 020D4B6C. No indirect calls/jump tables.
- A8D8: [0200A8D8,0200A924), 72 code +4 pool bytes; SHA-256
  `9950e1d6961160f5bdd7f0c6962186ca0997dd2322879178eaf9a73c3ce659e0`.
  Its pool points to 020D4B68. Three nested calls (A990,6E9C,6EB0) remain
  opaque. It traverses next pointers at +4 until null or a first-word/key match;
  list readability/termination and nested effects are not certified.

## Branch-complete control and memory map

[pair_producer_contract_status.json](pair_producer_contract_status.json) contains
all 84 instruction addresses, **107 labelled CFG edges**, all calls, three exits,
loop edges and per-family success obligations. It contains no raw code snapshot.

| Original range / point | Observed behavior |
|---|---|
| AD94..ADAC | Save r4-r8/LR, reserve 16 bytes (40-byte frame); read input[0] unconditionally; retain scratch/input/output/mode |
| ADB0..ADE0 | Initial `/` or `\`: read global word 0 into a 12-byte local descriptor; zero its two halfwords +4/+6 and word +8; advance input once |
| ADE4..AE1C | Otherwise copy global words 0/1/2 to local descriptor; inspect indices 0..3 for NUL, `/`, `\`, `:`; stop on NUL/separator or after four ordinary bytes |
| AE24..AE34 | Colon found at index 0..3: call A8D8(input,prefix_length); null return exits zero at AE34 |
| AE38..AE54 | Read returned node word +0x10; missing bit 2 exits zero at AE54 |
| AE58..AE98 | Qualified node becomes descriptor word 0, other eight bytes zero; advance past colon, read following byte, skip at most one `/` or `\` |
| AE98..AEB0 | Write scratch+8 = descriptor word 0; +0x38 = current input pointer; copy descriptor by value to scratch+0x2c..0x37 |
| AEB4..AED4 | Mode nonzero: scratch+0x3c=1, +0x40=mode. Mode zero: +0x3c=0, +0x40=original output pointer |
| AED8..AEE0 | Call A464 with r0=scratch,r1=4 (r2=descriptor word 2,r3=scratch+0x2c); restore frame and return its **raw r0**, without booleanizing or checking output |

The only normal exits are AE34, AE54 (explicit zero), and AEE0 (raw dispatcher
result). No direct instruction dereferences the output pointer. **Storing r6
into scratch+0x40 publishes a pointer; it does not initialize either pair word.**
Arguments in r2/r3 at opaque calls are observations, not recovered API arity.
Normal ABI preservation of r4-r8/SP is assumed. Final dispatcher flags are
unknown; no synthetic NZCV guarantee is assigned to AD94's dispatch return.

The scan loop has four iterations, not a full pathname/string validation.
Ordinary four-byte input needs no fifth byte for this body's scan. A colon at
index 3 followed by successful lookup **does** read input[4]. A colon at index
4 is not recognized. Leading separators advance without a subsequent direct
byte read; the published suffix may be one-past and still invalid for the
opaque dispatcher. These observations do not establish its wider read domain.

## Path-sensitive pair proof and exact missing contract

Finite input partitions cover 33 structural families: two leading-separator
families; ten NUL/interior-separator stops; one four-byte fallthrough; and twenty
colon families (four positions times null lookup, disabled node, or enabled
node with three post-colon byte classes). Eight families exit zero before
publishing the pair. **All other 25 reach command 4**, and any can return nonzero
if that opaque call does. Mode branches produce 58 distinct labelled paths.

For the actual ABBC -> ACD0 route, **mode=0** is proven by existing original code.
Required conditional contract at A464 command 4:

1. On a normal nonzero return, synchronously initialize all four bytes of **both**
   words at the destination published in scratch+0x40, before returning.
2. Respect readable/writable bounds and lifetime of scratch/input/destination;
   do not read unknown scratch bytes before writing them and do not retain
   stack pointers for deferred work beyond their owners' lifetimes.
3. Preserve normal call/stack state; any broader effects must obey a separately
   established resource, alias and concurrency contract.

None is proved merely by a nonzero status. The checker explicitly permits
opaque masks 00,01,10,11: all yield a modeled nonzero return when requested, but
only 11 discharges ABBC's two-word read obligation. Across mode-0 nonzero cases,
150/200 countermodels leave a word or both unknown. **These are logical
countermodels under unconstrained summaries, NOT observed Brain Age failures.**
Mode-nonzero does not publish the caller pair and has no pair-initialization
promise in this audit. It is outside ABBC's mode-0 use.

Failure handling is not rollback. Direct prefix failure paths publish no pair
pointer and return zero; their nested helper effects are still opaque. A failed
command 4 may write no words, one, or both. ACD0 normalizes zero to zero and ABBC
then skips both output reads. Nonzero AD94 values, including 0x80000000, normalize
to one, so checking signed positivity instead would be incorrect.

## Partial initialization, aliasing and lifetime

AEE8 initializes 22/68 scratch bytes. At command 4, AD94 has added descriptor,
suffix pointer, mode flag and destination: **46 bytes are known initialized**.
Offsets +0x14..17 and +0x1a..2b (22 bytes) remain unknown. A u32 read at +0x18
is not safe merely because its low halfword was initialized. Whether A464
writes these fields before reading is still outside this audit.

Under the original nested stack layout, relative to ABBC entry SP=S:

- ABBC's output pair: [S-16,S-8), consumed only after successful ACD0 return.
- ACD0 scratch: [S-96,S-28), freed when ACD0 returns.
- AD94 local reservation: [S-136,S-120), including descriptor copied **by value**.

These ranges are disjoint, not heap allocations. On mode 0, AD94 publishes the
outer pair address in the shorter-lived scratch object. Copying the descriptor
does not prove non-retention of scratch or output pointers. Synchronous pair
writes plus non-retention are required; an asynchronous return-before-write
would leave ABBC reading uninitialized storage.

The model explicitly excludes pair aliases with scratch, input, globals, lookup
nodes or owned stack; it also rejects unsupported input aliases. **These are
preconditions of the proof, not guards invented in the original function.**
Arbitrary AD94 callers' alias safety is unproved. Null input is unconditionally
dereferenced at entry; empty mapped storage and short nonterminated inputs can
run out of bounds. A readable NUL byte is different: it reaches command 4 rather
than an early empty-input rejection. Global descriptor/node readability,
concurrent mutation, nested termination and valid resource state remain unknown.

## Reproduction, tests and preserved work

```powershell
python -B tools/matching_phase1/pair_contract.py --publish-status
python -B tools/matching_phase1/batch.py --publish-status
```

The audit reuses pinned input validation, ARM decoding, call checks and the
existing bounded context checker, not a new CPU execution framework. Original
64-step bounds remain for earlier models; AD94 has a 256-step bound (maximum
108 observed). No nested guest function is called. Helpers/globals are explicit
virtual summaries; no host address is dereferenced.

**160 regressions PASS** (prior 135 plus 25), no failures/errors/skips. Ten
compile/model checks still PASS. The audit covers all 107 edges and all 46
predicate outcomes in 792 scenarios, including return normalization, partial
writes, null/short input, scan boundary, unknown scratch reads, alias rejection,
stack restoration, missing CFG edges and altered-loop budget failure. This is
bounded decoded-operation evidence, not an independently qualified ARM emulator
or proof of real opaque-callee effects.

All 12 original inputs and six/eight/ten linked objects/reports are hash-identical;
all ten authored input .o identities agree with the previous link metadata.
Source count stays ten, byte verdicts one trivial Clang MATCH/nine MISMATCH.
No C body/helper, new link, ROM modification, runtime BSS/MMIO access, guest/host C
execution, BIOS, proprietary tool, relay change or binary/asset commit occurred.
Unrelated local work was preserved.

AD94 C is deliberately deferred: its structure is now mapped, but adding a
scenario-only implementation would not close the actual pair/resource/lifetime
obligation, and qualifying its nested effects exceeds this audit's dispatcher
budget. The task's contract-first stopping point is more defensible than a new
unqualified source count. Original CodeWarrior and original compilation-unit
partitions remain unknown; authentic matches=0, Gate0 OPEN.

**One actionable next improvement:** a bounded command-4-only audit of
0200A464 and the exact invoked operation/callback, proving both pair-word writes
before nonzero return, scratch read-before-write safety and pointer non-retention.
Do not broaden that into all dispatcher commands or gameplay execution.
