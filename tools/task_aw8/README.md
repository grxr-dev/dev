# AW8 exact-profile provider fixture

This is a ROM-free certification target, not a runner or replay launcher.

`check.py` authenticates AW5's saved canonical observation against the committed
AW5/AW6 identity, cross-checks the historical ROM/RAM/DTCM/save hashes, and builds
fresh synthetic runtime objects from its scalar values. The original passive
provider functions read those objects. No provider returns an expected snapshot.

Three test-copy-only adapters bind computed surrogate RAM/DTCM/save digests to
authenticated historical observations. ROM uses authenticated loader metadata;
framework identity is still the provider's original constant. Adapters check the
local surrogate identity and immutable evidence on every sample. They do not
claim synthetic bytes hash to the original images. Original production source
files, getters, manifests and runtime identity behavior remain unchanged.

The generated IO test copy additionally traps at real IO entry before any MMIO
body effect. The five allowed transitions are scalar/model operations only.
AW7's real-bus callback interlock remains closed. No interpreter is invoked.

Requires the existing local framework/toolchain, support libraries, installed
AW3-AW7 source, and AW5's retained metadata audit/attempt lock. Missing or altered
inputs fail closed; no image extraction or replay is attempted.

```powershell
python tools/task_aw8/check.py --out local/task-aw8/certification-new
python tools/task_aw8/certify.py --evidence local/task-aw8/certification-new --out local/task-aw8/readiness-new.json
```

Expected: exact 361-scalar/five-identity entry through real provider interfaces,
69 observations to AW6's final digest, fail-closed controls, and unchanged default
build behavior. Readiness metadata is for a **later separately authorized**
one-shot diagnostic only. It does not arm any runtime or authorize execution.
