# Exact-one Inbox delivery — prepared post-turn deployment, NOT LIVE

**PARTIAL; not installed, not armed, no Send.** The source-seal migration and
owner launcher are now prepared; see **DEPLOY.md** for the single post-turn action.
The original issue96 implementation/evidence below is retained as historical context.
 This is a source overlay for the
existing bridge, not another service. Do not copy it over a running installation.
Do not release HOLD, repeat Jarvis's POST, or replay any historical delivery.
The migration is implemented/tested in fixtures; actual idle activation remains pending.

## Exact authority, not a synthetic flag

The sole supported delivery is:

`middleman-smoke-20261101-71c4fb280c:8715f59ac9710f1e355f50d284d3f2902d15a08470bdca4f7077a9a6fc004878`

Queued text SHA-256:
`1edebbb24c9c320d71a5c4d1369ccaa2e51c20e73d0a8ab157223b2679cac651`.
The delivery suffix hashes the original result, not the prefixed Inbox text.
Issue 95 comment 6554873031 and senior authorization 6554871278 were checked.
No request prefix, marker, arbitrary caller flag, or active-tab inference grants
authority. The explicit owner action is required even for this exact pinned item.

## Protocol

`inbox_one.py` uses the existing queue lock and atomic queue-file replacement.
Grant and claim cannot split across two stores. The grant freezes public binding
(ID/generation/epoch/full identity/HOLD), exact delivery and text hash, full queue
fingerprint at issuance, and canonical hash of *all other entries* plus existing
recovery/supersession records. It has an audit, integrity seal, random authorization
ID and 1..300-second lifetime. Local issuance uses the existing protected admin
token and loopback/Host/no-Origin/no-Referer guards; there is no remote arm API.

`ARMED -> CLAIMED -> SEND_INTENT -> FINISHED`, or unclaimed `REVOKED/EXPIRED`.
There is no rearm/delete/retry API. Claim increments this item's attempt once.
The existing native journal is flushed before forwarding. The browser background
and content must advertise the new capability in a fresh exact-binding no-send
receipt; every layer validates the same exact envelope and destination. A browser
readiness receipt is not delivery evidence.

Immediately before the sole existing `button.click()` site, content must obtain a
separate durable one-use Send permit through background -> native -> local queue.
The background validates extension sender and the active exact tab; the native
host supplies its own stored claim token. The queue records Send intent *before*
replying. Lost replies/disconnects never create a second permit or forwarding.
Expiry/navigation/composer changes prevent Send. A missing/ambiguous outcome is
NEEDS_REVIEW; even proven pre-Send failure consumes the single attempt.

DELIVERED still requires exact hash, one Send, one new stable USER UUID and an
actually empty composer. The UUID and authorization ID now join the durable ACK
evidence. A duplicate identical ACK is allowed for crash recovery of *this grant*
only; it never resends. Historical ACKs remain held. Exact known outcomes can be
recorded after expiry, but expiry never authorizes another Send. Revocation is
only legal before claim; after claim use review, not cancel-and-retry.

The original native recovery, generic queue and historical helpers are preserved.
Production local next/ACK do not fall back to an oldest-item claim when binding is
missing/malformed. Unknown grants and source mismatches fail closed.

## Supported owner commands after a separately reviewed coherent activation

**These commands are not presently installed in the live bridge.** No grant should
be armed until all loaded capabilities and fresh content readiness agree.

```powershell
python bridge/inbox-v1/exact_one.py status
python bridge/inbox-v1/binding.py request-readiness
python bridge/inbox-v1/exact_one.py arm --delivery-id middleman-smoke-20261101-71c4fb280c:8715f59ac9710f1e355f50d284d3f2902d15a08470bdca4f7077a9a6fc004878 --text-sha256 1edebbb24c9c320d71a5c4d1369ccaa2e51c20e73d0a8ab157223b2679cac651 --binding-identity <fresh-current-identity> --queue-fingerprint <fresh-status-fingerprint> --expires-in 120
python bridge/inbox-v1/exact_one.py revoke --authorization-id <exact-unclaimed-authorization-id>
```

The command verifies live exact-one capabilities before invoking the authenticated
local route. Missing capability, stale receipt or changed queue means no grant.
Do not put credentials in commands. No result POST or cursor operation is used.

## Concrete activation blocker / rollback

The current generation-1 binding's full identity includes eight component hashes,
including the three unconditional HOLD enforcers and the validator itself. Their
source cannot change while keeping that exact identity valid. This overlay also
binds the queue/API/local boundary/grant/wire/shared grant contract. A blind source
copy or hand-edit of the JSON would be an incompatible partial update. There is
currently no supported atomic source-upgrade/reseal control; `binding.py rebind`
is not one (it changes generation/epoch). We deliberately did not substitute an
identity, add an old-identity alias, loosen hashing, or install a second native host.

Next prerequisite: separately review/authorize a coordinated source-integrity
upgrade that keeps destination/generation1/epoch/HOLD/history, explicitly records
old/new source identity, invalidates stale readiness, provides rollback and uses
the idle post-turn managed restart. No helper or grant was armed in this task.
Bridge PID464 reported active throughout; its loaded code remains unchanged.

Backup: `dev/local/inbox-exact-one/backup/` contains the original eligible source
and held binding plus hashes; queue/journal/old hold were not overwritten or copied
into this repository. Since nothing was deployed, rollback now means discarding
the staged overlay, not writing any runtime file. After a future attempt, never
roll back the queue, claim, grant or journal to manufacture an unattempted state.
Source rollback must preserve the new grant/audit; an older queue schema rejects
it rather than safely erasing it. That activation/rollback integration is NOT
certified by this staged-only task.

Only after coherent idle activation: one browser action may be required, **Reload
the existing Jarvis Inbox V1 add-on** at `about:debugging#/runtime/this-firefox`,
then refresh the exact NEW tab. Do not load a second copy or click Send. Do not
reload now on the assumption that this staged code is deployed.

## Tests / evidence

```powershell
python -X utf8 dev/tools/inbox_exact_one/test_exact_one.py
node dev/tools/inbox_exact_one/test_exact_one.js
python -X utf8 dev/tools/inbox_exact_one/inspect_live.py
```

35 Python tests use the actual staged queue, API, readiness validator, native host,
and an ephemeral real local HTTP listener. 20 JS tests execute the actual staged
background/content/shared contracts against deterministic DOM/native fixtures.
These are NOT live Firefox delivery. No message is sent by these tests.

Negative cases include wrong IDs/hash/binding/generation/epoch; malformed or stale
grant; missing readiness/capability; unauthorized local caller; unrelated old work;
changed history; expiry/revoke; duplicate grant/claim/permit/ACK; crashes before/
after claim, before journaling, after ACK; reconnect/disconnect; wrong payload/UUID;
draft/composer/navigation; and missing/corrupt binding/queue. 33 existing held-mode
tests also passed against unchanged production. Total: 88 tests, no live send.

`inspect_live.py` is read-only and deliberately does not instantiate the queue
(constructor/get/count methods can mutate recovery). It reads only the authorized
item, hashes, aggregate counts and allowlisted health fields; it never calls next,
ACK, arm, POST Inbox, recovery or browser control.
