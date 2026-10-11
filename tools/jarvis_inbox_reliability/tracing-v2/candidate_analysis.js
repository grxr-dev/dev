/*
 * Jarvis Inbox V1 — enhanced candidate analysis (tracing v2).
 *
 * Pure functions for diagnosing canonical mismatches. No DOM access, no
 * network, no side effects. Designed to be integrated into the extension
 * content script's verification loop and fully testable under Node.js.
 *
 * Privacy: never returns full payload text. The mismatch window is bounded
 * (<=60 chars, JSON-escaped) and shows only a fragment around the first
 * difference. Hashes are one-way SHA-256. Lengths are integers.
 */

"use strict";

/**
 * Find the first index where two strings differ.
 * Returns -1 if equal, or the index of the first difference.
 * If one is a prefix of the other, returns the length of the shorter.
 */
function findFirstMismatch(a, b) {
  const len = Math.min(a.length, b.length);
  for (let i = 0; i < len; i++) {
    if (a[i] !== b[i]) return i;
  }
  return a.length === b.length ? -1 : len;
}

/**
 * Escape a string for safe inclusion in trace output.
 * Uses JSON string escaping (without surrounding quotes), which handles
 * control characters, quotes, and non-ASCII as \uXXXX.
 */
function escapeForTrace(s) {
  return JSON.stringify(s).slice(1, -1);
}

/**
 * Build a bounded context window around a mismatch index.
 * Shows up to `radius` chars on each side, escaped, hard-capped at 60 chars.
 * Format: "<before>⟦<a_char>≠<b_char>⟧<after>" — but using ASCII markers
 * for maximum compatibility: "[<a>!=<b>]".
 *
 * If mismatch_index is -1 (equal), returns "".
 */
function mismatchWindow(expected, observed, index, radius = 20) {
  if (index < 0) return "";
  const eStart = Math.max(0, index - radius);
  const oStart = Math.max(0, index - radius);
  const eCtx = expected.slice(eStart, index + radius);
  const oCtx = observed.slice(oStart, index + radius);
  const eChar = index < expected.length ? expected[index] : "<END>";
  const oChar = index < observed.length ? observed[index] : "<END>";
  // Show codepoints for the differing chars to disambiguate lookalikes.
  const eCp = index < expected.length
    ? "U+" + expected.codePointAt(index).toString(16).toUpperCase().padStart(4, "0")
    : "END";
  const oCp = index < observed.length
    ? "U+" + observed.codePointAt(index).toString(16).toUpperCase().padStart(4, "0")
    : "END";
  let window = `diff@${index}: ${eCp}!=${oCp} `;
  window += `exp[${eStart}..]:...${escapeForTrace(eCtx)}... `;
  window += `obs[${oStart}..]:...${escapeForTrace(oCtx)}...`;
  // Hard cap at 60 chars to satisfy native host validation (<=80).
  // The diff marker is first so it survives truncation.
  return window.length > 60 ? window.slice(0, 57) + "..." : window;
}

/**
 * Analyze a single candidate against the expected canonical text.
 *
 * @param {string} observedRaw - raw observed text (before canonicalization)
 * @param {string} observedCanonical - canonicalized observed text
 * @param {string} expectedCanonical - canonicalized expected text
 * @param {string} normalization - 'none' | 'bubble' | 'markdown'
 * @param {string} observedSha256 - hex SHA-256 of observedCanonical
 * @param {string} expectedSha256 - hex SHA-256 of expectedCanonical
 * @returns {object} analysis with the v2 tracing fields
 */
function analyzeCandidate(observedRaw, observedCanonical, expectedCanonical,
                          normalization, observedSha256, expectedSha256) {
  const mismatchIndex = findFirstMismatch(expectedCanonical, observedCanonical);
  return {
    expected_sha256: expectedSha256,
    observed_sha256: observedSha256,
    expected_len: expectedCanonical.length,
    observed_len: observedCanonical.length,
    raw_len: observedRaw != null ? observedRaw.length : null,
    mismatch_index: mismatchIndex,
    mismatch_window: mismatchWindow(expectedCanonical, observedCanonical,
                                    mismatchIndex),
    normalization: normalization || "none",
    canonical_match: mismatchIndex === -1,
  };
}

/**
 * Determine conversation identity signals for a sample.
 *
 * @param {string} boundId - the bound conversation ID (constant)
 * @param {string} currentId - conversation ID from URL at sample time
 * @param {string} initialId - conversation ID at baseline (first sample)
 * @param {boolean|null} branchDetected - true/false if branch DOM indicators
 *   were safely checked, null if detection was not attempted/possible
 * @returns {object} {conv_id, conv_changed, is_branch}
 */
function conversationSignals(boundId, currentId, initialId, branchDetected) {
  return {
    conv_id: currentId || null,
    // Changed if current differs from bound, or from initial baseline.
    conv_changed: currentId !== boundId || currentId !== initialId,
    is_branch: branchDetected == null ? null : !!branchDetected,
  };
}

// Export for Node.js testing; in the extension, these are globals.
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    findFirstMismatch,
    escapeForTrace,
    mismatchWindow,
    analyzeCandidate,
    conversationSignals,
  };
}
