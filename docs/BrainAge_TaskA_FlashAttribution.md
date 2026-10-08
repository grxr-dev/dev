# Brain Age Task A: causal cartridge Flash tracing

Date: 2026-10-08. Status: **instrumentation verified; requested CLEAR-RAM-CHECK verification incomplete**.

## Recovery and reconstruction

Used the existing `C:\Users\rustg\Documents\Codex\Muse\dev` checkout on `codex/brainage`, initially at `2bae4f474a9cb24151907cb1b6bff4c5b23b28ae`. The earlier temporary-environment artifacts were unavailable, as instructed; they were not searched for again.

Public framework checkout: `local/ndsrecomp`, pinned to `3a57236bb23d25dcb4caad7d58d733311062ff5e` (0.6.10). Public UI checkout: `local/recomp-ui`, pinned to `7e884a227accea91ddb378671bd49aaeeea13371`. Framework submodules remain at the baseline's declared commits. No framework baseline change was made. The instrumented runner identifies itself as `3a57236-dirty`.

The exact ROM passed SHA-1 verification: `b8a105bacc3234dede8d4465df0869f2b922a0e2`. Extracted ARM9/ARM7 identities match Stage 1A. The ROM was unchanged.

Minimal runner reconstruction succeeded using:

- Unmodified pinned recompiler, built locally with portable w64devkit 2.10.0 / GCC 16.2.0. The initial MSVC build failed on the baseline's existing `__builtin_popcount`; selecting GCC required no source fix.
- Existing ARM9/ARM7 configs, producing 3,333 / 1,284 functions, respectively. Four ARM9 and two ARM7 body shards were emitted for ordinary runner CMake integration. No extra address seeds or coverage banks were added.
- Public FreeBIOS banks. Retail-named BIOS link placeholders were generated from the same public FreeBIOS inputs; runtime selection registers the FreeBIOS tables. No retail BIOS or firmware dumps were used.
- Built-in direct boot and generated firmware, with explicit deterministic MAC `02:00:00:00:00:01`.
- Headless runner: SDL NONE, compute renderer OFF, bootstrap-firmware build ON, existing title-bank SHA-1 gate, existing cartridge configuration for 262,144-byte Flash.

The normal framework build compiled and linked all generated C without manual changes. Existing compiler warnings include generated unused labels, misleading indentation in existing runtime code, and unused headless helpers; these were not silenced or fixed.

All command executions explicitly requested outside-sandbox execution. The broken normal sandbox was not used. The built-in patch tool rejected a reparse-point path, so edits used the bundled `apply_patch` helper through individually approved elevated execution. Approval policy was unchanged.

## Instrumentation and causal attribution

ROM-free continuation files:

- `.gitignore`: additionally excludes state/screenshot extensions.
- `config/brainage_task_a.toml`: direct boot, FreeBIOS, generated firmware, 256 KiB Flash.
- `tools/task_a/ndsrecomp-flash-trace.patch`: temporary edits against the exact framework baseline.
- `tools/task_a/brainage_flash_trace.h`: opt-in JSONL logger and scoped instruction-origin helpers.
- `tools/task_a/origin_test.cpp`: focused attribution test, including deliberately stale global PC and changed CPU between command/data bytes.
- `tools/task_a/build.ps1`: pinned reconstruction, emission, build and focused tests.
- `tools/task_a/probe_boot.py`: erased-save, bounded no-input boot capture, marker detector, optional local checkpoint/frame capture.
- `tools/task_a/analyze_trace.py`: independent old-byte validation, full replay, transaction-origin consistency and disk-image comparison.
- This document.

Actual temporary framework edits under `local/ndsrecomp/runner/src`:

- `cart_backup.h`: diagnostic origin/hook fields and optional arguments.
- `cart_backup.cpp`: command-origin retention, byte-origin retention, write/program and page/sector-erase callbacks at actual memory commits.
- `io.cpp`: capture at the accepted backup-chip SPI call; mark DMA-originated transactions unknown; invalidate diagnostic origin on savestate import.
- `tier3.cpp`: scoped actual interpreter instruction PC/mode around `Interpreter::step`.
- `brainage_flash_trace.h`: copied from our ROM-free diagnostic source.

Path: guest bus store -> `nds_io_write` -> `auxspi_write_data` -> `cart_spi_write` -> `cart_sram_spi_write` -> `nds_cart_backup_spi_write` -> `flash_spi_write`. Dirty completed transfers retain the original `nds_io_flush_cartridge_save` write-through behavior.

CPU identity comes from the scheduler-owned `g_nds_active`. Native generated instructions set `g_cpu.R[15]` to their current instruction PC in their prologue. Tier-3 keeps a separate `CPUState`, so its global `g_cpu.R[15]` can be stale; the new scoped helper supplies the actual `pc` and `thumb` arguments around interpreter execution instead. It does not modify CPU registers.

The first backup-chip command byte (`pos == 0`) captures and retains **command_origin**. Each accepted byte also carries **byte_origin**. The commit callback consumes these retained snapshots, rather than sampling CPU/PC there. In this baseline, Flash SRAM mutation is synchronous during the data/address SPI call; the scheduled AUXSPI event only clears busy later. Thus the byte origin directly identifies the actual committing guest store, while command origin is carried across the SPI state machine. This does not claim to identify the high-level ARM9 IPC requester or callers; those were not traced.

Exact fields per JSONL event:

`sequence`, `transaction`, `command`, `status_before_latch_clear`, `spi_position`, `last`, `offset`, `length`, `changed_bytes`, `wrap_mask`, `commit_path`, `command_origin`, `byte_origin`, `old_hex`, `new_hex`.

Each origin contains `valid`, `cpu`, `pc`, `thumb`, `execution`, `cpu_cycles`, `system_cycles`, `instruction`. CPU values are 9 or 7. Execution is native, tier3, hardware-unknown, or unknown. ARM9 system timestamp is its CPU timestamp shifted right once; ARM7 uses its CPU timestamp directly. The sequence is the authoritative commit order; these are emulated, not wall-clock, times. Instruction ordinals are the framework's execution counters, observed before the store's final cycle charge.

Every accepted program/write byte is logged, including unchanged values, with `changed_bytes` distinguishing actual modifications. Erases log a complete masked span with previous/committed bytes. Baseline write-enable, zero-valued erase/program modeling, address wrapping, dirty flags, persistence and scheduled busy timing are preserved. No generated runtime ABI or generated C was edited.

Hardware-originated writes are explicitly invalid/unknown rather than borrowing a stopped CPU PC. Restoring a state mid-transaction leaves command origin unknown until a new command starts; trace metadata is deliberately not added to the savestate format. Only CPU stores were observed in verification. Logging is opt-in via `NDS_FLASH_TRACE`; it changes host logging cost, not emulated timing.

## Verification evidence

Both the existing `cart_backup_test` and our `TASK_A_ORIGIN_TEST_OK` passed. Python syntax, PowerShell parsing, instrumentation patch reverse-check, and repository diff checks passed.

Fresh saves were exactly 262,144 bytes of `FF`, also matching the framework's fresh-save default. No keys, touch, Daily Training or profile input was sent.

The captured boot initialization contains **31,648 accepted byte commits across 176 writing transactions; 28,976 commits change a byte**. Every old byte validates against independent replay from the erased image. The replayed full 256 KiB image equals the persisted save exactly. All observed command and byte origins are **ARM7, ARM mode, PC `0x038032B8`, Tier-3**. The actual executable word read at that PC is `0xE1C120B0`, `STRH r2,[r1]`, confirming an initiating store rather than a later host helper's incidental PC. Only this instruction was checked; callers were not traced.

The first page transaction is command `0x0A`, transaction 23, offsets `0x100..0x1FF`, **256 separate byte commits**, all `FF -> 00`:

- Command origin: ARM7 `0x038032B8`, system cycle **51,399,763**, instruction **1,478,006**.
- First commit: sequence 1, offset `0x100`, system cycle **51,400,288**, instruction **1,478,270**.
- Last commit: sequence 256, offset `0x1FF`, system cycle **51,430,889**, instruction **1,493,315**, final byte of transfer.
- Region `0x180..0x18D`: sequences **129..142**, 14 individual `FF -> 00` commits, system cycles **51,415,648..51,417,208**. Most adjacent byte timestamps differ by 120 cycles; the full original sequence is preserved, without combining it into one invented operation.

Representative complete event:

```json
{"sequence":129,"transaction":23,"command":"0x0A","status_before_latch_clear":2,"spi_position":132,"last":false,"offset":384,"length":1,"changed_bytes":1,"wrap_mask":262143,"commit_path":"flash_spi_write","command_origin":{"valid":true,"cpu":7,"pc":"0x038032B8","thumb":false,"execution":"tier3","cpu_cycles":51399763,"system_cycles":51399763,"instruction":1478006},"byte_origin":{"valid":true,"cpu":7,"pc":"0x038032B8","thumb":false,"execution":"tier3","cpu_cycles":51415648,"system_cycles":51415648,"instruction":1485822},"old_hex":"ff","new_hex":"00"}
```

Captured Flash JSONL is byte-identical across normal static-bank and existing `--force-tier3` selector captures:

`SHA-256 81cd452919e3371fa3164858b5051c6cfa116907882f24d67d9a90089e957b2e`.

Persisted save SHA-1: `5f3eef519e834abc6e690bcef47aaba00e9e3fcc`.

### Required marker limitation

**CLEAR-RAM-CHECK was not reproduced.** Its literal exists in the supplied ROM, but it does not occur in the captured save or intermediate replay. The expected region `0x180..0x18D` was zeroed by the transaction described above. It must not be reported as a marker write.

The first two probe attempts stopped because the harness misinterpreted transient `run_cycles` pauses, not because a framework halt was logged. The harness now resumes such pauses using the existing `run_rounds` command. A corrected forced-interpreter capture reached ARM9 cycle 600,000,085 / ARM7 cycle 300,000,042. A corrected normal capture preserved a checkpoint at ARM9 cycle 450,000,090 / ARM7 cycle 225,000,045. All produced the same initialization writes and persisted image. No unsupported instruction, fatal dispatch miss or codegen failure was reported.

The checkpoint screenshots show the Brain Age research disclaimer and Nintendo splash saying "Please wait a moment." No profile flow was entered. This leaves the specified marker route unresolved in the minimum reconstructed boot. Attribution is verified for the actual generic writes, but the full requested marker-specific verification cannot be claimed. No save checks were bypassed, and no marker was synthesized or injected to make the test pass.

## Local artifacts

All paths are relative to the existing dev checkout and ignored by Git:

- `build/recompiler-gcc/nds_recompile.exe`
- `build/task-a-runner/nds_runner.exe`
- `build/task-a-runner/cart_backup_test.exe`
- `build/task-a-origin-test.exe`
- `local/inputs/{arm9,arm7}.bin`
- `generated/brainage/` and `generated/public/`
- `local/task-a/{configure,build,build-resumed,emit-*}.log`
- `local/task-a/boot-001/` and `boot-002/`: initial probe logs, saves, and debug responses, including the harness pause diagnosis.
- `local/task-a/boot-003-interpreter/`: corrected bounded capture, `flash.jsonl`, `summary.json`, `trace-audit.json`, `initial-page-sequence.json`, `erased.sav`, `replayed.sav`, debug responses and process logs.
- `local/task-a/boot-004-checkpoint/`: normal capture, same trace/save, `boot.state`, `engine-A.png`, `engine-B.png`, full debug responses including the guest instruction read, and independent audit outputs.

No ROM-derived outputs are staged or pushed.

## Reproduction

Use the existing project checkout. Place public ndsrecomp and recomp-ui checkouts at the pinned commits above under `local/`, initialize ndsrecomp's declared submodules, and supply a local GCC/Ninja/CMake toolchain. The tested portable toolchain directory is `local/toolchain/w64devkit/bin`. Do not clone the title project again. During this Windows sandbox failure, command executions require the explicit outside-sandbox local approval path.

```powershell
.\tools\task_a\build.ps1
python tools/task_a/probe_boot.py --runner build/task-a-runner/nds_runner.exe --rom '../Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds' --out local/task-a/new-boot --max-cycles 450000000 --checkpoint
python tools/task_a/analyze_trace.py local/task-a/new-boot
```

The probe requires a new output directory and refuses to overwrite prior captures. Exit 1 means the required marker was absent within the requested bound; it does not itself mean the runner failed. `--force-tier3` is an optional existing runtime selector, not a coverage-generation step. `build.ps1` encapsulates the same manual configure/emission/build/test steps used here; its syntax and patch idempotence were checked, but the wrapper itself was not separately run end-to-end.

No Task B/C, static caller analysis, one-transition profile experiment, onboarding, optimization, or unrelated DS hardware work was performed.
