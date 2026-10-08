# Brain Age Stage 1A — static emission

Status: **PASS**

This milestone was completed against the exact retail target ROM while keeping the public repository ROM-free.

## Baseline

- Target: *Brain Age: Train Your Brain in Minutes a Day!* (USA Rev 1)
- Game code: `ANDE`
- ROM SHA-1: `b8a105bacc3234dede8d4465df0869f2b922a0e2`
- `RetroPortingToolKit/ndsrecomp` commit: `3a57236bb23d25dcb4caad7d58d733311062ff5e`
- Recompiler project version at that commit: `0.6.10`

The public recompiler was built unmodified on GitHub Actions. The resulting executable and public runtime ABI headers were transferred to the local analysis environment. No ROM, extracted binary, or generated ROM-derived source was uploaded to GitHub.

## Prepared binary identities

### ARM9

- ROM offset: `0x00004000`
- load address: `0x02000000`
- entry PC: `0x02000800`
- size: `0x000D3218` / 864,792 bytes
- SHA-1: `eedde90ca6073d4d71653d37ed6997d4eed15ed4`
- minimal config: `config/brainage_arm9.toml`

### ARM7

- ROM offset: `0x000D7400`
- load address: `0x02380000`
- entry PC: `0x02380000`
- size: `0x00026F24` / 159,524 bytes
- SHA-1: `f2d795fb08500539b331b67686efcb7e44dc933a`
- minimal config: `config/brainage_arm7.toml`

`ndspy.rom.NintendoDSRom` was independently checked: its `arm9` and `arm7` properties are direct byte slices from the ROM, so these raw-image identities match the preparation convention used by existing ndsrecomp title projects.

## ARM9 audit

Minimal entry seed: `0x02000800`, ARM mode.

Results:

- functions discovered: **3,333**
  - ARM: 3,329
  - Thumb: 4
- decoded instructions: **173,080**
- indirect sites reported: 2,679
- stored-pointer seeds: 20
- landing pads: 4
- undefined functions reported by finder: 0
- codegen NOT-IMPLEMENTED ops: **none**
- distinct undefined instruction encodings: **0 ARM / 0 Thumb**
- auto jump tables: 0

Relocation scan detected three matched copies:

- source `0x020D2BA0` -> runtime `0x01FF8000`, size `0x600`
- source `0x020D2292` -> runtime `0x020D4AB0`, size `0x48`
- source `0x020D31A0` -> runtime `0x027E0000`, size `0x4C`

The relocation scan reached its configured step cap after 4,194,304 steps. This is not a codegen failure; it is relevant evidence for later runtime-bank/coverage work.

## ARM7 audit

Minimal entry seed: `0x02380000`, ARM mode.

Results:

- functions discovered: **1,284**
  - ARM: 1,276
  - Thumb: 8
- indirect sites reported: 929
- stored-pointer seeds: 6
- landing pads: 20
- finder `undefined` count: 2
- codegen NOT-IMPLEMENTED ops: **none**
- distinct undefined instruction encodings: **0 ARM / 0 Thumb**
- auto jump tables: 0

The audit's decoded-instruction count from the original static image was 356 because large portions of the ARM7 workload are copied to runtime destinations and discovered through relocation provenance rather than remaining only at the header load base.

Relocation scan found the two important runtime copies immediately:

- source `0x0238FBF4` -> runtime `0x027E0000`, size `0x17319`
- source `0x02380170` -> runtime `0x037F8000`, size `0xFA84`

Generated dispatch output contains substantial native coverage at both runtime destinations. These will need deliberate runtime-bank treatment during bring-up rather than being mistaken for ordinary static addresses.

## Emission

Unmodified `nds_recompile` successfully emitted both banks.

### ARM9 output

- 3,333 functions
- 1 body shard
- generated files: `arm9.c`, `arm9.h`, `arm9_dispatch.c`
- 71 inline-leaf candidates identified

### ARM7 output

- 1,284 functions
- 1 body shard
- generated files: `arm7.c`, `arm7.h`, `arm7_dispatch.c`
- 49 inline-leaf candidates identified

Generated source is ROM-derived and was deliberately kept local and uncommitted.

## Generated-source compile verification

The exact public ABI headers from the pinned ndsrecomp commit were used:

- `recompiler/armv4t/runtime_arm.h`
- `external/arm-recomp-core/common/runtime_arm_types.h`

The emitted sources passed host C syntax compilation against the actual ABI:

```sh
gcc -std=c11 -O0 -DNDS_STATIC_CPU=0 \
  -I<runtime-headers> -I<arm9-output> \
  -fsyntax-only arm9.c arm9_dispatch.c

gcc -std=c11 -O0 -DNDS_STATIC_CPU=1 \
  -I<runtime-headers> -I<arm7-output> \
  -fsyntax-only arm7.c arm7_dispatch.c
```

Results:

- **ARM9_OK**
- **ARM7_OK**

This closes the Stage 1A acceptance criterion that generated code compiles against the current runtime ABI without editing `ndsrecomp` or generated code.

## Cartridge save verification

Current melonDS `ROMList.cpp` contains ANDE as:

`{0x45444E41, 0x01000000, 0x00000005}`

`CartRetail.cpp` maps save type 5 to FLASH with size `256*1024`.

Therefore the exact title should use:

```toml
[cartridge]
save_type = "flash"
save_size = 262144
```

for a future title `game.toml`.

## Known future compatibility risks

These are hypotheses to test at runtime, not fixes to implement preemptively:

1. Brain Age uses DS 2D window registers; current ndsrecomp still has incomplete window-mask rendering support.
2. Brain Age voice recognition uses the standard DS microphone path plus embedded MEI `libASR`; host microphone input has not yet been demonstrated for this title/runtime.
3. ARM7 copies large executable bodies to `0x037F8000` and `0x027E0000`; title bring-up will require correct runtime-bank/dispatch provenance for those copies.
4. Initial minimal discovery still reports unresolved indirect sites, which is expected before runtime coverage/oracle work.

## Verdict

**Static recompilation feasibility is confirmed.**

The current public recompiler can process the exact Brain Age ARM9 and ARM7 binaries, discovers thousands of functions, encounters no unsupported instruction/codegen operations, emits both native C banks, and the generated source compiles against the current runtime ABI.

The next meaningful milestone is no longer static feasibility. It is **Stage 1B: minimal runtime/direct-boot bring-up and first measured divergence**.
