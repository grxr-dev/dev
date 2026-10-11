# Seq 55 bubble-only verification

Installed files: ../bridge/inbox-v1/extension/chatgpt_content.js and ../bridge/inbox-v1/tests/test_content.js. The exact incremental patch is committed in bubble-only.patch, following the existing unversioned-bridge artifact convention.

Make the user bubble text source explicit: a unique user-message markdown-tone descendant takes priority; with none, use the bubble itself and its canonical innerText. Multiple markdown sources fail closed. Nearest message-ids ancestor UUID remains the baseline/new-turn identity. Exact canonical payload/hash, stable samples, legacy compatibility and no resend are unchanged. No content child class is required.

Important limitation: the installed code before this change already used the bubble itself when no markdown-tone descendant existed. The supplied seq55 DOM therefore does not demonstrate a failing branch in that on-disk version. This change explicitly encodes and tests the requested rule; it does not establish the live root cause or prove deployed Firefox was running that version.

Focused tests: 34/34 content and 8/8 background passed. Added actual-discovery bubble-only formatted/Unicode payload delivery, unrelated bubble, existing baseline UUID with same payload, and multiple exact UUID ambiguity. Existing markdown DOM, delayed render, legacy and idempotency tests pass. No browser, smoke, queue, cursor or backend state operation performed.

Next: reload the installed temporary Firefox extension and bound tab, then separately verify the held seq55 path. Existing NEEDS_REVIEW is not automatically reclassified by a code reload; this patch does not authorize or perform a resend.
