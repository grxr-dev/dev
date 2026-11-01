"""Small deterministic maintenance-only suite; no production queue or network."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
import receipt as r

BRIDGE = Path(__file__).resolve().parents[3] / 'bridge'
sys.path.insert(0, str(BRIDGE))
from inbox_queue import InboxQueue


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.q = InboxQueue(Path(self.tmp.name) / 'inbox_future_queue.json', clock=lambda: 2000)
        self.text = 'ROM-free operator receipt fixture'
        self.binding = {'schema': 'test', 'identity': r.IDENTITY, 'conversation_id': r.DEST,
                        'generation': 1, 'epoch': r.EPOCH, 'delivery_policy': 'HOLD'}
        self.lane = {'state': 'ACTIVE', 'lane_id': r.LANE, 'seal': r.SEAL,
                     'completion_cutoff': 129, 'request_cutoff': 129, 'binding': self.binding}
        self.source = {'sequence': 132, 'request_id': r.TARGET.rsplit(':', 1)[0]}
        h = r.sha(self.text.encode())
        self.q.enqueue(r.TARGET, self.text)
        self.q.enqueue('other-historical-entry', 'must remain unchanged')
        self.q._entries[r.TARGET].update(state='NEEDS_REVIEW', attempt_count=1,
            claim_token='a' * 64, last_attempt_at=1000, last_error='original verifier deadline',
            outcome={'state': 'NEEDS_REVIEW', 'send_intent': True, 'observed_sha256': None,
                     'user_turn_uuid': None, 'error': 'original automated error',
                     '_future': {'binding': self.binding, 'lane': self.lane, 'source': self.source,
                                 'delivery_id': r.TARGET, 'text_sha256': h}})
        self.q._commit(copy.deepcopy(self.q._entries))
        self.before = copy.deepcopy(self.q._entries)
        self.operator = {'id': r.COMMENT, 'user': {'login': 'grxr-dev'},
                         'issue_url': 'https://api.github.com/repos/grxr-dev/codex-relay/issues/45',
                         'body': 'test explicit operator authorization'}
        base = {'delivery_id': r.TARGET, 'bound': True, 'conv_id': r.DEST, 'conv_changed': False}
        candidate = {'uuid': r.UUID, 'in_baseline': False, 'canonical_match': False,
                     'normalization': 'bubble', 'expected_len': 991, 'observed_len': 1003,
                     'mismatch_index': 991}
        rows = [dict(base, event='start', payload_sha256=h),
                dict(base, event='baseline', baseline_ids=['another-uuid'], baseline_truncated=False),
                dict(base, event='send')]
        rows += [dict(base, event='sample', candidates=[candidate]) for _ in range(348)]
        rows += [dict(base, event='terminal'), dict(base, event='ack_committed', state='NEEDS_REVIEW')]
        self.raw = '\n'.join(json.dumps(x) for x in rows).encode()
        self.patches = patch.multiple(r, TEXT_SHA=h, FINGERPRINT=self.q.fingerprint(),
                                      INCIDENT_SHA=r.sha(self.raw), AUTHORITY_SHA=r.sha(self.operator['body'].encode()))
        self.patches.start()
        self.addCleanup(self.patches.stop)

    def apply(self, **changes):
        args = dict(queue=self.q, did=r.TARGET, expected_fingerprint=r.FINGERPRINT,
                    binding=self.binding, lane=self.lane, trusted_source=self.source,
                    incident_raw=self.raw, operator_record=self.operator, exclusive=True)
        args.update(changes)
        return r.reconcile(**args)

    def test_receipt_is_atomic_preserves_history_other_entries_and_has_no_send_permit(self):
        historical = Path(self.tmp.name) / 'inbox_queue.json'
        historical.write_bytes(b'immutable unrelated history')
        before = historical.read_bytes()
        result = self.apply()
        e = self.q._entries[r.TARGET]
        self.assertEqual(e['state'], 'DELIVERED')
        self.assertEqual(e['attempt_count'], 1)
        self.assertEqual(e['claim_token'], self.before[r.TARGET]['claim_token'])
        self.assertEqual(e['outcome']['_future'], self.before[r.TARGET]['outcome']['_future'])
        self.assertEqual(e['outcome']['operator_receipt']['automated_outcome'], self.before[r.TARGET]['outcome'])
        self.assertIsNone(e['outcome']['user_turn_uuid'])
        self.assertFalse(result['send_permit_created'])
        self.assertEqual(self.q._entries['other-historical-entry'], self.before['other-historical-entry'])
        self.assertEqual(before, historical.read_bytes())
        reopened = InboxQueue(self.q.path)
        self.assertEqual(reopened._entries, self.q._entries)

    def test_mismatched_id_or_fingerprint_refused(self):
        for changes in ({'did': 'another-entry'}, {'expected_fingerprint': '0' * 64}):
            with self.assertRaises(ValueError):
                self.apply(**changes)
        self.assertEqual(self.before, self.q._entries)

    def test_replay_refused(self):
        self.apply()
        raw = self.q.path.read_bytes()
        with self.assertRaises(ValueError):
            self.apply()
        self.assertEqual(raw, self.q.path.read_bytes())

    def test_stale_binding_lane_and_source_refused(self):
        bad_binding = dict(self.binding, identity='0' * 64)
        for changes in ({'binding': bad_binding}, {'lane': dict(self.lane, seal='0' * 64)},
                        {'trusted_source': dict(self.source, sequence=133)}):
            with self.assertRaises(ValueError):
                self.apply(**changes)
        self.assertEqual(self.before, self.q._entries)

    def test_missing_or_changed_trace_authority_or_instance_ownership_refused(self):
        for changes in ({'incident_raw': b'{}'}, {'exclusive': False},
                        {'operator_record': dict(self.operator, body='unauthorized')}):
            with self.assertRaises(ValueError):
                self.apply(**changes)
        self.assertEqual(self.before, self.q._entries)

    def test_stale_queue_and_wrong_state_or_send_intent_refused(self):
        for field, value in (('state', 'QUEUED'), ('attempt_count', 2)):
            self.q._entries[r.TARGET][field] = value
            with patch.object(r, 'FINGERPRINT', self.q.fingerprint()):
                with self.assertRaises(ValueError):
                    self.apply()
            self.q._entries = copy.deepcopy(self.before)
        self.q._entries[r.TARGET]['outcome']['send_intent'] = False
        with patch.object(r, 'FINGERPRINT', self.q.fingerprint()):
            with self.assertRaises(ValueError):
                self.apply()

    def test_existing_production_send_permit_still_refuses_reconciled_entry(self):
        from inbox_future import FutureLane
        from inbox_queue import Conflict
        self.apply()
        lane = object.__new__(FutureLane)
        lane.q = self.q
        entry = self.q._entries[r.TARGET]
        lane.checked = lambda body: (entry, entry['outcome']['_future'])
        body = dict(delivery_id=r.TARGET, authorization_id='old-grant', claim_token='a' * 64,
                    text_sha256=r.TEXT_SHA, binding_identity=r.IDENTITY)
        with self.assertRaises(Conflict):
            lane.permit(body)

    def test_concurrent_calls_only_one_commit(self):
        def run(_):
            try:
                self.apply()
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(run, range(2))), 1)

    def test_failed_persistence_does_not_publish_or_mutate_state(self):
        raw = self.q.path.read_bytes()
        with patch.object(self.q, '_commit', side_effect=OSError('injected commit failure')):
            with self.assertRaises(OSError):
                self.apply()
        self.assertEqual(self.before, self.q._entries)
        self.assertEqual(raw, self.q.path.read_bytes())


if __name__ == '__main__':
    unittest.main()
