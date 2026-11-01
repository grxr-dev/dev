# Seq134: diagnosed; staged guard only, relay not restored

No Send, receipt, rearm, cursor change, production installation or restart occurred.
Seq134 remains NEEDS_REVIEW / attempt 1; seq135 remains unposted according to
Jarvis's independent report 6565187521. Historical HOLD remains intact.

## Exact evidence

Retained incident SHA-256:
`5afae75146153c079e04e1236f0ab891c14747cc38dce6be23fb44a9130cd367`.
Delivery identity and complete bounded timeline are in `SEQ134_RESULT.json`.

At 1793573925646 ms, baseline contained five stable UUIDs and was not truncated.
Send occurred at 1793573925906. New UUID
`acab8cd4-6871-49cd-b92a-93961f10a574` was observed 341 times, outside baseline,
in the correct unchanged bound conversation. Candidate source was **bubble**,
not raw-user-model. First failing delivery condition was canonical candidate
equality: expected normalized length 1243, observed 1255, first mismatch at
1243 (expected END, observed LF). Expected normalized hash:
`db367e3434db0a083fe163c44c5c07f41cc95da5ebcd9f5d2a7e78b8d2110802`;
observed hash:
`2cee5dddf813f882d7654c190be945c76dfa1d53f75c6fa6cfed054437cbdac8`.
The hash-equality stage was never reached because text equality failed.
Terminal deadline_expired: 1793574016092; native outcome: 1793574016150;
durable NEEDS_REVIEW ACK: 1793574016244. All timestamps are Unix milliseconds.

The queued payload itself is 1253 characters, SHA-256
`74b79d3c88d0b31883ebf253eb58c26c3bbe7fc0a9925963f210163e1f89ac6f`.
1243 is the existing inline-code rendering normalization, not its raw length.
No new canonicalization was introduced in this task.

Fresh no-send native/background/content probe
`16287157f125442e89350d62c0867814`, observed 1793574527715:

- Exactly one normal bound tab, content reachable, composer empty, not busy.
- Loaded proof build `inbox-raw-user-proof-20261101-01`.
- Target node_count=1; **model_unavailable**, raw hash and length null.
- Rendered length/hash exactly reproduce the retained failure.
- Privacy-minimized structure: DIV -> DIV -> (DIV, BUTTON), with button
  descendants. The full bubble is not an exclusively authored-text node.

Thus this failure is neither missing/virtualized target nor observed conversation
change nor unrelated-message selection. The installed React walker does **not**
provide an actual raw user model for this present Firefox node. Tests of synthetic
React objects cannot establish production availability.

The button's text and a post-exclusion subtree hash were not exposed by the
installed diagnostic. Consequently attribution of all 12 trailing characters to
that exact button is structurally supported, but not directly measured. Do not
invent the button label or claim a clean-subtree hash was verified.

Seq132 had the same 991 -> 1003 end mismatch. Seq133 differed: 1287 -> 1285,
mismatch 89, expected backtick versus observed `0` near a fence. Those older
nodes are now absent from mounted DOM (node_count=0). No scrolling was requested.
This guard does not claim to solve arbitrary Markdown/fence rendering.

## Narrow staged correction and recovery preparation

Only repository staging source changed, in
`tools/inbox_future/production/inbox-v1/extension/chatgpt_content.js`.
`authoredBubbleBody` selects a unique DIV content branch excluding sibling
interactive controls. Unknown/multiple content branches fail closed. It does
not trim a suffix, rewrite Markdown, infer a raw model, or change UUID/binding,
composer, single-Send, exact-comparison/hash, idempotency or no-resend gates.

`SEQ134_STAGED_SEAL.json` describes **hypothetical**, unapplied source/lane seals.
Installed identity remains `eb789679...`, lane seal `975fe745...`. The original
`SOURCE_SEAL.json` is the prior installed snapshot, not authority to install this
new candidate. Do not run the old #108/#110 installer against this staged tree.

`receipt134.py` reuses the atomic receipt kernel with the exact delivery, queue
fingerprint, incident, new UUID, current binding/lane and senior authority
#45/6565241702 pinned. The real retained proof and UTF-8-decoded authority were
validated. It is NOT applied and supplies no Send permit or runnable release
launcher. Any eventual use must recheck the fingerprint and hold the original
managed idle instance lock plus queue lock; preserve the failed automated record.

Releasing seq134 now could send135 under an unproven verifier. No such release
or unattended maintenance action was armed. Live bridge16660 owns this task.
The remaining blocker is positive live authored-subtree/raw-message proof before
coherent source/VM seal activation and extension reload. No new user action is
requested on the basis of these incomplete deployment prerequisites.

## Two notification paths

1. GitHub #45 is ChatGPT/Jarvis operational coordination, consumed by Jarvis's
   separate watcher. A comment/auto-ACK is not a ChatGPT input event.
2. Normal future results: durable completion/results -> VM future worker ->
   authenticated POST /chatgpt-inbox -> Windows future queue -> loopback18741 ->
   native host -> extension -> the already-open bound tab -> one Send -> positive
   verification -> durable ACK. This path creates the ChatGPT USER turn.

Installed Inbox API accepts only delivery_id/text; ACTIVE future eligibility
requires a trusted completion, so arbitrary diagnostic status is not silently
forwarded through that lane. No enabled alternate Jarvis-status-to-ChatGPT wake
path was found locally. Legacy browser courier is disabled; GitHub request
poller enabled. The old completion hook emits a worker-condition notification;
its code does not itself send to ChatGPT. VM source is not locally accessible;
Jarvis was asked directly in #45/6565291526 for read-only confirmation, not a Send.

## Focused checks

- `node tools/inbox_verifier_repair/test_bubble_boundary.js`: 8 PASS.
- `node tools/inbox_verifier_repair/test_model.js`: 12 PASS, synthetic model tests.
- `node tools/inbox_verifier_repair/test_probe.js`: 2 PASS.
- `python -B -m unittest discover -s tools/inbox_receipt_132 -p test_receipt.py -q`:
  9 PASS. All receipt mutations are temporary fixtures.
- Real read-only trace/authority/scope validation PASS; online receipt refused.
- Production binding/source load PASS; six protected state/config files matched
  across the final audit. Only no-send diagnostic request/results were written.
- All GitHub subprocesses created by this task used CREATE_NO_WINDOW. No GUI.

Classification: **PARTIAL — diagnosis and narrow staging complete; not deployed,
not automatically restored, no new automatic raw-model proof.**
