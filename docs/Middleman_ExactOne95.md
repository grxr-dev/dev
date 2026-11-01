# Middleman exact-one issue-95 delivery — PARTIAL

The exact queued result was verified against issue 95 terminal comment 6554873031.
There was no existing exact-one production authorization mechanism. A narrowly
pinned staged implementation and 55 contract tests were added under
`tools/inbox_exact_one/`; 33 existing no-send tests also passed.

No deployment or delivery occurred. The binding identity hashes the actual HOLD
enforcers. Source installation therefore requires an audited coherent source-seal
upgrade, not a global policy release or manual JSON replacement. This task stops
before that incompatible partial deployment, as requested. The live bridge also
owns this active turn and cannot be restarted safely from it.

Live: PID464; generation1; epoch `b2108916e5fb44098859a58e0252a2ad`; HOLD;
identity `376671cc6cefba6f6e5f95284f13b7a96deb912518a3a0032ae97845bd3493c3`.
The one authorized entry remains QUEUED, attempt0, no grant, no delivery timestamp.
The 66-entry queue, binding, native outcome journal and old no-send hold are byte
identical before/after. No VM cursor/queue writes or requests were made. Seq94/
cursor93 are not locally observable; the last Jarvis report says unchanged and a
fresh read-only confirmation was requested on issue45, comment6555113554.

The staged owner command binds exact delivery ID/text hash/current binding and
queue fingerprint; expiry is at most300seconds. Claim and grant consumption are
atomic. A separate durable one-use permit precedes the sole Send site. Other work
and historical ACK/recovery stay held. Reconnect/crash never re-forwards the item.
DELIVERED requires exact new USER UUID/hash, one Send and actual empty composer.

Remaining: review/install a compatible source-integrity upgrade with rollback and
idle post-turn activation; reload the existing extension only afterward; obtain a
fresh matching capability/recipient receipt; explicitly arm exactly the existing
item; observe delivery and obtain independent senior nonce confirmation. No helper
was armed. Do not POST issue95 again. No end-to-end PASS is claimed.

Brain Age remains paused. No credentials, permissions, model routes, VPN/firewall,
historical states, cursor, binding generation/epoch, or project semantics changed.


## Source-seal continuation (still PARTIAL, no live Send)

Reused all17 staged blobs unchanged and the authoritative88 tests. Added a pinned,
journaled source/seal installer and owner-invoked post-turn launcher;8 migration
cases and3 launcher guards passed. Runtime plan/backups are local-only under
`bridge/.runtime/inbox-seal-96/`. Same recipient/generation1/epoch/HOLD and protected
history are retained; new identity is derived from all reviewed component hashes.
No production file, seal, queue, journal or hold was changed. The existing test is
still QUEUED attempt0, grant absent. Nothing was scheduled/detached.

After this result publishes and bridge is idle, double-click
`C:\Users\rustg\Desktop\Commands\Middleman\Finish Exact One.cmd`.
See `tools/inbox_exact_one/DEPLOY.md` for exact safeguards, Reload/refresh prompt,
no-send readiness, one-use authorization, rollback and status. No live/end-to-end
PASS is claimed. Brain Age remains paused.
