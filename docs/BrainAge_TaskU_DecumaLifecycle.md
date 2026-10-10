# Task U - standalone Decuma session lifecycle proof

**FULL PASS for Policy A: an independently owned private-bus session at the compiled title boundary.** This is not a live Brain Age heap allocation or a production recognizer service. The runtime's existing reference ARM interpreter executed the original initializer, recognizer, metric accessor and context teardown against independently owned buffers, using a read-only snapshot of the live title code. No original Calculations constructor, worker, queue, resource loader or title allocator was invoked.

Authoritative evidence: `local/task-u/session-003`. Predecessor: `1ce9015c734c4d68af1d46015a05d2d22ae0eb94`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`.

## Original ownership map

Labels below are analytical, not recovered API symbols. Original manager/loader/worker ownership is **strongly supported statically**; the selected context-only init/recognize/teardown sequence is **proven dynamically**. Raw disassembly remains local. The map excludes unrelated exercise callers and library internals.

| Function/callsite | Purpose and inputs | Created storage / owner | Matching teardown | Required for direct session? | Evidence |
|---|---|---|---|---|---|
| 02027AAC/02027AB0 -> 020508F0 | allocate manager, size 0x238 | exercise+0xC24 | 02027A00 -> 020530B4, then 02027A08 -> 0205086C | No | Static |
| 02027AC0 -> 020531C8 | setup(manager, slot count=1) | manager-owned subsystem | 020530B4 | No; split out context-only init | Static + successful omission |
| 020531E0 -> 020508AC | allocate slots, count*0x370 | manager+4 | 020531AC -> 02050850 | No | Static |
| 020531F0 -> 02066124 | load(path, alignment=16) | database at manager+8 | 020531A4 -> 02050910 | Database bytes yes; this loader no | Static + private resource proof |
| 02053238 -> 020A3F08 | context size | returns 0x94E0+0xE70=0xA350 | n/a | Size required | Static |
| 02053240 -> 0205092C | allocate(size, alignment=4) | slot+0x1C context | conditional 02053180 -> 020A4440, then 02053188 -> 02050910 | Context required, title allocator not required | Static + dynamic |
| 0205324C -> 020508F0 | allocate 16-byte config | slot+0x20; database pointer at +0 | 02053158 -> 0205086C | Config required | Static + dynamic |
| 02053274 -> 020508F0 | allocate 0x30-byte alternate-mode config | slot+0x1C4; database at +0x24 | 02053150 -> 0205086C | No | Static + successful omission |
| 02053298 -> 020B541C; 020532A0 -> 0205092C | size 0x1290, alignment=4 | alternate-mode state at slot+0x204 | 02053160 -> 02050910 | No | Static + successful omission |
| 020532AC/020532B8 | point allocation 0x4000, descriptor allocation 0x100 | slot+0x208/+0x20C | 02053148/02053140 -> 02050850 | Equivalent input storage required | Static + dynamic |
| 020532C4/020532D0 | alternate point/descriptor allocations, same sizes | slot+0x1FC/+0x200 | 02053138/02053130 -> 02050850 | No | Static + successful omission |
| slot+0xE4/+0x104/+0x144 | embedded candidate groups/metric | part of slot, not separate original allocations | freed with slot | Equivalent output storage required | Task R/S + dynamic |
| 0205330C -> 02005EC8 | queue init, allocated 0x14-byte header, 16 entries at manager+0xA8 | global 020DC928 | stop message at 020530E0 -> 02005CD8; header free 02053104 -> 0205086C; global cleared 02053110 | No | Static + successful omission |
| 02053318 -> 0205092C | worker stack, 0x4000 bytes | manager+0xA4 | 020530F0 -> 02050910 | No | Static + successful omission |
| 02053344 -> 02005710; 0205334C -> 02005568 | thread create/start, object manager+0x10, entry 02051A30, priority 0x14 | manager | state check 0200566C, null queue message, join 02005680 before stack free | No | Static + successful omission |
| 020523E8 -> 020A447C | activate(context, config, 0x10, 1) for mode 0 | fills caller-owned context | 020A4440 validates then clears 0x94E0-byte prefix | Yes | Dynamic |
| 020A41A0 | incremental recognition with Task S ABI | mutates context and supplied outputs | retain across strokes, then context teardown | Yes | Dynamic |

The original worker receives messages at 02051A68 -> 02005D84 and returns on a null message at 02051A74..02051A7C. The matching manager teardown sends that null message and waits before freeing worker storage. The manager destructor does not free the outer manager object; the exercise destructor does that separately at 02027A08.

All observed title allocation/free wrappers resolve heap handle global **020DC924**, allocate target **0208B524**, free target **0208B4E8**. Original database loader **02066124** uses shared file object **020DCBF4**, obtains file length, allocates aligned storage, reads, checks read length, performs cache maintenance and closes the file. On read failure it frees the allocation and returns null. No reference-count contract was identified or assumed; the matching manager path explicitly frees its own database allocation.

These original manager/FS/worker paths were mapped, not exercised in Task U. Their global/allocator rollback is unnecessary for the selected design because none is called.

## Selected design and database ownership

Design A: no manager, no slot record, no worker, no queue, no live title heap allocation. `tools/task_u/isolated_session.h` defines one fixed sequence with four allowed entries: 020A447C, 020A41A0, 020A3FB8 and 020A4440. No externally supplied PC/register RPC, general guest-call service, new emulator, scheduler changes, ROM patch or generated-C edit is introduced.

The existing `armv4t::Interpreter::step` executes original live code through a small fail-closed `armv4t::Bus`. The bus owns independent host vectors mapped at private ARM address values. **These addresses do not designate borrowed live-game allocations.** A private write at 02200000 changes only the session's backing vector, not live DS RAM at 02200000. The live title cannot see any session pointer. This distinction is central to the proof and to any later integration design.

Read-only code/constants are snapshotted from live main RAM `[02000000,020D2BA0)` at the actual boundary. Data reads outside code/constants and declared session regions fail. Code/database writes, MMIO, coprocessor operations, SWIs, undefined/unsupported instructions and execution outside live title code fail closed. Each call has a ten-million-instruction cap and checks stack bounds, balanced return SP and r4-r11 preservation. Original calculation constructor, manager setup, answer submission and correctness entry PCs are explicitly forbidden.

The database is independently loaded by the ROM-free helper from the exact identity-checked ROM filesystem: `/data/Decuma/_databas_le.bin`, file ID 55, file offset **0x796E00**, length **113956**. Its bytes exactly match the database buffer in the preserved Task S snapshot. It is mapped read-only and released with the session; no guest FS object, refcount or singleton is touched.

| Private ARM address | Size | Owned use |
|---|---:|---|
| 02200000 | 0xA350 | fresh zeroed context |
| 0220B000 | 0x4000 | points |
| 0220F000 | 0x100 | descriptors |
| 0220F100 | 0x100 | candidate groups and metric |
| 0220F200 | 16 | config: database pointer, zero +4/+8, uint16 +12=159/+14=111 |
| 0220F300 | 8 | output counts |
| 02210000 | 0x8000 | private stack; SP=02217FC0 |
| 02220000 | 113956 | read-only database |

All backing regions are independent and non-overlapping. The config comes from the established mode-0 activation path: database pointer, zeros, and `255-96=159`, `255-144=111`; init arguments r2=16/r3=1. No Task S context bytes or pointers are copied.

## Initialization invariants and correction to the scan interpretation

Fresh initialization returns 0 and establishes context+94DC=context+94E0, context+94D0=database, context+94BC=16, context+94C0=1. The original validator is then executed within recognition and context teardown; both succeed.

The Task T scanner's `context[0]=context+84` and `context[2C]=context` describe the **observed post-recognition Task S state**, not a universal fresh-init invariant. A fresh valid context has a different internal list head. Task T already limited its negative scan to the mapped shape; Task U must not strengthen it into a universal absence proof. Its original constructor/lifecycle finding remains valid. The independently initialized context is functionally equivalent on the known glyph, not byte-identical to Task S's already-used context.

## Dynamic proof and execution semantics

Fresh disposable Training-menu restore, production custom host OFF. At compiled ARM9 **0204D790**, r0=41, LR=02050268, current/requested/selected=32/41/11, the opt-in diagnostic creates the private session synchronously. The existing host remains unchanged and inactive.

Task S `adapter.h` is reused directly, retaining coordinate/capacity validation. Source is exactly the specified deduplicated 5+3 point digit, stored as `(y,255-x)`. Descriptors encode `(5,0220B000)` and `(3,0220B014)`.

Recognition ABI: r0=02200000, r1=0220F000 then 0220F008, r2=0 then 1, r3=0220F100; stack arguments `16,0220F300,0220F120,16,0220F304`. Synthetic LR=02051AF8 is intercepted before fetching that guest instruction. This is the same actual target/ABI, **not** the original worker callsite. Metric accessor uses `(context,1,0,0220F140)`.

| Operation | Original target | Private interpreted instructions | Return | Candidate | Metric after accessor |
|---|---|---:|---:|---|---:|
| Initialize | 020A447C | 15069 | 0 | n/a | n/a |
| Stroke 0 | 020A41A0 | 636625 | 0 | 0032 / '2' | 500 |
| Metric 0 | 020A3FB8 | 120 | 0 | '2' retained | 500 |
| Stroke 1 | 020A41A0 | 1561105 | 0 | 0034 / '4' | 249 |
| Metric 1 | 020A3FB8 | 120 | 0 | '4' retained | 249 |
| Context teardown | 020A4440 | 13160 | 0 | output storage subsequently released | n/a |

Both recognition calls return group counts 0/1. Metrics are not called confidence. Context snapshots prove incremental state survives between calls. No recognition tuning, resampling alternatives or other glyphs were tested.

**Policy A:** private interpreter instructions are separately counted; they are not represented as physical DS cycle costs. No runtime scheduler/IRQ/device polling is invoked. The private bus has no MMIO or coprocessor implementation. Live guest counters are never overwritten or compensated.

Across the entire private session, before and after are identical:

- ARM9 runtime cycles: **2320143205**.
- ARM7 scheduler cycles: **1160071557**.
- ARM9/ARM7 instruction ordinals: **209065880 / 69096938**.
- Entire live ARM9 CPU structure: byte-identical, including banked state.
- All canonical 4 MiB main RAM: byte-identical; SHA-256 in JSON.

The ordinary original transition advances time only after the isolated session has been destroyed. No unrelated scene logic or peripheral execution occurs inside the private call interval.

## Teardown and continuation

Actual 020A4440 returns 0 and clears the complete 0x94E0 context prefix, verified byte-for-byte. The remaining context tail, config, input, output, stack, database and code snapshot backing vectors are then released through scoped C++ ownership. No title heap allocation was made, so no guest free call or allocator metadata rollback is needed. There is no guest queue/worker to cancel/join and no pointer published into pre-existing guest memory or CPU state. Full live RAM/CPU equality establishes absence of introduced reachable pointers and unchanged heap/global bytes. This is isolation and owned-storage destruction, not a blind RAM restore.

The saved lifecycle CPU was never changed. After session destruction, the original instruction resumes naturally exactly once. The existing observer records one compiled lifecycle entry; the diagnostic then stops before original rules initializer **020610B4** executes, with current/requested **41/41**, selected **11**. No calculation constructor, answer consumer or correctness logic runs. This is the smallest next-stage-entry continuation proof, not a full rules-screen or Back test.

## Attempts and safety

- `session-001`: initializer returned 0; an overly strict post-recognition-shape assertion stopped before any recognition. Private resources were released. No lifecycle/recognition behavior was tuned.
- `session-002`: init, the fixed glyph and teardown succeeded with live RAM/CPU/counters unchanged. The standard breakpoint missed the fallback rules entry; the observer recorded rules initialization once, but the driver hit its round bound and terminated. This run is not authoritative for final continuation/save capture.
- `session-003`: unchanged glyph/lifecycle calls; a narrow diagnostic stop catches the rules fallback entry. Complete authoritative result/save capture passes.

Authoritative logical save requests **0**, Flash commits **0**, changed save bytes **0**. Initial, live final and disk disposable Flash are equal:

`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

Canonical checkpoint/save and Task S evidence remain unchanged. No SDL/UI, custom-host activation, guest VRAM drawing, original answer, progression, menu addition or production service was introduced.

A tiny diagnostic-disabled run matches the preserved Task S disabled control in I/O/counters, all 4 MiB main RAM and save. The prior Task S and SDL executable hashes remain unchanged. Separate Task U runner SHA-256: `96c9c729c863684edda873f0496e6d00f9f3a713e3556a85d55aeee9226f95b6`.

## Artifacts and reproducibility

- `tools/task_u/isolated_session.h`: opt-in fixed lifecycle sequence/private bus and rules-entry stop.
- `install.py`, `build.ps1`: separate diagnostic installation/build in ignored local framework; production title headers untouched.
- `resource.py`: identity-gated extraction of the one database resource.
- `run.py`: disposable restore, normal compiled boundary, fixed session and bounded continuation.
- `analyze.py`: byte-level input/context/teardown/live-state/save audit; compact derived JSON export.
- `static_lifecycle.py`: narrow original ownership disassembly into new ignored local directories.
- Local: `local/task-u/session-001..003`, `static-001`, `static-002`, `disabled-001`, build logs.
- [Derived lifecycle evidence](BrainAge_TaskU_Lifecycle.json) contains per-call private-region hashes/changed-byte counts, calls, counters, resource/save hashes and continuation facts; no raw copyrighted memory/code.

Build requires the pinned local framework with existing Task S facilities. From repository root: run `tools/task_u/build.ps1`; `python tools/task_u/run.py --out local/task-u/<new>`; then `python tools/task_u/analyze.py --out local/task-u/<new> --export <derived-json>`. Use fresh evidence directories. Raw databases, RAM, states, saves and disassembly remain local/ignored.

## Scope and next step

The standalone lifecycle is proven for one known glyph and this title's exact code/database. It is enough to return to a bounded Task T-style integration **using the same private CPU/bus ownership model**, subject to service lifetime/error handling and native frontend tests. It does not prove creation/destruction in the live title heap, reuse of the original asynchronous worker, arbitrary symbols, production sampling, standalone reuse outside this title, custom results/save/history, or production service behavior. No next task or production integration was begun.
