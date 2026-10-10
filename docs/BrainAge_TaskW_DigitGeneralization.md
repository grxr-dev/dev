# Task W: generic digit-entry contract and frozen 0–9 characterization

**FULL PASS for implementation, characterization, input, isolation, reset and cleanup.** Final exact-corpus accuracy is **8/10 (80%)**. Digit 7 finishes as 5, and digit 9 finishes as 4. Those observations are preserved without tuning and do not constitute an implementation failure. This is one frozen sample per digit in Brain Age's rotated writing orientation, not arbitrary handwriting accuracy. **Recognition-input/generalization investigation should precede answer-entry integration.**

Task V predecessor: `9d2f35aa10f6adca396b77e3eedd2bb7ce7895c7`. Framework remains pinned at `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Exact ROM SHA-1 is `b8a105bacc3234dede8d4465df0869f2b922a0e2`. Authoritative evidence is `local/task-w/session-001/digit-0..9`, with `repeat-0` and `legacy-v-4`. Runner SHA-256: `fc4bf3dee295f79e5152192c12b9b77094053ef2bd80555a39d21816e9602d34`.

## Contract and architecture

`tools/brainage_custom/bc_digit_entry.h` adds **digit-entry-probe**, a display-only exercise accepting **8 strokes and 512 total points**. It uses the existing 256x192 surface, canvas x24..232/y32..136 and Continue x72..184/y148..184. Down starts capture, held motion adds points, identical consecutive points are ignored, and up alone invokes recognition. One service session remains alive throughout the glyph. A released stroke permits more strokes as well as a safe exit.

A successful stroke without a candidate enters `no_candidate`, renders **NO CANDIDATE YET**, and stays out of the service-error phase. Candidate availability is independent of operation success; an unavailable candidate value is not displayed or interpreted. A later candidate replaces the display, and a later no-candidate result clears that display. Continue is available after at least one completed stroke and no active contact regardless of candidate availability or correctness. Missing initialization or an actual service/capture-capacity error still provides a safe error exit. `ExerciseStatus.completed` means the display-only activity may exit; it never grades a digit.

Only the catalog adds a fourth stable selector/factory. `bc_digit_recognizer.h` gains semantic comments; service behavior already separated success and availability, so no interpreter/service change was needed. The surface adds digit 6–9 and Y glyphs needed by the generic UI. Existing rendered arithmetic/freehand behavior passes its historical tests.

**Unchanged from Task V:** `bc_host.h`, `bc_private_digit_recognizer.h`, `bc_rom_resource.h`, `bc_decuma_adapter.h`, `bc_digit_probe.h`, `bc_quiz.h`, and `bc_freehand.h`. The analyzer compares each file against the exact Task V commit. The original two-stroke probe remains available and retains its old bounded behavior. No digit, expected label, corpus coordinates, candidate semantics or recognizer ABI entered the host. No arbitrary guest call/RPC, PC/register API, new session manager, second ROM-selection workflow, guest FS, heap, manager/worker/queue, constructor, ROM patch or generated ROM-derived C edit was introduced. Task V's exact ROM/database gate, resource ownership, fixed calls and fail-closed checks remain intact.

## Frozen corpus and exact coordinates

The corpus was declared at **2026-10-10T07:33:56.665805+00:00**, before any Task W recognition observation. Committed source: [corpus.json](../tools/task_w/corpus.json), [freeze.json](../tools/task_w/freeze.json) and [corpus.sha256](../tools/task_w/corpus.sha256).

**Corpus SHA-256:** `23be6ac03c24141c191c0b80e5c18305c1f133847a4123cdb077173eb8d2144d`.

Canonical bytes are UTF-8 `json.dumps(corpus, sort_keys=True, separators=(',', ':'))`, without a trailing newline. Every run verifies that digest and records it with the source gestures. The batch writes a freeze copy before launching the first process. No corpus edits occurred after recognition observation. The 4 is the exact Task S/V 5+3 anchor. Other forms were predeclared as modest human-like title-oriented digits, with multiple strokes for 5, a three-stroke crossed 7 and a two-stroke 9. All listed coordinates are ordinary native DS-screen source points inside the canvas. The unchanged runtime adapter stores `(source_y,255-source_x)`.

`|` below separates released strokes. Each S starts with down; subsequent points are held motion; an up follows the final point.

```text
0: S0: (195,93) (191,75) (172,63) (140,60) (100,65) (78,80) (75,101) (89,117) (116,125) (155,125) (183,116) (195,93)
1: S0: (195,90) (165,90) (135,90) (105,90) (75,90)
2: S0: (170,65) (188,72) (195,94) (187,115) (169,125) (147,120) (125,101) (102,79) (76,60) (76,90) (76,126)
3: S0: (190,65) (195,85) (191,110) (173,122) (152,115) (139,96) (137,80) (132,103) (116,121) (96,122) (78,107) (75,85) (87,63)
4: S0: (190,110) (156,91) (121,65) (121,98) (121,130) | S1: (173,114) (132,114) (75,114)
5: S0: (195,65) (167,65) (141,65) (145,90) (135,115) (115,125) (95,121) (77,106) (75,81) (86,63) | S1: (195,65) (195,95) (195,125)
6: S0: (191,118) (195,95) (186,75) (155,62) (121,60) (92,65) (75,84) (79,106) (98,121) (122,123) (139,112) (143,91) (132,71) (121,60)
7: S0: (195,65) (195,95) (195,125) | S1: (195,125) (165,111) (135,97) (105,83) (75,69) | S2: (137,74) (137,98) (137,120)
8: S0: (195,94) (190,74) (176,64) (157,69) (142,88) (129,106) (110,120) (93,121) (78,108) (75,87) (89,68) (109,62) (129,75) (142,96) (157,114) (177,123) (191,113) (195,94)
9: S0: (159,120) (182,113) (195,93) (188,72) (168,61) (145,64) (131,80) (135,101) (151,117) (159,120) | S1: (159,120) (130,120) (102,116) (81,105) (75,85)
```

The target label exists only in corpus/driver metadata and offline analysis. It is not passed to the exercise or recognizer and never controls candidate selection, success, scoring or exit behavior.

## Real SDL observations

All ten target samples ran in fresh processes through `SDL_PushEvent -> normal frontend mapping -> nds_set_touch -> custom touch owner -> DigitEntryProbe -> production private service`. No direct exercise/service call, raw DS injection, diagnostic candidate or fabricated result counts as authoritative evidence. Supplemental direct service/unit tests are explicitly separate.

| Target | Strokes | Points | Candidate sequence | Final | Offline target match |
|---|---:|---:|---|---|---|
| 0 | 1 | 12 | 0 | 0 | yes |
| 1 | 1 | 5 | 1 | 1 | yes |
| 2 | 1 | 11 | 2 | 2 | yes |
| 3 | 1 | 13 | 3 | 3 | yes |
| 4 | 2 | 8 | 2 -> 4 | 4 | yes |
| 5 | 2 | 13 | 7 -> 5 | 5 | yes |
| 6 | 1 | 14 | 6 | 6 | yes |
| 7 | 3 | 11 | 1 -> 5 -> 5 | 5 | no |
| 8 | 1 | 18 | 8 | 8 | yes |
| 9 | 2 | 15 | 0 -> 4 | 4 | no |

Every one of the **15 corpus stroke calls** completed successfully, returned a candidate and returned error code 0. The fixed metric accessor also completed successfully. Metric is diagnostic, never confidence. Each candidate code below is its returned UTF-16/ASCII digit code. Stroke indices are zero-based. Private instruction totals and wall times include the metric accessor; they are not DS runtime cycles.

| Target / stroke | Points | Candidate available | Code / value | Metric | Return/error | Wall ms | Private instructions |
|---|---:|---|---|---:|---:|---:|---:|
| 0 / 0 | 12 | yes | 48 / 0 | 227 | 0 | 26.113 | 650135 |
| 1 / 0 | 5 | yes | 49 / 1 | 90 | 0 | 24.407 | 629264 |
| 2 / 0 | 11 | yes | 50 / 2 | 191 | 0 | 24.622 | 648591 |
| 3 / 0 | 13 | yes | 51 / 3 | 268 | 0 | 24.277 | 648287 |
| 4 / 0 | 5 | yes | 50 / 2 | 500 | 0 | 23.478 | 636745 |
| 4 / 1 | 3 | yes | 52 / 4 | 249 | 0 | 58.031 | 1561225 |
| 5 / 0 | 10 | yes | 55 / 7 | 416 | 0 | 25.395 | 686256 |
| 5 / 1 | 3 | yes | 53 / 5 | 194 | 0 | 66.620 | 1754965 |
| 6 / 0 | 14 | yes | 54 / 6 | 255 | 0 | 23.906 | 644354 |
| 7 / 0 | 3 | yes | 49 / 1 | 767 | 0 | 30.551 | 816999 |
| 7 / 1 | 5 | yes | 53 / 5 | 415 | 0 | 58.482 | 1576462 |
| 7 / 2 | 3 | yes | 53 / 5 | 615 | 0 | 72.358 | 1904810 |
| 8 / 0 | 18 | yes | 56 / 8 | 233 | 0 | 25.794 | 659746 |
| 9 / 0 | 10 | yes | 48 / 0 | 335 | 0 | 24.219 | 649095 |
| 9 / 1 | 5 | yes | 52 / 4 | 442 | 0 | 58.584 | 1576368 |

The final accuracy calculation is offline only: **8 correct / 10 samples = 80%**. Final confusion counts, rows target and columns returned digit:

| Target \ returned | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 5 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 6 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 7 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| 9 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |

NO CANDIDATE and OTHER final columns are both zero. The two off-diagonal cases are **7 -> 5** and **9 -> 4**. Repeated/legacy runs are excluded from this accuracy and timing population. No points, thresholds, transform, ABI, database or recognizer settings were adjusted to improve these results.

## No-candidate, reset and regressions

All real corpus strokes happened to return candidates. Therefore the no-candidate proof is the **fake-service contract/render test only**; nothing was injected into real recognition. `tools/task_w/contract_test.cpp` returns success=true, availability=false and a deliberately meaningless candidate field. It verifies phase `no_candidate`, diagnostic error=false, exact rendered NO CANDIDATE YET text, continued capture, safe release/Continue, later candidate 2 and replacement with 9. Its ROM-free rendered image was inspected at `local/task-w/fake-no-candidate.png`. It also verifies 8 strokes/512 points, duplicate suppression, release-only recognition, bounded extra strokes, real-error exit and old/new/default/unknown selector behavior.

Authoritative order is **0,1,2,3,4,5,6,7,8,9,0**, with complete teardown between fresh processes. Repeated 0 has the same availability, code, metric, return and private instruction sequence: candidate 0, metric 227, **650135** instructions. `active()==false` after every teardown is recorded. A separate production-service test reuses **one object** for **0 -> end -> 1 -> end -> 0** against the local Task U code snapshot; it verifies identical repeated results/instruction counts, inactive state after each teardown and unchanged source memory. This supplements the real SDL evidence and proves index/point/context ownership resets on end/begin.

Both the generic 4 and the unchanged Task V `digit-recognition-probe` return **2 -> 4**, metrics **500 -> 249**, error 0/0 and private instruction totals **636745 / 1561225**. Historical P arithmetic pixel/contract/activation tests, Q freehand capture/capacity/selection tests, V adapter parity/service/lifecycle/error tests and W contract/reset tests pass. Default/no-ID stays arithmetic; unknown IDs still reject; all four stable IDs resolve correctly. The host/service/adapter/ROM-resource and old exercise source comparisons pass. No broad unrelated gameplay or performance matrix was run.

## Isolation, visual evidence, handoff and save

Policy **A** is unchanged. No scheduler, IRQ/device polling or unrelated title logic runs during isolated calls; counters are never restored to conceal execution. No writable guest RAM is borrowed and no private pointers are published. In every authoritative session, all **4 MiB live main RAM** and the **full ARM9 CPU structure** are byte-identical before session creation and after teardown. Registers, ARM9/ARM7 runtime cycles and instruction ordinals, underlying guest pixels, VRAM/palette/OAM aggregate and guest touch-delivery count remain fixed throughout the native hold. Current/requested/selected stays **32/41/11** until Continue.

| Target | Live RAM SHA-256 before = after | ARM9 / ARM7 cycles held | ARM9 / ARM7 ordinals held |
|---|---|---|---|
| 0 | e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab | 2361597139 / 1180798512 | 211109619 / 69987893 |
| 1 | e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab | 2361597139 / 1180798512 | 211109619 / 69987893 |
| 2 | 6dd8335f5f9614f6e7ec470f74f533041fc97e6a2f269f79a470e920adfd59ec | 2360476791 / 1180238341 | 211053169 / 69958207 |
| 3 | e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab | 2361597139 / 1180798512 | 211109619 / 69987893 |
| 4 | e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab | 2361597139 / 1180798512 | 211109619 / 69987893 |
| 5 | e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab | 2361597139 / 1180798512 | 211109619 / 69987893 |
| 6 | e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab | 2361597139 / 1180798512 | 211109619 / 69987893 |
| 7 | e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab | 2361597139 / 1180798512 | 211109619 / 69987893 |
| 8 | e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab | 2361597139 / 1180798512 | 211109619 / 69987893 |
| 9 | e381676be923dc25e2497259c35391d9e84278698d37a429116db1e9aaf5a3ab | 2361597139 / 1180798512 | 211109619 / 69987893 |

For all ten samples and both supplemental SDL runs: custom guest touch deliveries **0**, logical save requests **0**, Flash commits **0**, changed save bytes **0**. Initial, live handoff and final on-disk disposable 256 KiB Flash are identical: **a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb**. Canonical checkpoint/save are untouched.

After safe Continue: contact clean -> touch/presentation owners removed -> exercise destroyed -> original `020A4440` teardown returns 0, clears the proven context prefix and releases private buffers/code/database -> require service inactive -> verify live state -> original transition to 41 resumes exactly once. Rules initializer `020610B4` is reached once and original Calculations constructor count remains 0. No original answer/correctness/progression/save/history call is made. Every process exits cleanly with code 0, without forced cleanup.

Required actual-window/native-readback proof was captured for **one-stroke 0**, **two-stroke 4**, **three-stroke 7**, plus **original rules and ordinary Back to Training** from generic 4. PrintWindow bottom captures match the same-window readbacks at exact 2x scaling and were visually inspected. Other digit sessions use provenance/invariant/readback diagnostics without unnecessary OS screenshots. Physical SendInput/pen input is not claimed. The fake no-candidate image is contract evidence only.

| Target / capture | Actual-window/readback bottom RGB SHA-1 |
|---|---|
| 0 / initial | 4cc887ae6ac393a6934a79a6cfaae7c59ba37ed9 |
| 0 / stroke1 | 109c7c1b2886c3751e50d28a2e30a195354c6ad4 |
| 4 / initial | 4cc887ae6ac393a6934a79a6cfaae7c59ba37ed9 |
| 4 / stroke1 | c8a7f208f25bcfa25f6df4e2b0a8848f41450993 |
| 4 / stroke2 | 71d70e89e4667fa0edc7d2f873b16a52ed107278 |
| 4 / rules | 698377129c9428a6833e065eb09922ac81651d35 |
| 4 / returned-menu | 9fa73ce218415464a1dbedd0c6616c990422ffce |
| 7 / initial | 4cc887ae6ac393a6934a79a6cfaae7c59ba37ed9 |
| 7 / stroke1 | 9e6b477ef0b03ee0922e8a7fca785c6b18e6fe32 |
| 7 / stroke2 | f4c437e5b19fbceb91cccfe190af2b0551cec0ec |
| 7 / stroke3 | 862e70a15f3431c4bd0021ddadecbffd05fdd34a |

## Timing, artifacts and next step

Across the 15 frozen-corpus calls, recognition wall time is **min 23.478 ms**, **median 25.794 ms**, **max 72.358 ms**. Slowest is target **7**, stroke **2** (third stroke). No realtime threshold was imposed and no optimization was attempted. These synchronous pauses remain bounded; the observed classification issues are input/generalization quality, not latency or isolation failures.

Reproduce from repository root with the existing pinned P/Q/V runner:

```powershell
./tools/task_w/build.ps1
python tools/task_w/check.py --rom '../Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds' --code-snapshot local/task-u/session-003/before-mainram.bin
python tools/task_w/run.py --out local/task-w/<new-batch>
python tools/task_w/analyze.py --out local/task-w/<new-batch> --export docs/BrainAge_TaskW_Result.json
```

The local snapshot is used only by the supplemental direct reset/regression tests. Production still obtains resources from the active verified ROM. Fresh directories are required. The committed artifacts are ROM-free production source, the frozen corpus, focused helpers/tests, this report and [derived JSON](BrainAge_TaskW_Result.json). Raw ROM/database bytes, states/saves, code/RAM snapshots, screenshots/game assets and generated binaries/C stay local/ignored. Python syntax, build, focused tests, source-equality and whitespace checks pass.

Remaining implementation/safety blocker: **none for Task W**. Recognition quality is **not strong enough to proceed directly to answer-entry integration**: even this single frozen sample set has two final confusions, and it does not characterize unseen handwriting or an upright native-canvas writing form. Recommended separately authorized next work is a bounded recognition-input/generalization investigation, especially 7 and 9 and the writing-orientation expectation, using independent samples frozen before observation. Do not retroactively tune this corpus. No answer submission, scoring, save/menu integration, Task X or performance follow-up was begun. **Stop after Task W.**
