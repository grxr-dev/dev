# AW11: lossless terminal metadata and negative handoff certification

`terminal.json` is the complete allowed scalar/hash AW9 terminal observation,
promoted from an existing audit authenticated by AW9's committed digest. It is
not a savestate, ROM/RAM image, raw trace or runtime identity override.

Reproducible ROM-free checks, using a fresh ignored output path:

```
python -B tools/task_aw11/check.py --out local/task-aw11/check-new
```

This reconstructs AW2S solely from the committed metadata, compares all AW10
projection cells and uses original canonical/schema/journal code. Extracted
scheduler/timer/GPU function bodies are compiled on synthetic scalar objects.
No runner, interpreter, runtime bus or Brain Age process is launched. No source
installation occurs. Test-only bodies and binaries remain local/ignored.

Optional historical cross-authentication (read-only, requires retained evidence):

```
python -B tools/task_aw11/authenticate.py
```

The decision can be reproduced from passing evidence into a fresh ignored file,
never into runtime activation:

```
python -B tools/task_aw11/decision.py --evidence local/task-aw11/certification-004 --out local/task-aw11/decision-new.json
```

`state.py`'s direct entry point is the one-time metadata promotion operation; it
rejects if `terminal.json` already exists. Normal tests never need to re-promote or
open the old audit, checkpoint or save. Ownership tags are getter/source ownership,
separate from canonical logical bytes; no native object layout enters identity.

The tests positively certify complete existing metadata and negatively establish
that ordinary return/unwind redispatches at this under-cap boundary. The GPU test
is an ambiguity witness: equal debt can hide different service eligibility. It is
not a claim about which GPU state AW9 actually had or a full runtime-device model.

No early-yield token/escape, new controller phase, cap write, scheduler activation,
guest prefix or dynamic permission is installed. The certificate remains negative
for scheduler execution. Existing AU/69-observation/terminal guards are unchanged.
