# Task Y: bounded original answer-entry publication

**FULL PASS for this one disposable publication experiment, on forced Tier-3.** Real SDL input produced private recognizer outputs **2 -> 4**. The Task X equivalent title policy selected **4**, and the untouched original publication routine/caller loaded it into **r2 at 020266B4**. That BL instruction was **not executed**. No correctness, score/count advancement, next problem, completion, history or save occurred. This is not compiled answer-entry parity or a resumable gameplay replacement.

Predecessor: `b08cb211687368e4ca9f089f7dfb3f71a5c8b1d6`; frozen X corpus: `76e3d26e8078ac5e70e5540085202314c0fabe79`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Derived machine-readable evidence: [Task Y result](BrainAge_TaskY_Result.json). No Task X consumer analysis was repeated: its existing bounded disassembly established the original call/return/publication chain.

## Controlled problem and frozen input

Reused immutable `local/task-g/session-001/11-answer-01-63/checkpoint.state` and `after.sav`, copying both into the disposable run. Problem is **11 - 7**, expected **4**, historical correct count **1**, answer phase **1**. Current/requested/selected scene is **11/11/11 hexadecimal**, because this checkpoint is already inside Calculations, not at the Training menu. No menu traversal, original constructor, random-problem search or problem alteration was introduced.

Checkpoint SHA-256: `3911c3e98f90d77916497fd82e4f7ae49e7ca825273e52a90b66fd05ce2b2f2f`. Source and final Flash SHA-256: `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

Canonical input was frozen at `2026-10-10T14:47:55.828191+00:00`, before any Task Y recognition. SHA-256 **`88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`**; UTF-8 JSON sorted keys, compact separators, no newline. `tools/task_y/input.json` and `freeze.json` contain the complete definition and checkpoint digest. The authoritative driver validates both before process launch.

- Stroke 0: `(190,110),(156,91),(121,65),(121,98),(121,130)`.
- Stroke 1: `(173,114),(132,114),(75,114)`.

These are the unchanged V/W known-4 source points. The driver injects 2 downs, 6 held motions and 2 ups through **SDL_PushEvent -> normal frontend mapping -> nds_set_touch -> native owner**. Client size is 512x768; mapping is `(2*x, 2*(192+y))`. Releases map to `(0,0,false)` and do not add points. Every queued event, frontend mapping, native receipt and unchanged guest-delivery total is recorded. No raw-DS command, direct Exercise/recognizer call, fabricated candidate or answer-specific control supplies the authoritative input.

## Title policy and recognition

`bc_calculations_policy.h` consumes host `DigitResult` groups, retains group-0 prefix deltas, replaces the group-1 suffix, bounds the combined numeric positions and applies the exact policy-2 secondary substitution. The unusual two-position units guard on secondary tens !=1 is preserved. Decimal accumulation uses the original signed-32-bit interpretation and 0..99/FFFF result bound; metric is never confidence.

The expected value is read from the preserved exercise **only by title interpretation**, not supplied to private recognition. A Task Y wrapper delegates unchanged production begin/recognize/end calls and observes their returned host values. The generic digit-entry exercise and service are unchanged from X. Publication eligibility is selected countdown=1 and a valid integer, **not a fixed stroke count or an expected-value write**.

| Released stroke | Group 0 count/codes/secondary | Group 1 count/codes/secondary | Selected integer | Original selection countdown | Eligible in this update | Metric | Private instructions |
|---|---|---|---:|---:|---|---:|---:|
| 0 | 0 / [] / [] | 1 / [50] / [48] (`2` / `0`) | 2 | 41 | no | 500 | 636956 |
| 1 | 0 / [] / [] | 1 / [52] / [48] (`4` / `0`) | 4 | 1 | yes | 249 | 1561436 |

Wall times were **26.935 ms / 63.662 ms**, diagnostic only. The first result is not immediately publishable: an ordinary original update would decrement 41 to 40. Guest update time is deliberately frozen during native capture; this experiment does not simulate 40 delayed original frames or assert physical sampling-cadence equivalence. The second release replaces the result/countdown with 4/1; the actual original publication update decrements **1 -> 0**. Three-stroke/two-digit 4/5 timing depends on contributor metadata not exposed here and is explicitly unsupported, rather than guessed.

## Fixed live publication adapter and firewall

The opt-in Task Y interpreter hook holds **before the original BL at 0202668C -> 02052424**, not at an arbitrary guest RPC target. It requires exact title identity/opcode, the preserved problem/count/phase, one idle mode-0 slot, policy=2, expected=4, empty queue, no prior contact, zero original stroke/point counts and countdown=0. It uses the existing host-only SDL service, native touch owner and presentation owner during capture.

After final release it removes both owners, destroys the activity/surface and tears down the private recognizer. Full live RAM, full runner ARM9 CPU and private interpreter CPU are compared with their held snapshots **before any publication staging**.

Only two fixed live fields are then staged in this disposable process:

| Address / role | Before | Staged value | At blocked caller |
|---|---:|---:|---:|
| slot `020FAA50` +320 = `020FAD70`, recognized integer | FFFFFFFF | **4**, from returned groups/title policy | 4 |
| slot +364 = `020FADB4`, original publication countdown | 0 | **1**, from title policy | **0**, decremented by original code |

No private pointer, recognizer context, output code array, queue item, scene global or expected value is written. No original worker is recreated. The interpreter resumes the untouched original instruction. With clean contact/empty queue, original `02052424` reaches `02052F3C..02052FA4`, expires the countdown, writes slot index 0 to the original caller's output, and returns normally. Original caller `02026698..020266AC` resolves the slot and loads its integer; `020266B0` sets the exercise argument.

At **020266B4, before BL 02025778**, the firewall verifies **r0=020E9A00, r1=0, r2=4**, countdown=0, one original publication entry and one slot read. It snapshots state and terminally stops. Entry to 02025778/02025698, accepted-phase store 020265F8, save API 0200DE78, original constructor/manager/worker setup and instruction-budget overflow fail closed. No instruction at the correctness BL or its callees executes.

The opt-in frontend exit guard leaves the frame loop on this diagnostic terminal halt and follows normal runner shutdown; it does not resume the half-submitted guest. Both successful control and authoritative process exit **0**, without forced cleanup. This small host exit guard is necessary because halting just ARM9 otherwise leaves the interactive frame wait stalled. No guest counters are restored and no synthetic return is used.

## Isolation and side effects

- During native capture: ARM9/ARM7 cycles **3416875127 / 1708437504**; instruction ordinals **281097760 / 96026779**, all invariant. Frontend hold presents advance **0 -> 161**.
- Guest video aggregate (VRAM A-I, palettes, OAM) stays SHA-1 `d3f4367c0f34a5ce1a876c419a1aeb927c17b499`; custom pixels use only the removable presentation surface.
- All 10 custom events are consumed; guest touch-delivery delta **0**. Contact is released before ownership removal/publication.
- Full 4 MiB RAM before/after private service has SHA-256 `5c0784c4b91e0ae19fc9941e08af7afc7aa46968aa38ef3cdcb16899aded577b`; both CPU representations compare equal. Policy A runs no live scheduler, IRQ/device polling, heap, FS, original constructor or worker/thread/queue. Original private teardown returns 0 in **13160** instructions and leaves the service inactive.
- After cleanup, the original publication path legitimately advances ARM9 by **166 cycles / 74 instructions**; ARM7 instruction ordinal stays fixed. This advancement is not concealed or called part of isolated recognition.
- At the blocked caller, **exactly four RAM bytes differ**, solely `020FAD70..020FAD73`: the staged integer. The countdown has expired naturally. The complete exercise (C34 bytes) and manager (238 bytes) remain byte-identical. Correct count remains **1**, phase **1**, expected **4**. No score/result acceptance or next-problem store occurred.
- Logical save requests **0**, Flash commits **0**, changed Flash bytes **0**, dirty=false. Source, live final snapshot and on-disk disposable save remain the identical SHA-256 above. No new savestate was saved from the publication state; the source checkpoint/save remain unchanged.

Native initial/first-release actual window captures stay local; the first-release image was inspected and shows `CANDIDATE: 2`, the stroke and the frozen original 11-7 context. The proof of 4 at the original caller is the exact instruction-boundary audit/readback, not a fabricated screenshot or a claim that the original game accepted it.

## Controls, regressions and attempts

Authoritative evidence: **`local/task-y/session-001`**. Disabled control: **`local/task-y/disabled-004`**, same problem checkpoint and gate, no native activity/input/staging, unmodified state at the read-only breakpoint, unchanged save, exit 0.

Focused tests in `local/task-y/focused-tests.json` pass: policy/prefix/secondary/known-4 timing, first-release 7/9, two-position guard, invalid result, unsupported contributor-dependent timing, V private known-4 twice/reset/error/teardown, W generic digit-entry/no-candidate/render/capacity, X bounded groups/secondary, arithmetic/freehand contracts and all four catalog selectors. Host/service/catalog/old exercise sources match the X commit after source-only CRLF/LF comparison. No historical test evidence was overwritten. Supplemental service tests are direct isolated tests, **not authoritative SDL input**.

Three earlier **disabled, no-input** provisioning attempts are retained: disabled-001 window startup race, disabled-002 terminal frontend stall, disabled-003 unsafe direct process-exit destructor failure. None recognized a stroke or staged an answer. The final implementation uses orderly frontend shutdown; disabled-004 and the single enabled session succeed. The direct-exit experiment is not retained in functional code.

## Reproduction and next authorization

```powershell
./tools/task_y/build.ps1
python tools/task_y/run.py --out local/task-y/disabled-NEW --disabled
python tools/task_y/run.py --out local/task-y/session-NEW
python tools/task_y/check.py --rom '../Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds' --code-snapshot local/task-u/session-003/before-mainram.bin
python tools/task_y/analyze.py --out local/task-y/session-NEW --disabled local/task-y/disabled-NEW --export docs/BrainAge_TaskY_Result.json
```

Only `NDS_TASK_Y_OUT` enables the fixed diagnostic plumbing; `NDS_TASK_Y_PUBLICATION=1` enables native capture/staging. These do not replace stable exercise selectors. All Task Y behavior is off without its variables. The experiment intentionally re-enables forced Tier-3 after the existing SDL bootstrap clears the inherited selector; the legacy Task O startup diagnostic still prints its earlier clearing operation. Compiled publication parity is **not claimed**.

Committed artifacts are ROM-free policy/source/tests/install/build/driver/analyzer/input metadata and this report/derived JSON. ROM, database/code bytes, saves/states, raw memory, binaries and screenshots remain ignored/local. No ROM or generated C was edited; no guest VRAM custom drawing, save/history/menu integration or optimization was added.

**Next smallest separately authorized task:** map and guard the first state-writing instruction in the original correctness consumer, then allow one invocation for this exact published 4 only as far as a verified decision **before score/count/phase/progression mutation**. Task Y supports designing that experiment; it does not yet authorize answer acceptance, completion, history or saves. No Task Z work is implemented here. Stop after Task Y.
