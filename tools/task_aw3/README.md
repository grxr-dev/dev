# AW3 live-provider and capture-only handoff (PARTIAL)

AX is not authorized or implemented here. Do not launch the capture selector on
Brain Age until the remaining complete-controller certification is authorized
and passes. This task ran only native ROM-free tests and object compilation.

`bridge.h` records runtime-owned cap origins/reschedules/setter invalidations,
owner-thread/epoch/serial provenance, loader-derived ROM identity and immutable
canonical observations. `*.inc` are direct typed providers installed into their
owning runtime translation units. No raw object representation is hashed.
The canonical container remains AW2S v1; additional protected keys are explicit
logical fields, not a change in its wire encoding.

`install.py` applies small checked source hunks using `apply_patch`. It preserves
all AU terminal checks and adds a capture-only handoff before legacy output/halt.
Armed failures cannot use AU finish/ordinary `nds_halt`; a returned handoff at the
protected PC is also fatal. No branch enables candidate dispatch.

Future capture selectors are `NDS_TASK_AW3_CAPTURE_ONLY=1` and
`NDS_TASK_AW3_AUDIT=<fresh file>`. They are disabled by default. The audit is
opened exclusively; the actual cartridge loader hashes its input before secure
area transformations and rejects any nonmatching title. These selectors were
not used to launch a Brain Age process in AW3.

ROM-free reproduction from the repository root:

```powershell
python tools/task_aw3/check.py --output local/task-aw3/certification-new
```

The helper requires local w64devkit, pinned framework sources, AW inert hooks,
and existing ROM-free support libraries. It builds a separate test executable,
not a game runner. The positive AU/handoff model uses a mock CPU and synthetic
memory/provider observations while compiling the actual AU guard fragment.
The real-runtime test exercises actual cap setters/reschedules and CP15 import
on synthetic host globals; its I/O provider deliberately rejects unsupported
use. Six actual runner objects compile separately, without runner relink/launch.

Remaining blocker: AW2's expected snapshots freeze `cap.count`/history and
`snapshot_ordinal`, whereas the actual provider journals every reschedule and
copies the current ordinal. Hidden fetch/data/publication/accounting transitions
also need an exact full-state expected model. The negative test mechanically
demonstrates rejection rather than stripping those protected observations.
Full actual I/O/provider-to-controller success remains unproven. No optional
live replay, executable AX certificate, or reduced positive prefix is supplied.
