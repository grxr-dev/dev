# Issue106: one pinned operator receipt, no Send

This is a maintenance command for seq132 only. It is **not executed by the Codex
turn** and is never scheduled. Production bridge/extension source remains byte
identical, so no source-seal migration, lane reactivation, browser reload or
credential change is needed. The recipient, generation, epoch, ACTIVE lane ID,
seal and both cutoffs remain exact.

## One owner action after the terminal result

Run from the Windows owner desktop:

```powershell
& 'C:\Users\rustg\Documents\Codex\Muse\dev\tools\inbox_receipt_132\Reconcile Seq132 Receipt.cmd'
```

The launcher rejects Codex ancestry, waits for this exact task's terminal result
to be published, requires no active/pending request, checks the pinned tray/bridge
ownership, and uses the existing managed `shutdown-if-idle` operation. It never
force-kills a process. If a new request wins the race, shutdown/maintenance fails
closed. After verified exit it acquires the **same instance byte lock** used by
the bridge before opening state. It then owns a normal `InboxQueue`, takes its
`RLock`, and performs one `_commit` (fsync + atomic replace + memory publication).
The existing tray owns normal restart. No second or parallel bridge is launched.

The command verifies the exact queue fingerprint, source files, binding, lane,
trusted SQLite completion132, operator comment6561497959's exact body hash and
retained trace hash/UUID. Any stale input stops without changing the queue.
The unrelated entries and protected historical files must be unchanged.

## Receipt evidence and schema compatibility

The disposition is `DELIVERED` **by explicit operator attestation**, not an
automatic browser hash match. `outcome.verification_method` and
`outcome.operator_receipt` make this distinction explicit. The existing queue
schema requires `observed_sha256` for any delivered entry; here that slot holds
the **operator-attested logical-text checksum**, with its source explicitly
labelled. It does not assert that the DOM extraction matched. The entire original
automated outcome (including its null observed hash, error, grant, Send intent and
UUID fields) is retained verbatim as `operator_receipt.automated_outcome` in the
same atomic commit. No browser UUID, composer evidence or Send count is invented.
The trace UUID is labelled retained trace evidence whose canonical match was false.

The original text, ID, claim token, attempt count1, original grant/source and Send
intent are preserved. The operation issues no Send permit. Existing permit code
still rejects the delivered state/consumed intent. Only the existing VM worker may
notice the receipt and advance its own future cursor normally. This command has
no cursor write, result post, rearm, recovery, ACK or browser API.

Runtime-only plan, bounded incident copy, forensic before-queue and completion
audit are in `bridge/.runtime/inbox-receipt-132/`. The queue receipt itself is the
atomic journal/commit marker. A crash after commit but before the side journal
cannot cause replay: the pinned fingerprint no longer matches. Read the target's
`operator_receipt`; **never restore the before-queue after a committed receipt**,
because later worker progress could otherwise be lost. Before commit a failure
leaves queue and production source unchanged; there is no source rollback to run.

## Focused checks

```powershell
python -B dev/tools/inbox_receipt_132/test_receipt.py -v
# Inert preparation only; records current task/process identities and file hashes:
python -B dev/tools/inbox_receipt_132/finish_receipt.py prepare
```

Nine tests cover atomic receipt/history and unrelated entries, wrong ID/fingerprint,
replay, stale identity/lane/source, missing authority/trace/instance ownership,
wrong terminal state/attempt/intent, concurrent invocation, failed persistence,
and refusal by the existing production Send-permit guard. No broad suite or
production Send is used.

## Prevention recommendation, separate from this recovery

Seq132's retained trace proves a new bound UUID observed348 times, a 991-character
normalized target versus a 1003-character extraction, with the first mismatch at
991 (`END` versus newline). It does **not** identify the trailing12 characters.
Capture the bounded trailing-node provenance of that bubble, then exclude only
the demonstrated non-message UI node from text extraction, with an actual DOM
fixture regression. Do not trim arbitrary suffixes, accept prefixes, or weaken
exact comparison. This recovery makes no verifier change and does not claim the
underlying extraction defect is fixed.
