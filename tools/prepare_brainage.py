#!/usr/bin/env python3
"""Verify Brain Age USA Rev 1 and prepare ignored ndsrecomp inputs.

This script does not ship or download copyrighted data. The user supplies their
own legally obtained ROM. Extracted binaries are written only to the requested
local output directory and should remain git-ignored.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

EXPECTED_ROM_SHA1 = "b8a105bacc3234dede8d4465df0869f2b922a0e2"
EXPECTED_ROM_SIZE = 0x01000000
EXPECTED_GAME_CODE = b"ANDE"
EXPECTED_REVISION = 1
EXPECTED_ARM9_SHA1 = "eedde90ca6073d4d71653d37ed6997d4eed15ed4"
EXPECTED_ARM7_SHA1 = "f2d795fb08500539b331b67686efcb7e44dc933a"


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    digest = sha1(rom)
    if len(rom) != EXPECTED_ROM_SIZE:
        raise SystemExit(
            f"ROM size mismatch: got 0x{len(rom):X}, expected 0x{EXPECTED_ROM_SIZE:X}"
        )
    if digest != EXPECTED_ROM_SHA1:
        raise SystemExit(
            f"ROM SHA-1 mismatch: got {digest}, expected {EXPECTED_ROM_SHA1}"
        )
    if rom[0x0C:0x10] != EXPECTED_GAME_CODE:
        raise SystemExit(
            f"game code mismatch: got {rom[0x0C:0x10]!r}, expected {EXPECTED_GAME_CODE!r}"
        )
    if rom[0x1E] != EXPECTED_REVISION:
        raise SystemExit(
            f"revision mismatch: got {rom[0x1E]}, expected {EXPECTED_REVISION}"
        )

    arm9_off = u32(rom, 0x20)
    arm9_entry = u32(rom, 0x24)
    arm9_ram = u32(rom, 0x28)
    arm9_size = u32(rom, 0x2C)
    arm7_off = u32(rom, 0x30)
    arm7_entry = u32(rom, 0x34)
    arm7_ram = u32(rom, 0x38)
    arm7_size = u32(rom, 0x3C)

    arm9 = rom[arm9_off : arm9_off + arm9_size]
    arm7 = rom[arm7_off : arm7_off + arm7_size]
    if sha1(arm9) != EXPECTED_ARM9_SHA1:
        raise SystemExit(f"ARM9 SHA-1 mismatch: got {sha1(arm9)}")
    if sha1(arm7) != EXPECTED_ARM7_SHA1:
        raise SystemExit(f"ARM7 SHA-1 mismatch: got {sha1(arm7)}")

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "arm9.bin").write_bytes(arm9)
    (out / "arm7.bin").write_bytes(arm7)

    print(f"ROM verified: ANDE revision {EXPECTED_REVISION}, SHA-1 {digest}")
    print(
        f"ARM9: {len(arm9):,} bytes, ROM 0x{arm9_off:08X}, "
        f"RAM 0x{arm9_ram:08X}, entry 0x{arm9_entry:08X}, SHA-1 {sha1(arm9)}"
    )
    print(
        f"ARM7: {len(arm7):,} bytes, ROM 0x{arm7_off:08X}, "
        f"RAM 0x{arm7_ram:08X}, entry 0x{arm7_entry:08X}, SHA-1 {sha1(arm7)}"
    )
    print(f"Prepared ignored inputs under {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
