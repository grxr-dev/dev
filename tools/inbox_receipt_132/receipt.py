"""Pinned owner attestation, not a browser ACK, retry, or Send authorization.

The caller must exclusively own the stopped bridge's existing instance lock.
InboxQueue remains the authoritative in-memory owner and atomic file writer.
No production source/seal or lane identity is changed by this maintenance tool.
"""
import copy
import hashlib
import json

TARGET = 'brainage-phase0-roundtrip-20261101-03:3b79f7b78f6ee7e8c4cb7b07f3c6d6f21ed3dc3d719ae1205dbdad22a6c8dc7e'
TEXT_SHA = '19ca24772ea0645dcebe6153402902ceaace06b34376c3f98b5b48cabbe7b71d'
FINGERPRINT = '45ee56ba2314c35fe2e1fba0fdf7a59849f38e510adf5215df9ca35e77ef1103'
IDENTITY = 'e7e72008cbecd2299a424f68d34ddf03e104cd8e65b9f86f01f3173160d6f852'
DEST = '6ae5615a-0720-83ea-a43b-82386ce031e5'
EPOCH = 'b2108916e5fb44098859a58e0252a2ad'
LANE = '90df5616a7c1490d9e8af8d1bb78dfb6'
SEAL = 'c6e78aa85c3f61d2eccaf82c8ee28fed7adccb9d7aca44d9634f60aab6418028'
UUID = 'c47dd71d-d0bc-433a-86fc-3ca4f85e94a4'
INCIDENT_SHA = 'd7736e1ce2d3745e89ba9f04c6ac32dd04ee1bca61e0ab438de5eca76c120b8b'
COMMENT = 6561497959
AUTHORITY_SHA = '78958784629c2c8144bd1b493ff3e9c856a03bbb2ad58e88ce77534e6070ac1d'
SEQUENCE, EXPECTED_LENGTH, OBSERVED_LENGTH, MISMATCH_INDEX, OBSERVATIONS = 132, 991, 1003, 991, 348


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def authority(record):
    if (record.get('id') != COMMENT or record.get('user', {}).get('login') != 'grxr-dev'
            or record.get('issue_url') != 'https://api.github.com/repos/grxr-dev/codex-relay/issues/45'
            or sha(record.get('body', '').encode()) != AUTHORITY_SHA):
        raise ValueError('pinned operator authority changed/unavailable')


def trace_proof(raw):
    if len(raw) > 2 * 1024 * 1024 or sha(raw) != INCIDENT_SHA:
        raise ValueError('retained incident fingerprint mismatch')
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    if not rows or any(x.get('delivery_id') != TARGET for x in rows):
        raise ValueError('incident identity mismatch')
    baseline = [x for x in rows if x['event'] == 'baseline']
    sends = [x for x in rows if x['event'] == 'send']
    if (len(baseline) != 1 or baseline[0].get('baseline_truncated') is not False
            or UUID in baseline[0].get('baseline_ids', []) or len(sends) != 1):
        raise ValueError('new UUID/one-Send evidence missing')
    if not any(x['event'] == 'start' and x.get('payload_sha256') == TEXT_SHA for x in rows):
        raise ValueError('incident payload identity mismatch')
    candidates = []
    for row in rows:
        if row['event'] not in ('baseline', 'sample', 'terminal'):
            continue
        if row.get('bound') is not True or row.get('conv_id') != DEST or row.get('conv_changed') is not False:
            raise ValueError('retained conversation context mismatch')
        for c in row.get('candidates', []):
            if c.get('uuid') == UUID:
                if (c.get('in_baseline') is not False or c.get('canonical_match') is not False
                        or c.get('normalization') != 'bubble' or c.get('expected_len') != EXPECTED_LENGTH
                        or c.get('observed_len') != OBSERVED_LENGTH or c.get('mismatch_index') != MISMATCH_INDEX):
                    raise ValueError('retained target mismatch differs from owner receipt scope')
                candidates.append(c)
    if len(candidates) != OBSERVATIONS or not any(x['event'] == 'ack_committed' and x.get('state') == 'NEEDS_REVIEW' for x in rows):
        raise ValueError('incomplete retained receipt evidence')
    return {'incident_sha256': INCIDENT_SHA, 'retained_user_turn_uuid': UUID,
            'candidate_observations': len(candidates), 'automated_canonical_match': False,
            'expected_normalized_length': EXPECTED_LENGTH, 'extracted_length': OBSERVED_LENGTH,
            'send_events': 1, 'conversation_id': DEST}


def scope(binding, lane):
    if ((binding.get('identity'), binding.get('conversation_id'), binding.get('generation'),
         binding.get('epoch'), binding.get('delivery_policy')) != (IDENTITY, DEST, 1, EPOCH, 'HOLD')
            or (lane.get('state'), lane.get('lane_id'), lane.get('seal'),
                lane.get('completion_cutoff'), lane.get('request_cutoff')) != ('ACTIVE', LANE, SEAL, 129, 129)
            or lane.get('binding') != binding):
        raise ValueError('stale binding/ACTIVE lane identity')


def reconcile(queue, did, expected_fingerprint, binding, lane, trusted_source,
              incident_raw, operator_record, *, exclusive=False):
    """One atomic queue commit with the original automated outcome retained verbatim.

    Existing schema's observed_sha256 slot is the *operator-attested logical text*
    checksum here, explicitly NOT a measured DOM hash. The original automated
    observed_sha256 (null), error, UUID fields and grant remain in automated_outcome.
    No send_count, composer or automatic UUID evidence is manufactured.
    """
    if not exclusive:
        raise ValueError('exclusive stopped-bridge instance ownership required')
    if did != TARGET or expected_fingerprint != FINGERPRINT:
        raise ValueError('only the pinned receipt/fingerprint is authorized')
    authority(operator_record)
    proof = trace_proof(incident_raw)
    scope(binding, lane)
    with queue.lock:
        if queue.fingerprint() != expected_fingerprint:
            raise ValueError('stale queue/replayed receipt; no mutation')
        e = queue._entries.get(did)
        if (not e or e['state'] != 'NEEDS_REVIEW' or e['attempt_count'] != 1
                or e['text_sha256'] != TEXT_SHA or sha(e['text'].encode()) != TEXT_SHA
                or e['delivered_at'] is not None or e['outcome'].get('state') != 'NEEDS_REVIEW'
                or e['outcome'].get('send_intent') is not True
                or 'operator_receipt' in e['outcome']):
            raise ValueError('unexpected terminal receipt state')
        if any(x['state'] == 'DELIVERING' for x in queue._entries.values()):
            raise ValueError('another delivery is active')
        grant = e['outcome'].get('_future', {})
        if (grant.get('binding') != binding or grant.get('lane') != lane
                or grant.get('source') != trusted_source or trusted_source.get('sequence') != SEQUENCE
                or trusted_source.get('request_id') != TARGET.rsplit(':', 1)[0]
                or grant.get('delivery_id') != TARGET or grant.get('text_sha256') != TEXT_SHA):
            raise ValueError('trusted completion/grant scope mismatch')
        entries = copy.deepcopy(queue._entries)
        new = entries[did]
        original = copy.deepcopy(e['outcome'])
        receipt = {'schema': 'inbox-operator-receipt/1',
                   'verification_method': 'operator_attested_receipt_not_automatic_browser_ack',
                   'authority_url': 'https://github.com/grxr-dev/codex-relay/issues/45#issuecomment-' + str(COMMENT),
                   'authority_body_sha256': AUTHORITY_SHA, 'at': queue.clock(),
                   'expected_queue_fingerprint': expected_fingerprint,
                   'binding_identity': IDENTITY, 'lane_id': LANE, 'lane_seal': SEAL,
                   'attested_logical_text_sha256': TEXT_SHA,
                   'observed_sha256_source': 'operator assertion of logical text receipt; NOT DOM extraction',
                   'retained_trace': proof, 'automated_outcome': original,
                   'previous_state': e['state'], 'previous_last_error': e['last_error'],
                   'previous_delivered_at': e['delivered_at']}
        new['outcome'].update(state='DELIVERED', observed_sha256=TEXT_SHA,
                              verification_method=receipt['verification_method'], operator_receipt=receipt)
        new.update(state='DELIVERED', delivered_at=receipt['at'], last_error=None)
        queue._validate_entry(did, new)
        # _commit fsyncs and replaces atomically, publishing memory only afterwards.
        # The receipt and original outcome are in this SAME commit, not a side log.
        queue._commit(entries)
        return {'delivery_id': did, 'state': new['state'], 'attempt_count': new['attempt_count'],
                'verification_method': receipt['verification_method'], 'send_permit_created': False,
                'prior_automated_outcome_preserved': True, 'receipt_comment': COMMENT,
                'queue_fingerprint_after': queue.fingerprint()}
