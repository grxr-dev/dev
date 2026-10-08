# Brain Age Task B: logical marker requester

Date: 2026-10-08. Result: **ARM9 0x0202FCC0 owns the marker write.**
Provisional description: marker-write requester. No original symbol name is claimed.
Scope ends here; no profile experiment or Task C was performed.

## Evidence and continuation

This continuation found tools/task_b, a route-helper modification, and the completed
local/task-b/route-001 capture already present and uncommitted. It inspected those
artifacts, independently re-ran all three auditors, strengthened the request auditor,
and checked the narrow static control flow against the exact SHA-1-gated ROM.
It did not launch another gameplay session. No nds_runner process remained running.
Task A and A.5 captures were preserved.

ROM SHA-1: b8a105bacc3234dede8d4465df0869f2b922a0e2.
Framework pin: 3a57236bb23d25dcb4caad7d58d733311062ff5e, with diagnostic edits.
The capture uses --force-tier3, fresh erased Flash, the unchanged Task A config,
450M passive cycles, two 134M waits, one raw (144,96) tap, and automatic waits.
It stops at the marker and has a zero-cycle stop checkpoint. No further input.

## Low-level anchor

SUPPORTED STATICALLY: ARM-mode leaf routine 0x038032A8..0x038032E8,
followed by literal words at 0x038032EC/0x038032F0. It loads a source pointer
from [r0+4], loads one byte into r2 at 0x038032B0, loads r1=0x040001A2,
and performs STRH r2,[r1] at 0x038032B8. It increments [r0+4], polls bit
0x80 of 0x040001A0, reads 0x040001A2, and returns with BX LR.
The pinned io.cpp maps these registers to AUXSPIDATA and AUXSPICNT.
There are no nested calls in this leaf.

PROVEN DYNAMICALLY: each of the sixteen Flash commits matches a snapshot at
0x038032B8 by CPU cycle and instruction ordinal, with r1=0x040001A2,
r2=the corresponding marker byte, [r0+4]=0x020D4F60+i, and LR=0x03803394.
The serializer 0x03803338 receives r0=0x020D4F60, r1=0, r2=16,
r3=0x038032A8; its indirect call is at 0x03803390.
The leaf is a byte-transfer primitive, not the logical save requester.

## Literal and provenance

Two ROM occurrences exist, both in the ARM9 image (file 0x4000 mapped at
0x02000000):

| ROM offset | Guest address | Aligned pointer-word xref |
| --- | --- | --- |
| 0xCA3A0 | 0x020C63A0 | 0x0202FE18 |
| 0xCA3B0 | 0x020C63B0 | 0x0202FD58 |

SUPPORTED STATICALLY: 0x0202FCD0 loads the second pointer through its literal
pool. The neighboring routine 0x0202FD60 loads the first copy and compares a
16-byte result against it; that alone does not establish its runtime role.
The pointer scan covers aligned exact words in the ARM9 image, not every
possible computed or unaligned reference. The ROM-to-RAM placement follows
header mapping; boot copying itself was not traced by this bounded observer.

PROVEN DYNAMICALLY: 0x0202FCC0 enters with r0=0. Its byte-load/copy loop
0x0202FCE0..0x0202FCF4 reads the second literal into stack 0x027E3AEC.
The stack contains all sixteen bytes before 0x0202FCF8. A buffer returned by
0x020508AC is 0x02102090; stores at 0x0202FD1C populate it with the marker.
Calling it heap allocation is a provisional interpretation; its allocation
implementation was not needed for attribution.

The requester computes (argument << 15)+0x180 at 0x0202FCCC/0x0202FCD8.
For the observed argument zero, 0x0202FD34 calls 0x0202FA08 with
r0=0x180, r1=0x02102090, r2=16. This directly associates literal, offset,
and length. No profile meaning is assigned to the index argument.

ARM9 staging routine 0x0200E008 calls copy routine 0x02007BB8 at
0x0200E044 with (0x02102090,0x020D4F60,16). Later ARM7 snapshots show the
complete marker at 0x020D4F60, immediately before serialization. All these
payload buffers are main RAM in the pinned bus mapping; 0x027E3AEC is a
main-RAM mirror. The staging buffer is ARM9-populated and ARM7-readable,
not ARM7 private RAM or the separate shared-WRAM region.

## Dynamic chain and IPC

All entries below have runtime register/PC snapshots and statically checked
call or dispatch instructions. Addresses are provisional routine identifiers.

1. ARM9 0x0202FCC0 -> call 0x0202FD34 -> 0x0202FA08.
   Arguments (0x180,0x02102090,16); wrapper LR=0x0202FD38.
2. ARM9 call 0x0202FA5C -> 0x0200DE78; same arguments, LR=0x0202FA60.
3. ARM9 0x0200DE78 -> 0x0200E008, observed LR=0x0200DF1C.
   Staging copy at 0x0200E044 supplies 0x020D4F60.
4. ARM9 stores request fields at 0x0200E060/70/7C and calls 0x0200E88C
   at 0x0200E080, with operation 7 and another argument 10. Do not equate
   that API argument with the SPI opcode merely because both are 10.
5. ARM9 0x0200E88C -> call 0x0200E938 -> FIFO encoder 0x02009124,
   arguments (11,7,1). At 0x020091B0 it writes 0x1EB to 0x04000188.
6. ARM7 FIFO dispatcher 0x037FE1D0 reads 0x04100000 at 0x037FE22C;
   the next snapshot at 0x037FE230 contains the same 0x1EB.
   Decode yields low five bits=11, bit five=1, upper bits=7.
7. ARM7 indirect call at 0x037FE27C enters 0x03802D6C with (11,7,1),
   LR=0x037FE280. At 0x03802D90 it stores operation 7 into state
   0x03809460+4; static subsequent code sets work flags and wakes a worker.
8. ARM7 worker dispatch 0x03802CF8 selects 0x03803A34 for operation 7.
   State 0x03809460 points to the shared request 0x020D4CE0.
9. ARM7 adapter 0x03803A34 loads request fields and tail-branches to
   0x03802F48 with (0x180,0x020D4F60,16), LR=0x03802CFC.
10. ARM7 write routine calls 0x03803150 at 0x03802FB0 with (0x180,0x0A).
    Header buffer observed at 0x038031E4 contains 0A 00 01 80.
    It is serialized through 0x03803338/0x038032A8.
11. ARM7 call 0x03802FC4 -> serializer 0x03803338 -> callback
    0x038032A8 -> 0x038032B8 -> sixteen accepted Flash commits.

Shared request 0x020D4CE0 fields, checked on both ARM9 and ARM7:
+0x0C=0x020D4F60 (payload), +0x10=0x180 (Flash offset), +0x14=16.
The operation FIFO word notifies a previously shared structure; it does not
carry the marker bytes or buffer pointer in this request. Initial registration
of that structure predates this bounded trace and was not traced. Both cores'
matching pointer/fields plus the actual adapter loads establish this handoff.

The worker boundary is asynchronous dispatch, not an invented direct call from
the FIFO callback. Static flag/wakeup control flow and dynamic operation-state,
dispatch-target, shared-pointer and argument correlation support that link.

## Ordering and validation

| Event | System cycle |
| --- | ---: |
| ARM9 requester entry | 438074239 |
| ARM9 marker-write call | 438074629 |
| ARM9 FIFO send | 438078834 |
| ARM7 post-FIFO-read snapshot | 438079007 |
| ARM7 callback | 438079041 |
| ARM7 worker dispatch | 438079535 |
| ARM7 write routine | 438079572 |
| SPI command store | 438080559 |
| First marker byte commit | 438081084 |
| Final NUL commit | 438082885 |

The auditor also checks monotonically ordered snapshot sequence values.
ARM9 system cycles are CPU cycles divided by two. All sixteen byte origins
match exact cycles and instruction ordinals, not merely nearby timestamps.

All auditors pass: analyze_request.py, Task A analyze_trace.py, and Task A.5
analyze_marker_route.py. The full 33,200-event Flash trace is byte-identical
to preserved A.5, including timing and origins. Transaction 1481, sequences
33185..33200, still apply. Replay equals the persisted 256 KiB save.
Flash SHA-256: 76eaf80dbffbe400daa53ddb00767519247a84a3ffcd7a554d2dece9a1854721.
Request trace: 4,288 snapshots, SHA-256
2370f6d3e65501614f8f5b77cc5d4e3b0d77b122a63992a537db2a46607d9c0c.

Remaining inference: original function names, full SDK API semantics, and the
broader meaning of the integrity marker. The requester and cross-core payload
handoff do not depend on those interpretations. Stop at 0x0202FCC0 because it
owns the constant, offset calculation, buffer construction and write request.

## Diagnostics and reproduction

ROM-free files: tools/task_b/{brainage_request_trace.h,install_diagnostics.py,
static_view.py,analyze_request.py}; route_marker.py adds --force-tier3.
The header observes pre-instruction interpreter state, arms at requester entry,
and stops after the marker transaction's final byte. It caps repeated PCs and
40,000 total snapshots; this is a bounded diagnostic, not a complete execution
trace. RAM reads use bus_debug_read8; no guest register or memory writes occur.
The installer adds the observer to tier3.cpp and a diagnostic-only stop flag to
the local Task A logger. No generated recompilation C is edited.

After the existing Task A reconstruction, install and rebuild:

```powershell
python tools/task_b/install_diagnostics.py
$env:PATH = "$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake --build build/task-a-runner --target nds_runner --parallel 2
$env:NDS_TASK_B_TRACE = "$PWD/local/task-b/route-NEW/request.jsonl"
```

Use Task A.5's documented route commands with a new local/task-b/route-NEW
output, adding --force-tier3 to the start command. Inspect menu before the
single tap, stop on marker, and never proceed into setup. Do not run Task A's
build wrapper afterward without reinstalling Task B: it copies its original
logger header over the Task B stop hook.

```powershell
python tools/task_b/analyze_request.py local/task-b/route-NEW --reference local/task-a5/route-001
python tools/task_a/analyze_trace.py local/task-b/route-NEW
python tools/task_a/analyze_marker_route.py local/task-b/route-NEW --before 02-menu
```

Local-only evidence remains in local/task-b/route-001: request.jsonl,
request-audit.json, flash.jsonl, trace-audit.json, marker-route-audit.json,
marker-transaction.jsonl, session.json, checkpoint summaries, saves and images.
ROM-derived disassembly is not checked in. No save semantics changed, no game
patches, no manual generated-C edits, no profile experiment, no Task C.
