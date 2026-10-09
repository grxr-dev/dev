# Brain Age Task C: first-check completion save probe

## Result

**A: no persistent write** during the measured first Brain Age Check completion.
The first-time check used the game's supported **I can't speak** route,
which supplies a twenty-problem handwriting Calculations test. The measured
transition was the final answer **6** to **8-2**, followed only by automatic
settling. The resulting stable screen begins the pre-name introduction:
Kawashima notes that he has not asked the player's name; More is enabled.
No More tap, name entry, confirmation, or later profile transition followed.
No brain-age score was displayed at this stop point.

Both layers report zero operations: **0 logical ARM9 save submissions and
0 accepted Flash commits**. The full 256 KiB Flash image is unchanged.
This result answers the tested non-voice completion boundary; it does not
establish what a later More/name transition does, nor prove equivalence with
the voice/Stroop path. No first post-marker persistent operation was found.

## Task B preservation and interrupted-work recovery

Task B was already preserved and pushed during the preceding attempt:
`9c0cf84b35d463848e925ebddf669fb335c57aea`, on `codex/brainage`.
This retry verified local HEAD and origin matched it; no duplicate commit
was created. That commit includes the Task B report, four helpers, and the
Task A route helper's force-interpreter option, and no runtime payloads.

Partial Task C work existed at `local/task-c/route-001/`, with ROM-free
observer/step helpers under `tools/task_c/`. It had not completed the check.
The old runner was no longer alive, and the interrupted check-launch command
had not created its proposed checkpoint directory. Existing captures were
preserved; onboarding was not repeated this retry.

Independent validation found:

- Full initial Flash replay exactly matches its persisted image. Its 33,200
  events are byte-identical to Task A.5 and Task B, SHA-256
  `76eaf80dbffbe400daa53ddb00767519247a84a3ffcd7a554d2dece9a1854721`.
- The initial logical observer recorded 926 ordered events, including 193
  ARM9 write submissions. Its latest submission is the known marker write.
- No later logical submission or Flash commit occurred during the partial
  onboarding, date confirmation, or right-handed selection.
- The successful local state at `route-001/34-pre-check-question/checkpoint.state`
  restores the exact CPU control state, CPU cycles, instruction ordinals, and
  Flash image. State SHA-256:
  `1c2732d2bb02ec32287651105bf7e06afc448e9c9306f9cbf88cc62db664b544`.

The usable checkpoint was restored into new `local/task-c/recovered-003/`.
An earlier `recovered-002/` restore was preserved: its helper assertion had
incorrectly expected diagnostic event/frame counters to be serialized.
Those counters reset, while CPU cycles and instruction ordinals restore
correctly. Only the helper assertion was corrected; emulator behavior was
unchanged, and that recovery process executed no gameplay before termination.

## Starting state and unchanged baseline

- Checkout: `C:\Users\rustg\Documents\Codex\Muse\dev`, `codex/brainage`.
- ndsrecomp pin: `3a57236bb23d25dcb4caad7d58d733311062ff5e`.
- Same existing title/FreeBIOS banks, direct boot, generated firmware,
  256 KiB Flash configuration, fixed identity MAC, and network off.
- ROM SHA-1 reverified:
  `b8a105bacc3234dede8d4465df0869f2b922a0e2`.
- Source: restored partial Task C checkpoint, not a new boot route.
- Visible state: first-time introduction about checking current DS brain age,
  immediately before launching check preparation.
- Restored ARM9/ARM7 cycles: **6491994316 / 3245997158**.
- Marker exists once at `0x180`.
- Baseline save SHA-256:
  `f8310763e5c388ceeb82b520c20fcd88e35a3c93af14db7d3dcaebcec292ede0`.

Savestate import retains the framework's intentional battery-persistence
detachment. Live Flash was always captured with the existing `cart_save`
command and independently compared with trace replay, rather than assuming
that a disk file necessarily follows a restored state. There were no new
writes here, so the live and on-disk images also remained identical. No
persistence flag, save semantics, or savestate format was changed.

## Setup and the single measured transition

Both logical and physical tracing remained enabled throughout setup.
The pinned local runner exposes no prior PCM injection facility. Rather than
reconstruct microphone hardware or switch framework revisions, this run
selected the game's normal non-voice alternative. All answers were ordinary
stylus strokes processed by the existing game handwriting recognition.
No recognition result, guest register, RAM, or saved value was injected.

Nineteen correct answers led to the final problem. Two unaccepted pen attempts
followed a sideways-screen misreading; the normal Erase control cleared them,
and correctly oriented checkpoint images resolved the equation. This was
normal input correction, not a replay/differential or a game-logic bypass.
No post-marker write/request appeared at any point in setup.

Measured boundaries under `recovered-003/`:

| Boundary | Checkpoint | ARM9 cycles | ARM7/system cycles | ARM9 / ARM7 instruction counts |
| --- | --- | ---: | ---: | --- |
| Before | `35-before-final-answer` | 10738970918 | 5369485459 | 692599842 / 348559311 |
| Final answer, automatic fade | `36-measured-final-answer` | 10938970963 | 5469485481 | 705544135 / 352890922 |
| Stable immediate next state | `37-measured-result-settle` | 11138996880 | 5569498440 | 722050727 / 356836963 |

The before state shows final **8-2**, an empty input canvas, and the preceding
accepted answer. It has a successful local savestate and full Flash snapshot.
The single semantic action was handwriting **6**. The next capture was during
an automatic fade; a no-input wait completed that same transition. The final
state waits on More before asking for a name. The runner was then terminated;
no subsequent game input or transition was performed.

## Logical requests and physical Flash result

- Logical write requests during setup since restore: **0**.
- Logical requests during the measured interval: **0**.
- Ordered requester PCs, payloads, offsets, lengths, FIFO correlations, and
  resulting Flash ranges for this transition: **none**, not invented entries.
- Accepted Flash commits since restore and during the measured interval: **0**.
- Before SHA-256:
  `f8310763e5c388ceeb82b520c20fcd88e35a3c93af14db7d3dcaebcec292ede0`.
- After SHA-256: exactly the same full hash.
- Changed bytes: **0**. Contiguous changed ranges: **[]**.
- Before/after changed-range hex and new ARM core/PC attribution: not applicable.
- Marker region remains `434c4541522d52414d2d434845434b00` at `0x180..0x18F`.

The latest inherited persistent request remains the marker submission:
observer sequence 923, ARM9 `0x0200E080`, payload `0x020D4F60`, offset `0x180`,
length 16, system cycle 438078748, instruction ordinal 74980431. Task B's
established high-level requester for it is `0x0202FCC0`. It is not a Task C
transition request.

The Task C observer has a positive control in that initial capture. It matches
submission 923 -> FIFO send 924 at ARM9 `0x020091B0` -> receive 925 at ARM7
`0x037FE230` -> write entry 926 at ARM7 `0x03802F48`, all with the same shared
request/payload/offset/length. Their system cycles are 438078748, 438078834,
438079007, and 438079572. The sixteen resulting Flash events are transaction
1481, sequences 33185..33200, with the established ARM7 `0x038032B8` origins.
This proves the new logical observer is functional, without redoing Task B's
caller investigation. Sequence counters restart in the new recovery process;
restored emulated cycles/instruction ordinals do not.

## Classification and persistence

**PROVEN:** complete live Flash snapshots compare equal, every recovered
checkpoint matches the baseline, and neither trace layer records a write
through the first stable post-completion state.

**SUPPORTED:** the game's normal recognition/check path completed its twenty
questions and reached a pre-name introduction. The observed marker control
validates the established ARM9-to-ARM7/Flash tracing chain.

**INFERENCE:** persistence may be deferred to a later onboarding transition;
that transition was not tested. No score/result, user name, slot record, or
handedness-derived bytes are classified from RAM or an absent write.

Classification **A**. First observed post-marker persistent operation: **no**.
Genuinely profile-specific persistent operation: **no operation observed**.
No differential was warranted. Persistence terminate/relaunch check: **not
performed / not applicable**, because no changed bytes exist. Termination for
cleanup was performed, but it is not mislabeled a persistence test.

## Tooling and reproduction

ROM-free continuation files are this report and `tools/task_c/`:

- `brainage_logical_trace.h`: opt-in, read-only interpreter-boundary observer.
- `tier3-hook.patch`: its two insertion sites on the Task A/B-instrumented pin.
- `restore.py`: isolated verified checkpoint restore, without old-output overwrite.
- `step.py`: one input/wait, live Flash snapshots, request/commit monitoring,
  local images, optional savestate, and a first-save stop latch.
- `digits.py`: small generic pen paths for normal numeric handwriting input.
- `analyze_transition.py`: measured diff/replay and known marker positive control.

The observer records wrapper `0x0202FA08`, write API `0x0200DE78`, submission
`0x0200E080`, save FIFO send/receive, and ARM7 write entry. Fields include
sequence/kind, CPU/PC/mode/path, cycle/instruction, LR/registers, shared-request
address, payload pointer/validity/full bytes, target offset, and length.
The existing Task A Flash logger is unchanged. Game execution uses the already
supported `--force-tier3` selector so guest request boundaries are observable.

Install on the existing Task A/B diagnostic setup, not on generated C:

```powershell
git -C local/ndsrecomp apply ../../tools/task_c/tier3-hook.patch
Copy-Item tools/task_c/brainage_logical_trace.h local/ndsrecomp/runner/src/brainage_task_c_trace.h
$env:PATH = "$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake --build build/task-a-runner --target nds_runner --parallel 2
```

Do not apply the hook twice; `git apply --reverse --check` verifies an existing
installation. Both trace environments are set by `restore.py`; Task B's bounded
trace environment is removed. Recovery requires the corresponding local
checkpoint and its source session metadata; these are not distributed in Git.

The decisive normal input and audit commands, after reaching the validated
before state, were:

```powershell
python tools/task_c/step.py --out local/task-c/recovered-003 --label 36-measured-final-answer --answer 6 --cycles 200000000 --savestate
python tools/task_c/step.py --out local/task-c/recovered-003 --label 37-measured-result-settle --cycles 200000000 --savestate
python tools/task_c/analyze_transition.py local/task-c/recovered-003 --before 35-before-final-answer --after 37-measured-result-settle --reference local/task-c/route-001
```

Those checkpoint labels already exist; reproduction requires a new directory
and appropriate source state. No additional gameplay validation run was made.
Auditor, Python syntax checks, and hook reverse-check pass. The rebuilt runner
used unchanged generated banks; no coverage expansion was performed.

## Local artifacts and execution safety

- `local/task-c/route-001/`: preserved partial route, marker positive control,
  request/Flash captures, full snapshots, images, and source savestates.
- `local/task-c/recovered-002/`: preserved failed helper-validation attempt.
- `local/task-c/recovered-003/`: restored baseline, setup checkpoints, measured
  before/after saves and states, raw/book PNGs, empty post-restore request/Flash
  traces, debug responses, `restore.json`, `final-observation.json`, and
  `transition-audit.json`.
- Existing `build/task-a-runner/nds_runner.exe`; build log `local/task-c-build.log`.
- ROM-derived runtime evidence remains under ignored `local/`; only ROM-free
  source/scripts/patch/documentation are eligible for commit/push.

The normal sandbox test still failed before process creation with
`helper_unknown_error: setup refresh had errors`. Supported reviewed escalation
was used thereafter; no sandbox/policy change or approval bypass was made.
Routine safe operations proceeded under the current auto-review policy, with
no Graham approval prompt observed and no approval-capacity/bridge failure.
This remaining sandbox setup failure is distinct from the repaired approval
infrastructure and did not block the experiment.

Safety: game patched **no**; Flash/save semantics changed **no**; generated C
manually edited **no**; unrelated hardware implemented **no**; new caller graph
traced **no**; later profile transitions performed **none**. No runner remains
active. Task C stops here; no later task or research phase began.
