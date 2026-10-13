# AW2 ROM-free certification (PARTIAL; AX withheld)

This directory is not an AX launcher or a production runtime activation. It
contains a canonical logical snapshot, immutable AU scalar/hash anchors, a
conditional twelve-instruction prospective model, and an ordered controller
using AW's existing observer/disposal ABI. Unknown live inputs remain denied.

`canonical.h` defines `AW2S` version 1: little-endian widths/counts/lengths;
sorted ASCII keys; explicit 1/2/4/8-byte unsigned cells and lowercase digest
strings. Neither equality nor hashing reads object representations. `model.h`
derives costs/readiness from supplied logical values, not safety attestations.
`observed_timing.h` passively copies actual typed CP15/publication fields.
Cap-chain values in the synthetic fixture are **not a trusted live journal**.

`au_manifest.h` and `manifest.json` contain addresses, words, scalar observations
and hashes from authoritative AU/AV reports. `make_manifest.py` checks those
reports against their Git commits and regenerates identical metadata in memory;
it never opens ROM/save/checkpoint files. Missing historical peripheral/timing
entry classes are explicit. There is no self-approval of a live snapshot.

Run from the repository root:

```powershell
python tools/task_aw2/make_manifest.py
python tools/task_aw2/check.py --output local/task-aw2/retry-20261013/certification-004
python tools/task_aw2/review.py
```

Choose a fresh output directory; existing evidence is never deleted/reused.
The local w64devkit compiler/CMake and existing **ROM-free** `libnds_armv4t.a` /
`libnds_support.a` are required. `CMakeLists.txt` links a separate native test
against real bus/CP15/runtime/scheduler sources and existing device stubs, not
game banks, the Tier-3 interpreter, SDL, a ROM or a runner executable. Device
stubs abort on unsupported access. No guest instruction dispatch is requested.

The positive controller child uses synthetic passive states to validate all 77
ordered observations. Failure children exercise preflight, wrong access/cost,
IRQ, debt, missing events, and rejection of legacy raw snapshots. A further
child calls the **actual** `nds_reschedule_slice` on synthetic host state:
its real observer invokes the controller; wrong copied cap state hard-exits
before the rest of that function can run. This is stronger than a toy `_Exit`
test but does not prove complete live AU snapshot/controller coupling.

Never call `Controller::start` from a Brain Age run on the strength of these
tests. The complete live canonical/cap/readiness provider, immutable dynamic
baseline binding and reviewed AU-to-controller guard handoff are still missing.
No executable AX certificate, reduced prefix or guest authorization is supplied.
