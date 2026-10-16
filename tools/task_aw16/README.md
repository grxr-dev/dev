# AW16 ? ROM-free owned scheduler-tail certification

```powershell
python -X utf8 tools/task_aw16/check.py --out local/task-aw16/certification-new --syntax
```

Use a fresh local output directory. The pinned framework sources, existing
AW9/AW14 scalar/source evidence and local MinGW toolchain must already exist.
Missing evidence fails closed. No download, runner linking/launch, ROM/save/
checkpoint access, interpreter, real bus or runtime Brain Age MMIO is involved.
Without `--syntax`, the command is only a preliminary scalar-rail check.

## Components

- `controller.h`: fixed runtime getters, actual AW12 private receipt plus
  completed AW7 logical ledger binding, one-use observer transfer, chained
  full-state checks and nonreturning audit flush/close/disposal.
- `plan.h`: the exact 26-stage host-only tail to the next slice-begin fence.
  B4 fetch/account/dispatch and all MMIO/guest events remain forbidden.
- `auxiliary.h`, `*.inc`: canonical passive Overlay/Wi-Fi/GPU-trace/scheduler
  observations, including the runtime-owned journal seal latch. No identity
  override, externally supplied readiness flag, pointer hashing or padding.
- `hooks.py`: reversible private source overlay, composed with AW12. Original
  runtime and historical task files stay unchanged. No environment selector,
  permit, launcher, global hook installation or broad scheduler change.
- `fixture.py`, `services.h`, `providers.h`, `inspect.cpp`: isolated source-body
  rail with actual mutable runtime/scheduler/journal getters, dynamic device
  scalars and authenticated readonly metadata. These are not a live image.
- `oracle.py`, `check.py`: independent complete-state/chain/record-grammar checks,
  negative mutations, default/legacy controls and actual-type syntax checks.

The explicit compile-time `AW16_DIAGNOSTIC_TAIL` path must be armed by reviewed
task-scoped host code and offered a valid AW12 receipt. Merely defining it does
not arm anything. Default mode retains the old terminal fence; no owner means
no successor. `AW16_ROMFREE` only enables fault hooks in scalar test binaries.

New auxiliary values in successful tests are **synthetic witnesses**, not newly
measured AW14 state. A later separately authorized validation must sample the
fixed live getters twice, seal their exact canonical values and reject any
unsupported readiness. Never fill missing live values from a test witness.

The existing AW14 process ended and all old permissions remain consumed. AW16
adds no means or authorization to replay, resume that process, run B4, read
DIVCNT, continue past slice begin or reuse a permit. See the report/certificate
for the exact static boundary and prerequisites of a possible later task.
