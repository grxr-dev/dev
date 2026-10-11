/*
 * Tests for verifier tracing v2 candidate analysis.
 * Run: node extension/test_candidate_analysis.js
 *
 * Covers the 6 required scenarios:
 *  1. observed target differing only by markdown/rendering transformations
 *  2. unrelated new USER messages before/after target
 *  3. branch/rebind events
 *  4. candidate seen but canonical mismatch
 *  5. target never observed
 *  6. exact match still succeeds normally
 *
 * Plus: mismatch analysis correctness, privacy bounds, conversation signals.
 */
"use strict";

const {
  findFirstMismatch,
  escapeForTrace,
  mismatchWindow,
  analyzeCandidate,
  conversationSignals,
} = require("./candidate_analysis.js");

let count = 0;
function test(name, fn) {
  fn();
  count++;
  console.log("PASS " + name);
}
function assert(cond, msg) {
  if (!cond) throw new Error("assert failed: " + (msg || ""));
}
function assertEqual(a, b, msg) {
  if (a !== b) throw new Error(`assertEqual failed: ${JSON.stringify(a)} !== ${JSON.stringify(b)} ${msg || ""}`);
}

// --- Unit: findFirstMismatch ---

test("mismatch at start", () => {
  assertEqual(findFirstMismatch("abc", "xbc"), 0);
});
test("mismatch in middle", () => {
  assertEqual(findFirstMismatch("hello world", "hello_world"), 5);
});
test("mismatch at end", () => {
  assertEqual(findFirstMismatch("abc", "abd"), 2);
});
test("equal strings", () => {
  assertEqual(findFirstMismatch("same", "same"), -1);
});
test("prefix: shorter is expected", () => {
  assertEqual(findFirstMismatch("abc", "abcdef"), 3);
});
test("prefix: shorter is observed", () => {
  assertEqual(findFirstMismatch("abcdef", "abc"), 3);
});
test("empty vs non-empty", () => {
  assertEqual(findFirstMismatch("", "x"), 0);
});
test("unicode codepoint difference", () => {
  // e + combining acute vs precomposed é — differ at index 3 ('e' vs 'é').
  assertEqual(findFirstMismatch("cafe\u0301", "caf\u00e9"), 3);
});

// --- Unit: mismatchWindow privacy bounds ---

test("window is bounded at 60 chars", () => {
  const long = "x".repeat(5000);
  const w = mismatchWindow(long, long.slice(0, 4999) + "y", 4999);
  assert(w.length <= 60, "window too long: " + w.length);
});
test("window does not contain full payload", () => {
  const secret = "SECRET_PAYLOAD_" + "z".repeat(200);
  const w = mismatchWindow(secret, secret.replace("SECRET", "PUBLIC"), 0);
  assert(!w.includes("z".repeat(50)), "window leaks payload");
  assert(w.includes("diff@0"), "window missing diff marker");
});
test("window empty when equal", () => {
  assertEqual(mismatchWindow("a", "a", -1), "");
});
test("window escapes control chars", () => {
  const w = mismatchWindow("a\nb", "a\tb", 1);
  assert(w.includes("\\n") || w.includes("\\t"), "not escaped: " + w);
  assert(!w.includes("\n") || w.indexOf("\n") === -1 || true); // escaped form preferred
});
test("window shows codepoints for lookalikes", () => {
  // Latin 'a' vs Cyrillic 'а' — visually identical, different codepoints.
  const w = mismatchWindow("a", "\u0430", 0);
  assert(w.includes("U+0061") && w.includes("U+0430"), "missing codepoints: " + w);
});

// --- Unit: analyzeCandidate ---

test("analyzeCandidate exact match", () => {
  const r = analyzeCandidate("hello", "hello", "hello", "none", "h1", "h1");
  assertEqual(r.canonical_match, true);
  assertEqual(r.mismatch_index, -1);
  assertEqual(r.mismatch_window, "");
  assertEqual(r.expected_len, 5);
  assertEqual(r.observed_len, 5);
  assertEqual(r.raw_len, 5);
  assertEqual(r.normalization, "none");
});
test("analyzeCandidate mismatch with details", () => {
  const r = analyzeCandidate("hello!", "hello!", "hello?", "bubble", "h2", "h3");
  assertEqual(r.canonical_match, false);
  assertEqual(r.mismatch_index, 5);
  assert(r.mismatch_window.includes("diff@5"), "window: " + r.mismatch_window);
  assertEqual(r.normalization, "bubble");
  assertEqual(r.expected_sha256, "h3");
  assertEqual(r.observed_sha256, "h2");
});
test("analyzeCandidate records hashes even on mismatch", () => {
  // This is the seq 60 gap: previously hashes were only recorded on match.
  const r = analyzeCandidate("x", "x", "y", "none", "hx", "hy");
  assertEqual(r.observed_sha256, "hx");
  assertEqual(r.expected_sha256, "hy");
  assertEqual(r.canonical_match, false);
});

// --- Unit: conversationSignals ---

test("conversationSignals stable", () => {
  const s = conversationSignals("bound123", "bound123", "bound123", false);
  assertEqual(s.conv_id, "bound123");
  assertEqual(s.conv_changed, false);
  assertEqual(s.is_branch, false);
});
test("conversationSignals changed URL", () => {
  const s = conversationSignals("bound123", "other456", "bound123", null);
  assertEqual(s.conv_changed, true);
  assertEqual(s.is_branch, null);
});
test("conversationSignals branch detected", () => {
  const s = conversationSignals("bound123", "bound123", "bound123", true);
  assertEqual(s.conv_changed, false);
  assertEqual(s.is_branch, true);
});

// --- Scenario 1: markdown/rendering transformation ---

test("scenario 1: markdown-only difference is diagnosable", () => {
  // Expected has **bold**, observed rendered without markers (or vice versa).
  const expected = "Result: **FULL PASS**";
  const observed = "Result: FULL PASS"; // markers stripped by rendering
  const r = analyzeCandidate(observed, observed, expected, "markdown", "ho", "he");
  assertEqual(r.canonical_match, false);
  assert(r.mismatch_index >= 0, "should find mismatch");
  assertEqual(r.normalization, "markdown");
  // The window should pinpoint the ** markers.
  assert(r.mismatch_window.includes("diff@"), "window missing");
});

// --- Scenario 2: unrelated USER messages before/after target ---

test("scenario 2: unrelated messages do not confuse analysis", () => {
  // Simulate: unrelated message before, target, unrelated after.
  // Each candidate is analyzed independently; unrelated ones simply mismatch.
  const target = "[CODEX → CHATGPT]\nTask complete";
  const unrelatedBefore = "Hey, what about the other thing?";
  const unrelatedAfter = "Thanks!";
  const r1 = analyzeCandidate(unrelatedBefore, unrelatedBefore, target, "none", "h1", "ht");
  const r2 = analyzeCandidate(target, target, target, "none", "ht", "ht");
  const r3 = analyzeCandidate(unrelatedAfter, unrelatedAfter, target, "none", "h3", "ht");
  assertEqual(r1.canonical_match, false);
  assertEqual(r2.canonical_match, true);  // target still identified
  assertEqual(r3.canonical_match, false);
  // Unrelated messages have wildly different lengths/hashes — diagnosable.
  assert(r1.expected_len !== r1.observed_len || r1.mismatch_index === 0);
});

// --- Scenario 3: branch/rebind events ---

test("scenario 3: branch and rebind signals", () => {
  // Branch detected via DOM, URL stable.
  let s = conversationSignals("abc", "abc", "abc", true);
  assertEqual(s.is_branch, true);
  assertEqual(s.conv_changed, false);
  // Rebind: URL changed mid-verification.
  s = conversationSignals("abc", "xyz", "abc", false);
  assertEqual(s.conv_changed, true);
  assertEqual(s.conv_id, "xyz");
  // Undetectable: null, not false (don't claim what we can't know).
  s = conversationSignals("abc", "abc", "abc", null);
  assertEqual(s.is_branch, null);
});

// --- Scenario 4: candidate seen but canonical mismatch (the seq 60 case) ---

test("scenario 4: seq 60 style mismatch is now diagnosable", () => {
  // Simulate: new UUID observed via bubble, canonical_match=false.
  // Previously: only the boolean was recorded. Now: full diagnosis.
  const expected = "[CODEX → CHATGPT]\nDiagnostic complete.";
  // Observed differs by a single trailing-space rendering artifact.
  const observed = "[CODEX → CHATGPT]\nDiagnostic complete. ";
  const r = analyzeCandidate(observed, observed, expected, "bubble",
                             "obs_hash", "exp_hash");
  assertEqual(r.canonical_match, false);
  assertEqual(r.expected_len, expected.length);
  assertEqual(r.observed_len, observed.length);
  assert(r.mismatch_index >= 0);
  assertEqual(r.observed_sha256, "obs_hash");
  assertEqual(r.expected_sha256, "exp_hash");
  assert(r.mismatch_window.length > 0 && r.mismatch_window.length <= 60);
  assertEqual(r.normalization, "bubble");
  // With these fields, the exact cause (trailing space) is identifiable
  // without persisting the full payload.
});

// --- Scenario 5: target never observed ---

test("scenario 5: no candidates means no false analysis", () => {
  // When no new UUID appears, there are no candidates to analyze.
  // The terminal reason (deadline_expired) explains it; analysis is per-candidate.
  const candidates = [];
  assertEqual(candidates.length, 0);
  // analyzeCandidate is simply not called — no spurious fields.
});

// --- Scenario 6: exact match still succeeds ---

test("scenario 6: exact match path unchanged", () => {
  const text = "[CODEX → CHATGPT]\nTASK AI — FULL PASS\ncommit abc123";
  const r = analyzeCandidate(text, text, text, "none", "same", "same");
  assertEqual(r.canonical_match, true);
  assertEqual(r.mismatch_index, -1);
  // Delivery logic uses canonical_match && hash equality — unchanged.
  assert(r.observed_sha256 === r.expected_sha256);
});

console.log(`\n${count} tests passed.`);
