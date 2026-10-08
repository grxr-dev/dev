# Brain Age Stage 0 findings

Target: **Brain Age: Train Your Brain in Minutes a Day! (USA Rev 1)**

## Exact ROM identity

- Game code: `ANDE`
- Revision: `1`
- Size: `0x01000000` (16 MiB)
- SHA-1: `b8a105bacc3234dede8d4465df0869f2b922a0e2`
- SHA-256: `ac83193346fdca6ea449a6cb60bbe44d327eeb66f2d619d9b1bf8f73600faf5e`
- MD5: `6588b14b57c41efacc6850d07bf037e9`
- CRC32: `10e8d76b`
- Nintendo logo CRC: valid
- Header CRC: valid

## Main executable map

### ARM9

- ROM offset: `0x00004000`
- RAM base: `0x02000000`
- entry PC: `0x02000800`
- raw ROM image size: `0x000D3218` (864,792 bytes)
- raw ROM image SHA-1: `eedde90ca6073d4d71653d37ed6997d4eed15ed4`
- raw ROM image SHA-256: `733b763b65a4f1bffefee7c69e805fe1f400dc9b73a5ead39c12b14916fe175d`
- BLZ/code-compressed: no evidence; module parameters indicate not compressed
- first `0x800` bytes occupy the DS secure-area region; do not treat apparent undecodable bytes there as ordinary executable code before secure-area normalization

### ARM7

- ROM offset: `0x000D7400`
- RAM base: `0x02380000`
- entry PC: `0x02380000`
- size: `0x00026F24` (159,524 bytes)
- raw image SHA-1: `f2d795fb08500539b331b67686efcb7e44dc933a`
- raw image SHA-256: `abef0964e4dde0ad115b814ff5b31a3e748c48691bed8cd4e910bb709069b931`

### Overlays

- ARM9 overlay table size: 0
- ARM7 overlay table size: 0
- No executable overlays were found.

## SDK / middleware fingerprints

The ARM9 contains explicit library signatures:

- `![SDK+MEI:libASR_V1_0_4_patch1]`
- `[SDK+Zi Corporation:MCRLIB]`
- `[SDK+Zi Corporation:SCRLIB]`

NitroSDK module parameters identify the SDK 2.1 generation.

Notable NitroFS data:

- `data/ASR/English/` contains ASR model files (`dtb.bin`, `hmm.bin`, `mdc.bin`, `phn.bin`, `str.bin`, `tree.bin`).
- `data/Decuma/_databas_le.bin` is associated with the Decuma handwriting middleware.
- Brain Age-specific directories include `Calculation`, `Calendar`, `Counting`, `Letter`, `Number`, `Oekaki`, `Stroop`, `Sudoku`, `Text`, `Word`, and others.

Static inspection located a Brain Age ASR wrapper around `0x020538E0` and a nearby vocabulary-building routine around `0x020535FC`. Embedded vocabularies include the Stroop colours, zero through ten, and title-screen phrases involving Doctor/Kawashima/glasses.

## Known ndsrecomp compatibility notes

- Touch, RTC, cartridge save devices, dual CPU execution, IPC and ordinary 2D rendering are already within current `ndsrecomp` scope.
- Brain Age writes DS 2D window registers (`WIN0H/WIN0V`, with related window controls present). Current upstream still lists full 2D window masking as incomplete, so this is a likely future visual divergence to test rather than preemptively patch.
- Host microphone input is not currently treated as a verified supported path for this title. Brain Age's recognition middleware appears to sit above the normal NitroSDK microphone API, making a runtime microphone-device implementation preferable to replacing the ASR engine.

## Current upstream baseline

`RetroPortingToolKit/ndsrecomp`

Commit: `3a57236bb23d25dcb4caad7d58d733311062ff5e`

Date: 2026-10-04

The recompiler config schema uses one TOML per binary, with required program identity and SHA-1, automatic discovery seeded from `entry_pc`, and optional explicit entry points / data ranges / code copies / jump tables.

## Repository hygiene

This repository must remain ROM-free. Do not commit:

- `.nds` ROM images
- extracted ARM9/ARM7 binaries
- BIOS or firmware dumps
- save files
- game assets
- generated C containing large verbatim ROM-derived data if distribution rights are unclear

Hashes, addresses, configs, scripts and analysis notes are permitted.
