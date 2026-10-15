# AW7 ROM-free integration

This is a **partial certification**, not a runnable Brain Age experiment.
`dynamic_execution_ready` is false; the runtime bus interlock stays closed.

- `integration.h`: exclusive reduced owner, real passive-provider calls, strict
  AW6 ledger, prospective guards and nonreturning audit disposal.
- `install.py`: idempotent dormant local-source additions after prior AU/AW3-AW6
  setup. It does not build a runner, arm the owner or launch anything.
- `test.cpp` / `au_guard_model.h`: installed AU guard fragment and component-getter
  **models**, with the retained source/scalar rail. Positive results are model-only.
- `provider.cpp`: actual getter-object rejection test on AW4's synthetic fixture.
  Its computed identities must not be overridden to force AW5 admission.
- `disabled.cpp`: production-default compile cannot arm the owner.
- `check.py`: focused ROM-free builds, process controls and independent hash/audit
  checks; no ROM/save/state input and no game runner launch.

Prerequisites are the existing local pinned framework, w64devkit toolchain,
AW4 `local/task-aw4/certification-004/build` object set, AW6
`local/task-aw6/certification-008` canonical/source-model metadata, prior AW5
audit/lock and unchanged runner artifacts. Missing prerequisites fail rather than
triggering replay or extracting images. This helper is not a portable fixture
provisioner or a dynamic execution launcher.

Use a fresh ignored output directory:

```powershell
python tools/task_aw7/check.py --out local/task-aw7/certification-new
```

Expected: 366 entry mutation assertions, 49 model child controls, one actual
provider rejection child, a default-mode test and a Tier-3 object compile. The
test summary intentionally remains PARTIAL. See
`docs/BrainAge_TaskAW7_ReducedControllerIntegration.md` for the exact remaining
actual-provider/immutable-identity coupling blocker. No activation command is
provided; do not execute the prefix.
