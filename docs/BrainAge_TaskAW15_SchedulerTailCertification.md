# AW15 ? scheduler tail from the captured pre-device fence

**PARTIAL.** The exact AW14 fence is bound losslessly, the protected device-tail
effects are source-modeled, and the conditional next target is derived. A full
executable tail/new-slice certificate is **withheld**. The existing capture owner
still terminates at the fence; no continuation phase, permit, hook or runtime
behavior was installed or relaxed. `dynamic_execution_ready=false`.

No Brain Age execution/replay, B4 fetch/account/dispatch, runtime Brain Age MMIO,
ROM/save/checkpoint access or mutation occurred. Scalar test calls to copied
framework functions are not runtime Brain Age service or live evidence.

## Authority and entry binding

AW14: `9c2b342f4fdf1f09316ce7d62ac2240edc0f9589`; framework:
`3a57236bb23d25dcb4caad7d58d733311062ff5e`. The unrelated later Inbox commit
`266587717e8aa7159ea3e6726200b9258d94d135` and untracked Inbox ZIP are preserved.

`tools/task_aw14/fence.json` plus AW11's committed terminal metadata reconstruct
all **411 scalars and five identities**, with only the two certified AW12 changes:
`unwinding=1` and `slot9.cycle=3416875777`. AW2S v1 is logical sorted-name,
explicit-width, little-endian serialization, not padding or pointer identity.

- Core: 8,862 bytes; SHA-256
  `3528c2be122178850a3d3c78157cdd1adaf5409e5eb32f6d794e1c3f81d27d84`.
- Actual AW14 GPU extension: 19 scalars; SHA-256
  `708de6de2568d09123820267c9daaa7abd49321e90e275923ac93d96513ad5d4`.
- All eight ownership-chain records are independently recomputed, including
  ticket 1, frame 566, saved-latch/depth transitions and the final chain
  `10bad78f6ef2fd96a21b26be7e074943e6ded5fa5541844c731d3e39892472b4`.
- Architectural PC `020019B4`, ARM9 cycle **3416875777**, retained cap
  **3416875778**; ARM7 cycle **1708437825**, parked debt **2**, HALT **1**.

The metadata is not a complete emulator/process checkpoint or a fresh permit.

## Exact source path and device ordering

The unchanged `scheduler_run_round` tail after the AW12 fence is:

1. Scheduler device observer, then `nds_tick_timers(0, slot9.cycles)`.
2. `nds_gpu3d_run(slot9.cycles)`: facade ARM9Timestamp assignment, original
   `GPU3D::Run`, then one host diagnostic trace-ring append.
3. Rendezvous = actual ARM9 timestamp **shifted right by one**, **1708437888**.
4. `run_slice(1, 63)` followed by ARM7 timer catch-up; no CPU switch/dispatch
   is needed in the HALT/no-wake/no-DMA branch.
5. Power-off check.
6. Display ? SPU ? Wi-Fi ? RTC ? system events, in both profiling branches.
7. Publish `g_sys_timestamp=rendezvous`, then **`live_overlay_poll()`**.
8. Round-scope teardown; frontend's inner round loop may call the next round.
9. Next scheduler observer/round ? deadline selection ? ARM9 `run_slice` ?
   `nds_slice_begin` ? ordinary wake/dispatch logic. A future successor must
   stop before that last wake/dispatch portion, not rely on cap exhaustion.

Within system events, ordering is **AUXSPI ? SPI ? card ? divider ? sqrt**.
The old diagnostic observer sequence before the overlay poll would contain
five device observations and one ARM7 observation: scheduler-device,
ARM9-timer-device, ARM7-slice, ARM7-timer-device, RTC-device, system-device.
These are expected *service observations*, not six guest instructions.

### Source-derived protected effects, not live service

| Component | Exact projected result |
|---|---|
| ARM9 | Guest cycle/registers/NZCV/PC/ordinals remain unchanged |
| Timers | Both last timestamps become 1708437888; timer 0 counter/accum 14558/62, timer 4 50776/43, timer 5 64195/39; all others unchanged; no overflow/IRQ |
| GPU | GXStat remains `80000000`, empty queues, zero debt/work; facade ARM9Timestamp becomes 3416875777 and GPU Timestamp becomes 1708437888; no command execution |
| ARM7 | HALT fast branch advances slot cycle by 63 to 1708437888; debt 2 stays parked; no instruction, wake, IRQ acceptance or DMA |
| Power | Not powered off |
| Display | No HBlank, scanline or frame edge crossed; only display-last changes |
| SPU | Due mix count 1668396 already reached; no mix/capture/sample-memory work |
| Wi-Fi | Deadline MAX, so no callback; a present bridge/device updates its auxiliary CurrentSystemTimestamp, whereas a null bridge does not |
| RTC | Exact due formula `(((T+1)*32768)-1)/33513982` gives 1670410, already processed; no RTC callback |
| System events | Every deadline exceeds rendezvous; divider deadline 1708437913 remains pending; no completion or MMIO |
| Published system time | Becomes 1708437888; passive `service.rtc_due` becomes 1670410 |

There is no unconditional IRQ-acceptance step in this tail. Timer/display/event
branches that could raise IRQs are not eligible in the bound projection. The
ARM7 wake branch is independently negative-tested. GPU mode bits alone do not
cause a FIFO IRQ check in the admitted early-out Run path.

The full protected core projection immediately **before the overlay poll** has
SHA-256 `0630f8089b909b87bc51b501c614b423737ba7468ef7d4e86c4f7609bc3bd2c3`;
GPU extension `4283d85effe5028f12adbe1fe495174d9eda117d65f7accc0eb9e248f5b189d9`.
All 411 fields remain checked at every offline stage; five identities are fixed.
This is a source-model endpoint, **not an installed executable stop** or a claim
that unprojected bridge/host bookkeeping is bit-identical.

## Conditional new-slice arithmetic

If the tail has a valid successor owner and the remaining host/auxiliary
branches are bound or proven noninterfering, deadline selection from T=1708437888
gives divider **1708437913**, LCD **1708438374**, SPU **1708438528**, RTC
**1708438848**; other recorded event deadlines are MAX. ARM9 is not halted, so
the both-CPUs-HALT fast-forward branch is not taken. Normal planned T+64 is
1708437952; the event-within-seven-cycle-margin rule selects **1708437913**.

The conditional ARM9 target is **3416875826**, quantum **49**. Original
`nds_slice_begin`/`cap_note(source=0)` would produce:

- cap epoch **496?497**, global serial **506?507**, six cap records replaced
  by one; scheduler round epoch **1168?1169**;
- record base/cycle 3416875777, quantum 49, after 3416875826,
  `observed_before=3416875778`, canonical first-record `before=0`;
- `slice_cap=3416875826`, `slot9.target`/planned target match;
- `request_yield_poll`: fast limit **0**, hint **1**; no guest clock change;
- `unwinding` still **1** until the later ordinary fresh-dispatch clear.

The conditional canonical schema has **361 scalars**, not silently omitted
protection: the source explicitly replaces six ten-cell journal records with
one, while the complete predecessor remains bound. Conditional core hash:
`68b88b2de2264fb8fc456422de7aa026a8ac00685268f8cd8ea5650d3b01f773`.
The actual journal and original slice-begin function are tested on scalar
objects, not installed or run on Brain Age. This arithmetic is **not** an
executable certificate, a cap normalization, or authorization of B4.

## Smallest remaining certification blocker

**First edge:** `task_aw12::Controller::fence()` disposes nonreturningly. If its
stop were simply removed/returned from, the first device observation would
reach the already-complete AW7 ledger and fail `cursor < plan->size()`. Its
guest guard also still forbids any fresh dispatch. No audited successor phase
currently transfers these owners to a tail/new-slice ledger. Removing observers
or reopening the old permit is not a solution and was not done here.

**Remaining binding obligation:** the terminal core/GPU projection does not
seal the final overlay-poll branch or nullable Wi-Fi bridge timestamp branch.
The original overlay poll can reach bank publication when enabled/due; its
enable/countdown state is absent from this fence projection. The native rail
demonstrates distinct branches under the same recorded core/GPU projection.
This is **not** evidence that AW14 actually enabled or ran the overlay: its
archived argv suggests disabled operation. A future admission must bind that
source-grounded setup fact immutably, observe it passively, or prove the branch
noninterfering; a guessed default is not an exact-state receipt. GPU trace-ring
bookkeeping likewise needs an explicit auxiliary/noninterference disposition,
not a claim that the entire GPU object is unchanged.

Therefore no complete tail/new-slice or guest re-entry certificate is issued.
The architectural next PC remains **020019B4**; no dispatch there is certified.
Under the retained old cap its eight-cycle LDRH still overruns by **7**.

## Tests, disabled behavior and limits

Final focused evidence: `local/task-aw15/certification-007/`.

- **1,398 Python cases:** every core/GPU field mutation/omission/width, all five
  identity classes, full protected stage evolution, stale epochs/serials,
  cap off-by-one, chain tamper, skipped/duplicate/reordered/missing/extra events,
  mid-stage readiness changes and forbidden B4/MMIO/service events.
- **29 native assertions:** original timer, HALT, GPU, SPU, Wi-Fi, RTC, system
  event, slice-begin and cap-journal code on bounded scalar objects; both exact
  no-work paths and independently changed readiness witnesses.
- **Two model disposal children**, exits 73/79: audit flush/close + `_Exit`;
  no scheduler/device/IRQ/ARM7/shutdown/persistence sentinel afterward. These are
  model-disposal tests, **not complete live successor-owner coupling**.
- Source fragments match the AW14 archived native bodies; periodic/overlay
  bodies also match the pinned framework Git source. AW11 source/guard identity
  checks are retained. No generated recomp C or ROM-derived image is involved.
- No runtime file changed. Default observer remains null; original disabled
  run_slice still redispatches under the one-cycle-margin cap in a source rail.
  All old ownership, evidence and consumed-permit metadata remain unchanged.

The 14 model stages are not a newly observed 69-event guest transcript. No
interpreter/real bus is linked. Historical save SHA-256 remains
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`;
there is no fresh save measurement or fabricated runtime continuation.

**Next safe task:** ROM-free, guarded successor-owner/ledger and actual-interface
certification from this exact fence through a new-slice pre-dispatch fence.
Bind or prove noninterference of the auxiliary branches, keep original receipts
dominating, validate all expected service/journal/round transitions, then dispose
before B4 fetch/account/dispatch. No live replay/status read is justified yet.

Stopped after AW15.
