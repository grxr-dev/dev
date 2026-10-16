# AW15: offline scheduler-tail proof, not a continuation permit

Run from the repository root, with the pinned local runtime/toolchain available:

```powershell
python -X utf8 tools/task_aw15/check.py --out local/task-aw15/certification-new
```

The output directory must be fresh. This command reads committed scalar metadata,
framework sources and prior source/lock metadata, compiles an isolated scalar
test executable, and runs focused tests plus two nonreturning model children.
It does not open a ROM, save or checkpoint, link an interpreter/real bus, launch
a runner, invoke historical replay scripts, create permits, or install hooks.

- `model.py`: lossless 411-scalar/five-identity core and 19-scalar GPU binding;
  independent reconstruction of all eight AW14 ownership-chain records;
  explicit protected-field tail transitions and sticky offline ledger.
- `inspect.cpp`: extracted original timer/HALT/GPU/periodic-service source
  bodies on scalar objects; conditional original slice-begin/journal reset;
  distinguishing hidden auxiliary branches; model disposal sentinels.
- `check.py`: source identities/order, entry mutations, transcript negatives,
  conditional cap/epoch arithmetic and unchanged protected sources/evidence.
- `certificate.json`: **withheld** full-tail/new-slice certificate. Conditional
  arithmetic and projected hashes are not a replacement for a successor owner.

The model intentionally stops before `live_overlay_poll`. Its 14 named stages
are new offline proof stages, not newly observed live events and not a modified
AW9/AW14 69-observation ledger. Optional nullable Wi-Fi timestamp changes and GPU
trace-ring bookkeeping are not falsely represented as newly measured fields.

No production identity adapter, activation selector, ownership bypass, cap
normalization, observer removal or executable continuation was added. Existing
AW12 disposal and the completed AW7 ledger still reject continuation. Follow the
report's remaining-work boundary; do not run Brain Age or B4 with these helpers.
