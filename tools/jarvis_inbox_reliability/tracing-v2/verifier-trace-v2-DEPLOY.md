# Verifier Tracing v2 — Deployment Handoff

## What this is

Enhanced per-candidate tracing for Jarvis Inbox V1's ChatGPT verifier,
per the senior's requirements (relayed 2026-10-11 ~04:13 EDT).

**Problem it solves:** seq 60's trace recorded `canonical_match: false`
for a new UUID but gave no way to determine WHY — no hashes, no lengths,
no mismatch location, no conversation identity. Cause: "E — insufficient
evidence." The next failure must be diagnosable from the trace alone,
without Graham acting as a visual proxy.

## Files in this package

| File | Purpose |
|------|---------|
| `verifier-trace-v2-DESIGN.md` | Field spec: the 12 required tracing fields |
| `extension/candidate_analysis.js` | Pure JS analysis functions (tested source of truth) |
| `extension/test_candidate_analysis.js` | 25 Node.js tests (all passing) |
| `verifier-trace-v2-content.patch` | Integration patch for `chatgpt_content.js` |
| `verifier-trace-v2-native.patch` | Allowlist patch for `jarvis_inbox_host.py` |
| `native-host/test_trace_v2.py` | 8 Python validation tests (all passing) |

## What changes (production, Windows)

1. **`bridge/inbox-v1/extension/chatgpt_content.js`**
   - Apply `verifier-trace-v2-content.patch`.
   - New build ID: `inbox-v1-trace2-20261011-01`.
   - The verification loop now computes SHA-256 for EVERY candidate
     (not just canonical matches) and records mismatch analysis.
   - Sample events carry `conv_id`, `conv_changed`, `is_branch`.
   - **Delivery logic unchanged:** same gates, same DELIVERED criteria,
     same NEEDS_REVIEW on ambiguity, same idempotency.

2. **`bridge/inbox-v1/native-host/jarvis_inbox_host.py`**
   - Apply `verifier-trace-v2-native.patch`.
   - `CANDIDATE_FIELDS` += 6 new fields; `TRACE_FIELDS` += 3 new fields.
   - New validation for `conv_id` (UUID format), `conv_changed`/`is_branch`
     (bool or null). All other bounds unchanged.

3. **Tests to run on Windows** (after patching):
   - `node bridge/inbox-v1/tests/test_content.js` (existing suite)
   - `node bridge/inbox-v1/tests/test_background.js` (existing suite)
   - `python bridge/inbox-v1/tests/test_trace.py` (existing suite)
   - Plus the new tests in this package.

## Deployment steps (Windows PC)

1. Apply both patches to the production files.
2. Run the existing + new test suites (all must pass).
3. Reload the Firefox extension via `about:debugging` (temporary add-on).
   - No bridge restart needed (native host patch is loaded on next
     native-messaging spawn; extension reload triggers reconnect).
   - No Firefox restart needed.
4. **Do NOT resend old seqs.** Let the next NATURAL delivery exercise
   the new tracing.

## Can this deploy without Graham doing anything?

**No.** The verifier runs on Graham's Windows PC (Firefox extension +
native host). This Linux VM cannot modify those files or reload the
extension. Deployment requires one of:
- (a) Graham applies the patches and reloads the extension himself, or
- (b) the senior creates a Codex infrastructure task (not a Brain Age task)
      to apply, test, and reload on Windows.

Recommended: (b) — a scoped Codex task with these patch files as input.

## Rollback

Revert both patches and reload the extension. The v1 trace format is
a strict subset; old and new trace files coexist (JSONL is append-only
and schemaless per line).

## What the next NEEDS_REVIEW will show

Instead of `canonical_match: false` with no explanation, the trace will
contain for the mismatched candidate:
- `expected_sha256` vs `observed_sha256` (were they even close?)
- `expected_len` vs `observed_len` vs `raw_len` (truncation? padding?)
- `mismatch_index` + `mismatch_window` (exactly which character differed,
  with codepoints to catch homoglyphs)
- `normalization` (was bubble/markdown fallback active?)
- `conv_id` / `conv_changed` / `is_branch` (did the page change?)

This is sufficient to distinguish: rendering artifacts, markdown
transformations, bubble fallback bugs, branch/rebind races, unrelated
messages, and true send failures — without visual inspection.
