# AW11 - lossless terminal binding and scheduler handoff

**PARTIAL.** The existing AW9 terminal observation is now losslessly committed:
all **411 scalars/five identities**, including the 322 missing from AW10's
projection. The exact canonical digest is reproduced independently in Python and
C++. A positive zero-guest early-yield/scheduler-tail certificate is **withheld**.
The existing return path redispatches B4; moreover, the recorded GPU-debt projection
cannot determine what the later GPU service will do. No guest instruction, replay,
runtime Brain Age MMIO, save/checkpoint access or mutation occurred.

## Authority, promotion and complete binding

AW10 `c699e3a21207abaa72b8130bf54c0f189c846412`; AW9
`fb3e417aa48cc70cc4c05f796263c9cf87b791af`; pinned ndsrecomp
`3a57236bb23d25dcb4caad7d58d733311062ff5e`. The unrelated subsequent Inbox commit
and untracked archive are preserved; no relay or approval infrastructure changes.

The missing values are **not inferred from a SHA-256 hash** or invented from a
synthetic default. AW10 explicitly identified promotion of existing authenticated
scalar metadata as the next work. `state.py` authenticates AW9's retained audit
against its committed SHA-256
`cfa3acc3e55bd2abf8504f662ded00ac4ea14c3fa617a89b9f3ae6fc0e545f8b`,
extracts only the existing final canonical observation, verifies its identity and
promotes its logical scalars/hashes. It does not read ROM, RAM images, checkpoint,
save, screenshot, native binary or game assets. No raw audit or canonical-hex dump
is committed. This makes the complete metadata available from **new committed
evidence**, rather than pretending all values were already in AW10's 89 cells.

`authenticate.py` independently verifies the historical 69-observation hash chain,
last accepted event (retired B0, index 68), no B4 observation, and exact equality
with AW8's authenticated reference states/events. The promoted terminal reproduces
the historical bytes exactly. Authentication is integrity binding to authoritative
project commits, not an external signature or new live observation.

`tools/task_aw11/terminal.json` contains schema/version, authority/provenance,
ordered `[name,width,value]` rows, ordered identity pairs and explicit getter
ownership for every field. The serializer is the existing **AW2S v1**:
`AW2S`, little-endian uint16 version 1, uint32 field count; per field uint16 ASCII
name length/name, uint8 width, little-endian unsigned value; then uint32 identity
count with uint16-length ASCII names/digests. Names are strictly sorted, unique;
widths are 1/2/4/8, range checked. No object padding, pointer or thread-ID bytes.

The **8,862 canonical bytes** reproduce
`ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526`.
All **89 AW10 cells match in name, width and value**; the other **322** are bound
without dropping any protected observation. The enclosing logical JSON metadata
identity also binds ownership/provenance independently of whitespace/line endings.

| Getter owner | Fields | Main contents / mutation sources |
|---|---:|---|
| Journal | 64 | six complete cap records, epoch/serial/ROM epoch; slice/reschedule journal |
| Runtime | 58 | registers/CPSR, clocks/ordinals, return stack, yield/fast/dispatch latches; Tier-3/runtime |
| Scheduler | 22 | stale slot/current ownership, round target/event/epoch, ARM7/debt, SPU/GPU projections |
| Bus | 84 | protected scalars, immutable RAM/DTCM identities, code/data/cache latches/maps |
| CP15 | 26 | control/cache/MPU/TCM mappings, generations and permission words |
| IO | 157 | divider, IRQ, DMA, every timer control/counter/reload/phase, device/periodic/save observations |

`terminal.json` enumerates every field; `owners` identifies the exact existing
getter source/function. Getter ownership is not a claim that only that module can
mutate a value. The five identities (ROM, RAM, DTCM, save, framework) retain their
original meaning. Native original `full_schema`, `journal_valid`, canonical
decode/re-encode and terminal identity checks accept the complete metadata.

This is the complete **existing AW2S observation**, not a full emulator savestate
or a restorable process. It does not magically add previously unobserved GPU/FIFO,
renderer, banked CPU or host-stack state. Any extra facts required for a new
transition must be captured/proven explicitly, not omitted from checking.

## Exact current boundary and control-flow proof

At recorded entry: PC B4, C=3416875777, cap=fast_limit=3416875778, CPSR=1F;
ordinal9=281098019, ARM7 C=1708437825/ordinal=96026779, parked debt=2/HALT=1.
All IRQ/event/terminal/DMA/stop readiness and hidden timing/cap/journal fields
remain exactly as bound. Yield hint remains **1**, neither cleared nor mistaken
for a Tier-3 pending-work predicate. The divider remains busy 8001, deadline
1708437913. B4/E1D100B0 still costs 8 and is inadmissible under the retained cap.

1. **Actual AW9 path:** the retired callback flushes/closes the audit and calls
   nonreturning `_Exit(73)`. There is no path "after disposal" back into Tier-3.
2. **Equivalent resumed boundary, ignoring no guard:** a separately owned harness
   would have to be established. Current `poll_after`/next `poll_exits` are false
   because C<fast_limit. Actual slice exhaustion has not occurred; prospective
   instruction non-admission is not the same predicate as clock exhaustion.
3. **Tier-3-only return/unwind:** `run_slice` restores unwind state, sees no
   terminal/DMA/HALT/event/expired-cap reason and redispatches B4 while C<cap.
   The original function body, on a scalar control-flow rail, proves two dispatch
   callbacks, the second intercepted before any guest function/fetch. An unwind
   flag or instruction-stop alone does not create a scheduler-round exit here.
4. An at-cap or event-break synthetic control can leave that loop, but those
   states differ from the bound entry and are rejected. No cycle burning, cap
   rewrite, fake event, ordinary halt, bank takeover or yield-hint normalization
   is installed. Existing AU/controller guards and terminal disposal stay intact.

The control-flow test initializes fresh synthetic objects at the recorded round
origin and stubs the already-running dispatch's return at the terminal clock.
It is **not** a restarted live `run_slice`, actual provider handoff or Brain Age
instruction execution. Re-entering a fresh live slice from stale `slot9.cycle`
would overwrite the live clock and is not certified.

## What an explicitly owned early return would face

The source order is: save ARM9 slot cycles/debt -> ARM9 timer tick -> GPU3D run ->
ARM7 catch-up/timers -> power-off check -> display -> SPU -> Wifi -> RTC -> system
events -> publish system timestamp -> later round chooses target -> new slice.
The old 69-event controller admits none of that tail; it already terminates.
A future task-specific phase/ownership transfer must prescribe and check the
allowed service observations, not silently disable the old observer or return
through its halt path. No such runtime escape/phase is installed in AW11.

Conditional scalar sub-results, **not a full scheduler certificate**:

- Saving unchanged ARM9 time gives rendezvous **1708437888**, not 1708437889.
  ARM7 is 63 system cycles behind. Its original HALT branch can consume those
  63 cycles without a guest instruction; its parked debt remains 2.
- Original timer bodies on the bound synthetic timer objects give timer0
  counter/phase **14558/62**, timer4 **50776/43**, timer5 **64195/39**. Both timer
  banks' last timestamps become 1708437888; no overflow/IRQ occurs in these
  isolated calculations. Disabled timers stay disabled. These are protected
  changes that a new tail ledger must model, not freeze or erase.
- If *all* intervening hidden service effects were proved inert, next deadlines
  would include divider **1708437913**, LCD **1708438374**, SPU **1708438528**,
  RTC **1708438848**. The normal selection relation could then choose target
  **3416875826**. That conditional arithmetic is **not a certified new cap**;
  no cap is set and B4 admission is not established.

## Concrete missing peripheral fact: GPU projection is non-injective

`scheduler_snapshot` records only `nds_gpu3d_cycles_to_run()` for GPU readiness.
Its actual `GPU3D::CyclesToRunFor` clamps negative CycleCount to zero and returns
CycleCount otherwise. Zero does **not** imply an empty FIFO/inert geometry engine.

The pinned original `GPU3D::Run` first checks GeometryEnabled, FlushRequest,
CmdPIPE emptiness and GXStat bit27. Otherwise it advances the hidden timestamp,
subtracts elapsed cycles and can call ExecuteCommand. None of those branch facts,
the raw timestamp/CycleCount or FIFO contents is encoded by `service.gpu_debt=0`.

The ROM-free source rail constructs two hidden GPU scalar objects with the same
observed debt **0**. One is disabled and returns without a command; another has
geometry enabled/nonempty pipe and reaches ExecuteCommand. Extracted original
getter/Run bodies yield **0 versus 1 command dispatch**, respectively. The command
implementation is a test stub; this proves differing branch eligibility, not any
particular actual command or that AW9 really had pending work. Both paths also
update a hidden GPU timestamp. Thus the 411-field tuple alone cannot justify a
unique complete scheduler-tail/service transcript. Even after adding a legal
early-yield token, those missing passive branch facts would still require proof.

## Focused tests and safety

`python -B tools/task_aw11/check.py --out local/task-aw11/certification-004`
and `python -B tools/task_aw11/authenticate.py` pass:

- **1,257 Python cases:** full serialization/identity, every field omitted and
  mutated, every ownership row altered, all identity classes, duplicate/reordered
  fields, version/endian/width/range/truncation, cap off-by-one, and missing/extra/
  duplicate/reordered scheduler phases or forbidden guest/MMIO/save/IRQ events.
- **1,260 native assertions:** original canonical/full-schema/journal checks;
  each of 411 missing/value/width changes rejected; stale epoch and every IRQ,
  ARM7, scheduler/device/timing observation remain protected by full identity;
  source-cost/cap rejection, original run_slice negative path, conditional HALT/
  timer evolution and the GPU ambiguity witness. No interpreter or runtime bus
  is linked/called. Service bodies operate only on isolated synthetic objects.
- Two full-binding disposal children: valid bound terminal exits **73**; an actual
  stale-epoch binding rejection exits **79**. Audit flush/close completes; no
  guest/scheduler/device/IRQ/ARM7/shutdown/persistence tail sentinel is reached.
- Historical AW9/AW8 **69 observations/full states/chains** authenticate exactly;
  no new replay or inference. Original source bodies, installed canonical/guard
  headers and all attempt/permission locks retain their recorded hashes.

Default observer remains null; no runtime installation, activation, source edit,
cap or timing semantic change is made. Generated source excerpts, native test
binaries and audits stay ignored. There are zero logical save requests, Flash
commits or changed save bytes attributable to AW11; no new live save measurement
is claimed. The historical save identity remains
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

## Decision and next safe task

`tools/task_aw11/certificate.json` is a **negative handoff decision plus positive
terminal-metadata binding**, not an executable scheduler or guest certificate.
`zero_guest_scheduler_handoff_certified=false`; `dynamic_execution_ready=false`.
No post-tail digest or positive new-slice state is fabricated. B4 fetch/account/
dispatch, status read, cap normalization and unmodeled service remain forbidden.

The smallest next task is separately authorized **ROM-free one-use diagnostic
early-yield ownership and a dominating pre-device fence**, with source/model
coupling through `run_slice`, preserving all AU guards and nonreturning failure.
Also define the minimal passive GPU branch/timestamp/FIFO observations required
before extending that fence through device service. Any missing historical values
must remain unknown; no positive full-tail/read certificate or live replay follows
from AW11. Stop before any new capture/execution authorization. Stopped after AW11.
