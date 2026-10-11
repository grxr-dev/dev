# AW: harness primitives, not an executable AX authorization

Run `python -B tools/task_aw/check.py` for ROM-free preflight, ordered-ledger,
sticky-negative and child-process disposal tests. It compiles one standalone
native test, not an ARM interpreter. No ROM/checkpoint is opened.

`python -B tools/task_aw/install.py` installs inert observer sites and passive
copies into the pinned local framework. No environment selector arms them.
No runner is launched. Existing AU MMIO prohibitions remain intact.

Compile only the five runtime object targets listed in the AW report; do not
relink/launch the runner. Then `python -B tools/task_aw/analyze.py --export`
creates the ROM-free result metadata. The AV body-identical checker now rejects
the added inert system-event observer; AW's audit strips only that observer and
requires the underlying divider/event model to remain byte-identical.

`Contract` attestations default false. A caller must supply an independently
reviewed, complete expected entry and transcript; copying a live snapshot into
an expected snapshot is NOT certification. `passive_snapshot()` deliberately
does not invent the still-uncertified cap provenance, timing classes or readiness
predicates. Its current output fails preflight. Do not fill those holes with zero.

Raw object copies are local diagnostic input, not a portable canonical snapshot
format. They can reject on padding differences. Terminal snapshot hex dumps stay
local; never commit real RAM/save/code/device captures.

`dispose()` is process-only: after explicit audit flush/close it uses `_Exit`,
skipping destructors, normal runner cleanup and persistence. On observer
exceptions it also disposes rather than allowing historical diagnostic catches
to call `nds_halt()`. This primitive is tested; a complete runtime controller is
not certified. **AX is withheld. Stop after AW.**
