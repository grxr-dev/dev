# AW13 - capture-only admission stopped before launch

**BLOCKED at the prerequisite gate. No live capture occurred.** The authorized
zero-guest terminal-to-fence transfer cannot be entered from an available,
already-authorized preserved runtime state. AW9 terminated nonreturningly; its
terminal observation is metadata, not a resumable process or full checkpoint.
AW13 expressly requires stopping if reaching entry requires a new prerequisite
replay. No replay, permit creation/reuse, runner launch, build, arming or retry
was performed.

## Authority and entry check

Repository branch `codex/brainage`; inspected HEAD and AW12 authority
`b60203a9d30b3a8536395aaacdd15d126ee88399`. AW9 authority remains
`fb3e417aa48cc70cc4c05f796263c9cf87b791af`. AW12 report/result/certificate were
read first; the current certificate matches its authoritative committed version.

The existing historical binding was independently validated using AW11's
logical serializer and authenticated AW9 audit, without running a guest or model
capture:

| Required entry property | Historical evidence | Live AW13 result |
|---|---|---|
| PC / last retired | `020019B4` / `020019B0` | No live sample |
| ARM9 cycle / retained cap | 3416875777 / 3416875778 | No live sample |
| Canonical terminal | 411 scalars, five identities, 8,862 bytes | Historical metadata verified only |
| Terminal SHA-256 | `ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526` | Exact historical match; not live admission |
| AW9 terminal process | PID 67860, recorded exit 73 | No active `nds_runner` process observed |
| One-shot authority | Remaining AW9 authorized runs = 0 | Consumed claims preserved |
| AW12 owner/frame/latch preconditions | Additional live observations required | Not sampled or armed |

AW9's retained `session.json` and authoritative result both record exit 73.
Its audit hash matches the committed value
`cfa3acc3e55bd2abf8504f662ded00ac4ea14c3fa617a89b9f3ae6fc0e545f8b`;
the last event is terminal disposal, and the last canonical observation matches
the full historical binding. A named process inventory observed zero runner
processes. No process was attached to, signaled, resumed or memory-inspected.

## Exact first blocker

**No trusted preserved terminal runtime is available in the authorized evidence
chain.** The read-only inventory of AW9's attempt directory identifies only
`source.state` as a `.state` file. AW9's launch source and recorded provenance
identify it as the earlier Task G source checkpoint, used before the historical
guarded AU gesture/replay; it is not a recorded terminal checkpoint. Its contents
were not opened or newly authenticated in AW13.

`tools/task_aw9/run.py` restores that earlier checkpoint, drives the historical
input path and executes the guarded 11-instruction/56-cycle prefix, including
five divider MMIO writes, before nonreturning disposal. Doing that again would
be a new prerequisite replay, not a zero-guest/zero-MMIO capture from an already
preserved terminal state. The old one-shot reservation, launch claim and runtime
permit claim are consumed. Their hashes still match AW12's protected evidence.

The 411-scalar fixture, canonical hash and RAM/DTCM fragments do not contain a
trusted resumable GPU/host-dispatch context. They cannot be injected as a live
provider snapshot, used to manufacture the missing context, or mistaken for a
checkpoint. The presence of the original permit file does not undo its existing
`.claimed` sidecar. No claim was deleted, rewritten, copied into a new ticket or
reused.

This is an authorization/state-availability blocker, not a newly discovered
failure of AW12's source-certified transfer. No safety predicate was weakened
and no live rejection/disposal exit code is fabricated.

## Capture, transcript and GPU disposition

- Prerequisite evaluation: **one**, not admitted before launch.
- Live capture attempts, launches, replays, retries: **zero**.
- Live ownership/fence transcript: **none**; ownership was not acquired/consumed.
- Escape-before-IRQ and pre-device-fence ordering: **not live-validated** in AW13.
- Live GPU readiness projection: **unavailable**. AW12's synthetic idle GPU
  witness is not substituted for live observations.
- No post-fence state or new cap was produced. B4 remains forbidden, and
  `dynamic_execution_ready=false` is unchanged.

## Safety and evidence

Zero Brain Age instructions, B4 fetch/account/dispatch, MMIO accesses, scheduler /
device / timer / GPU / IRQ / ARM7 service, save operations or Flash commits were
performed by AW13. These are consequences of **not launching or attaching to a
guest**, not a claimed successful runtime fence transcript. No ROM, save or
checkpoint contents were opened or mutated; no new live before/after save hash
comparison exists. Historical save identity remains the reference
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

Local read-only prerequisite evidence:

- `local/task-aw13/prerequisite-001/prerequisite.json`, SHA-256
  `f4a8ac4248865a852ab93f41df90b26a1f325d57f6c711c5d3a15604c8d813ae`.
- `local/task-aw13/prerequisite-001/process-inventory.json`, SHA-256
  `11c427287ac857c9242ac114682e58a03159f4b681b0bb7e3f03b12c5fff7f17`.

Checks passed: authoritative certificate comparison, lossless historical terminal
reconstruction, historical audit authentication/final-observation match, matching
recorded terminal exits, zero remaining AW9 runs, and unchanged consumed-claim
hashes. No native/controller suite was repeated or counted as live evidence.
Only metadata evidence and this report/result were created; prior source,
captures, checkpoints, permits and the unrelated untracked archive are preserved.

## Next safe task

A next scheduler-tail certification task is **not yet justified by new live
evidence**: AW13 did not obtain the missing GPU/ownership observations.

The prerequisite is separate explicit authorization with a fresh one-use permit
for the exact historical AU checkpoint/gesture replay **and** its already-
certified 11-instruction/56-cycle prefix, including five divider writes. Only
then may the AW12 owner capture the terminal-to-pre-device-fence interval, with
zero additional guest instructions/MMIO and nonreturning disposal before service.
Alternatively, a separately established trusted resumable terminal state must be
provided. No such replay, permit or state fabrication was implemented here.

No B4/status read, scheduler-tail continuation, new slice or retry is authorized.
Stopped after AW13's prerequisite rejection.
