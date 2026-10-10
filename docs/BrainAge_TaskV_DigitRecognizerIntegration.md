# Task V: production private-bus digit recognizer and native stylus probe

**FULL PASS.** The production-direction Brain Age host now supplies a narrow isolated digit service to `digit-recognition-probe`. The real SDL frontend supplies the exact known two-stroke gesture, and the actual native bottom window displays candidate **2**, then **4**. Original rules and ordinary Back to Training are visually verified. No arbitrary handwriting, original answer submission, correctness, scoring, progression, save/history, guest menu integration or physical pen/SendInput behavior is claimed.

Authoritative evidence: `local/task-v/session-005`. Disabled control: `local/task-v/disabled-002`. Task U predecessor: `c46fa77a38d7669c21a4124aff6eec8d08eb83c4`; pinned framework baseline: `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Exact ROM SHA-1: `b8a105bacc3234dede8d4465df0869f2b922a0e2`. Runner SHA-256: `2896f3ca99cdce71b0430c2067faa50448b34a98c0da854ba78606ea7fcf9def`.

## Architecture and ownership

| File | Responsibility |
|---|---|
| `tools/brainage_custom/bc_digit_recognizer.h` | Narrow begin/recognize-one-host-stroke/end/active interface and `ExerciseServices` dependency |
| `bc_private_digit_recognizer.h` | Private context, incremental index, inputs/outputs/config/stack, read-only code/database, fixed calls and fail-closed bus |
| `bc_rom_resource.h` | Read-only view of the runner's already verified active ROM; exact title resource identity checks |
| `bc_resource_hash.h` | Portable SHA-256 resource check; standard known-answer test |
| `bc_decuma_adapter.h` | Exact Task S point/descriptor encoding, with address-overflow check |
| `bc_digit_probe.h` | Two-stroke contact/capture, candidate/error display, bounds and candidate-independent Continue |
| `bc_contract.h`, `bc_catalog.h` | Minimal factory dependency injection; unchanged default arithmetic and existing freehand selection |
| `bc_host.h` | Supplies and scopes the service, removes owners and destroys exercise/service before original continuation |
| `bc_diagnostics.h` | Optional live RAM/full ARM9 CPU equality and teardown timing audit |

The host contains no expected digit, source geometry, candidate interpretation or recognition-result branch. The exercise contains no ARM addresses, ABI, interpreter or resource-loader logic. There is no public arbitrary PC/register/call/mapping API. The only internal targets are init `020A447C`, recognition `020A41A0`, metric `020A3FB8` and teardown `020A4440`.

The descriptor's factory accepts `ExerciseServices&`; a no-argument convenience call preserves historical P/Q tests. Arithmetic and freehand ignore services; their exercise source is unchanged. The generic exit check accepts permission established on release as well as permission already available before release. It still requires completion, no contact and no previous exit. The probe supplies no selected-answer event, so the historical arithmetic diagnostic labels are never used for its candidates.

The service object is cheap until `begin_session`. A scoped exercise guard guarantees exercise destruction before the service destructor on error. Recoverable missing-resource, coordinate/capacity and returned-call errors become a fixed error display with a safe release/Continue path and no fabricated candidate. An initialized session is still torn down on exit. Private interpreter/bus/teardown invariant failures propagate or terminate during RAII cleanup; they never silently resume the guest.

## ROM resource and private execution

`main.cpp` already owns the selected ROM vector and calculates/checks its SHA-1 before title initialization. The installer changes only that existing call to pass the vector's const view. No new user ROM path, second selection workflow, guest FS call, persistent extraction or broad runner subsystem is introduced.

For this exact immutable ROM identity, Task U's `/data/Decuma/_databas_le.bin` is FAT file 55 at `0x796E00`, length **113956**. The accessor checks the FAT bounds/offset/length and SHA-256 **2f237cc7009314df560311a7c026f2fcf6a47b039f6ad7a70443407ef56db0ad** before returning an independently owned read-only copy. No pre-extracted database is required or committed. Code/constants are independently snapshotted from live title RAM `[02000000,020D2BA0)` only when the session begins.

| Private bus address | Size | Use |
|---|---:|---|
| 02200000 | A350 | context |
| 0220B000 | 4000 | points |
| 0220F000 | 100 | descriptors |
| 0220F100 | 100 | output groups/metric |
| 0220F200 | 16 bytes | config |
| 0220F300 | 8 bytes | counts |
| 02210000 | 8000 | interpreter stack, initial SP 02217FC0 |
| 02220000 | 113956 bytes | read-only database |

These are private bus addresses, **not live DS allocations**. All mutable backing vectors, database and code snapshot belong to the session and disappear on teardown. No live heap, manager/slot, original constructor, thread or queue is used. Code/database writes, unmapped access/MMIO, coprocessors, unsupported/exception results, execution outside the title range and forbidden scene/worker/constructor targets fail closed. Calls retain the ten-million instruction bound, stack bounds/balanced SP and r4-r11 preservation checks from Task U.

**Policy A** remains synchronous private interpretation: no live scheduler, IRQ/device polling or unrelated title execution; no counter restoration/compensation. The private instruction tally is not DS runtime cycles.

## Authoritative SDL, recognition and actual window evidence

Stable activation:

```text
NDS_BRAINAGE_CUSTOM_EXERCISE=1
NDS_BRAINAGE_NATIVE_PRESENTATION=1
NDS_BRAINAGE_CUSTOM_EXERCISE_ID=digit-recognition-probe
```

Stroke 0: down `(190,110)`, motions `(156,91),(121,65),(121,98),(121,130)`, up. Stroke 1: down `(173,114)`, motions `(132,114),(75,114)`, up. Exactly **5+3 deduplicated host points** are encoded as `(source_y,255-source_x)` with 4-byte LE points and 8-byte `(count,address)` descriptors. Nonempty/coordinate/capacity/address checks remain; the exercise stops at two strokes and recognizes only on release.

Input is token/sequence-checked `SDL_PushEvent` before normal frontend mapping, then ordinary `nds_set_touch` and the native owner. No direct exercise/service call or raw DS diagnostic injection supplies authoritative UI input. Fourteen custom events include drawing, a rejected premature Continue and final Continue; their guest-delivery delta is **0**. No physical Win32 SendInput or pen input is claimed.

| Operation | Return | Candidate | Metric | Private instructions | Wall ms |
|---|---:|---|---:|---:|---:|
| Init 020A447C | 0 | — | — | 15069 | 3.784 |
| Stroke 0 + metric accessor | 0 / 0 | 2 | 500 | 636745 | 23.763 |
| Stroke 1 + metric accessor | 0 / 0 | 4 | 249 | 1561225 | 58.875 |
| Teardown 020A4440 | 0 | — | — | 13160 | 0.613 |

Each recognition instruction total includes the 120-instruction accessor. Metric is not confidence. Continue requires two released strokes, successful second recognition, a candidate and no active contact; it never tests candidate == 4. Focused tests use a different returned candidate to verify this distinction.

Actual window PID **66464**, HWND **1048672**, client **512x768**, software SDL presenter. PrintWindow captures and native/guest readbacks correspond at exact 2x scale in the same window. Images were visually inspected; no game screenshots are committed.

| Capture | Actual window/readback bottom RGB SHA-1 |
|---|---|
| WAITING | b2189f1d43249b32d245da499423539862f99755 |
| Candidate 2 | fd63d9d2d24d689bcf8f1c563d260a975949673f |
| Candidate 4 | 0bb86ec8bd466a599c27abc19362e8b1c9703085 |
| Original rules | 698377129c9428a6833e065eb09922ac81651d35 |
| Returned Training | 9fa73ce218415464a1dbedd0c6616c990422ffce |

No prolonged/visibly problematic recognition pause was observed in this bounded run. Calls remain synchronous; a short pause of up to 58.875 ms is possible. No speculative realtime threshold or performance redesign was imposed.

## Isolation, cleanup and save

Entire **4 MiB live main RAM is byte-identical** before session creation and after teardown; before/after SHA-256: `e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab`. Entire live ARM9 CPU structure is byte-identical. Frozen current/requested/selected remains **32/41/11** until Continue.

ARM9/ARM7 cycles remain **2361597139 / 1180798512**; instruction ordinals **211109619 / 69987893**. The guest video aggregate across VRAM A-I, palettes and OAM remains `ce35ae3af7966327430a2110cff94253d76f8b15`. Underlying top/bottom pixels and touch-delivery totals remain unchanged during the hold. Full live RAM equality rules out introduced private pointers or queue/heap-global changes; the private bus has no route to publish such pointers.

Ordered cleanup: contact release -> remove touch owner -> remove bottom presentation owner -> destroy surface/exercise -> original context teardown clears proven 94E0 prefix -> release all private ownership -> require inactive service -> compare live invariants -> untouched original transition resumes. Original transition to 41 executes **once**, rules initializer **020610B4** is reached **once**, constructor count is **0**. The subsequent ordinary guest-owned Back transitions to **32/32**, and the Training menu is visibly restored. Both runs close cleanly with code 0; no stale owner/session/candidate/error influences guest behavior.

Logical save requests **0**, Flash commits **0**, changed save bytes **0**. Initial, live rules, live returned-menu and final on-disk disposable Flash are byte-identical, SHA-256 **a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb**. Canonical checkpoint/save remain untouched.

## Focused validation, attempts and reproduction

Adapter parity compares every known 5+3 point/descriptor byte with unchanged Task S. The production service test performs two fresh init -> 2 -> 4 -> teardown sessions against Task U's local code snapshot, verifies session reset/invalid input/source immutability, and rejects a mutated database hash and wrong title identity. Contract tests cover missing/failed service, safe error exit, candidate-independent permission, duplicate points, no third stroke and selectors. Unchanged P arithmetic pixel/contract/activation tests and Q freehand capture/capacity/selection tests pass. Default/no-ID remains arithmetic; unknown IDs reject clearly; only the new stable ID selects the probe.

The focused disabled control reaches the original rules initializer without any custom instance, hold, service initialization or owners; save remains identical and exit is clean. Installer idempotence, Python syntax checks and diff whitespace checks pass. No unrelated validation/performance matrix was run.

Attempts 001/002 proved recognition/isolation but tapped Back before original rules had rendered. Attempt 003 proved visible rules and a Back scene transition; its menu screenshot sampled the loading interval. Attempt 004 repeated that capture because the intended menu wait was not applied. Final 005 waits for actual guest pixels and establishes the complete visual/clean-exit proof. An early disabled control also sampled the transition too soon; disabled-002 uses a bounded scene wait. All attempt evidence is retained. The reused driver's shadowed initial-save variable caused an incorrect changed-byte count in attempt 001; subsequent reporting compares the real initial save, and every actual save hash remains H0. No recognizer glyph, ABI, title code, counter or resource tuning was involved.

From repository root, with the already provisioned pinned P/Q/U runner:

```powershell
./tools/task_v/build.ps1
python tools/task_v/check.py --rom '../Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds' --code-snapshot local/task-u/session-003/before-mainram.bin
python tools/task_v/drive.py --out local/task-v/<new>
python tools/task_v/drive.py --out local/task-v/<new-disabled> --disabled-control --port 19879
python tools/task_v/analyze.py --out local/task-v/<new> --disabled-out local/task-v/<new-disabled> --export docs/BrainAge_TaskV_Result.json
```

Only the standalone test needs the local snapshot; production does not. Use fresh evidence directories. Raw saves, snapshots, ROM/database bytes, screenshots and binaries stay local/ignored. Committed artifacts are ROM-free headers, focused helpers/tests, this report and the derived [JSON](BrainAge_TaskV_Result.json). The Task V commit is the commit containing these artifacts; its hash/push result is in the final task response.

The production private-bus integration is proven for this exact title and gesture, enough to support a separately authorized bounded generalization step. Remaining blocker: **none for Task V**. No generalization, scoring/save/menu integration or performance redesign was begun. No optimization follow-up is required by these timings. **Stop after Task V.**
