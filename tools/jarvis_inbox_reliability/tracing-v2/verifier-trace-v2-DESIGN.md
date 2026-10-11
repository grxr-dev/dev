# Verifier Tracing v2 — Design

## Problem (from seq 60 / issue #37)

A new UUID was observed with `canonical_match: false`, but the trace recorded
only the boolean. It did not explain WHY the canonical texts differed:
no hashes, no lengths, no mismatch location, no conversation identity.
Cause classification: "E — insufficient evidence."

## Goal

For every newly observed USER candidate, record enough to explain a canonical
mismatch without persisting full payload text and without Graham acting as
a visual proxy.

## New candidate fields (per the 12 requirements)

| # | Requirement | Field | Type | Notes |
|---|-------------|-------|------|-------|
| 1 | stable UUID | `uuid` | string | existing |
| 2 | source type | `source` | string | existing: bubble/markdown-tone/legacy/synthetic |
| 3 | expected+observed canonical hash | `expected_sha256`, `observed_sha256` | string | NOW FOR ALL CANDIDATES (was only on match) |
| 4 | expected+observed canonical length | `expected_len`, `observed_len` | int | NEW |
| 5 | raw observed text length | `raw_len` | int | NEW (before canonicalization) |
| 6 | first canonical mismatch index | `mismatch_index` | int | NEW (-1 if equal) |
| 7 | escaped window around mismatch | `mismatch_window` | string | NEW (≤60 chars, JSON-escaped) |
| 8 | normalization used | `normalization` | string | NEW: 'none'/'bubble'/'markdown' |
| 9 | conversation ID / URL identity | `conv_id` | string | NEW (event level, per sample) |
| 10 | identity changed during verification | `conv_changed` | bool | NEW (event level) |
| 11 | branch vs canonical | `is_branch` | bool/null | NEW (event level, null if undetectable) |
| 12 | exact terminal reason | `reason` | string | existing (event level) |

## Privacy / safety guards

- `mismatch_window`: at most 20 chars each side of the mismatch index,
  JSON-escaped, hard-capped at 60 chars. Never the full payload.
- Hashes are SHA-256 (one-way); lengths are integers. No reversible content.
- `raw_len` is a length only, never text.
- Trace failures are swallowed (existing `verifierTrace` try/catch).
- All new fields fit the native host's 80-char string / primitive validation.

## Native host allowlist changes

`CANDIDATE_FIELDS` += `expected_len`, `observed_len`, `raw_len`,
`mismatch_index`, `mismatch_window`, `normalization`

`TRACE_FIELDS` += `conv_id`, `conv_changed`, `is_branch`

## Verification invariants (unchanged)

- stable UUID baseline; exact canonical+hash matching for DELIVERED
- deterministic delivery_id; idempotent re-POSTs; no blind resend
- unrelated new USER messages ignored; ambiguous → NEEDS_REVIEW
- tracing never affects delivery outcome (fire-and-forget, swallowed errors)
