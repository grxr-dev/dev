"""Deterministic faults against the actual shared consumer and production modules."""
import copy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import subprocess
import threading
import http.client
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from continuity import Store, Poller, IntegrityError, digest, signal

REPO = 'grxr-dev/codex-relay'
BRIDGE = Path(__file__).resolve().parents[3] / 'bridge'
sys.path.insert(0, str(BRIDGE))


def issue(number=1, request_id='brainage-task-aw16-test', status='COMPLETED', text='synthetic only'):
    prompt = ('---\ncodex_relay_version: 1\nrequest_id: ' + request_id +
              '\nthread_key: main\nroute_id: sol-high\n---\nNO INFERENCE SYNTHETIC')
    body = ('---\ncodex_relay_result_version: 1\nrequest_id: ' + request_id +
            '\nroute_id: sol-high\nstatus: ' + status + '\nterminal_reason: test\nresult_sha256: ' +
            digest(text) + '\n---\n[CODEX \u2192 CHATGPT]\n' + text)
    return ({'number': number, 'title': '[CODEX RELAY] ' + request_id, 'body': prompt,
             'user': {'login': 'grxr-dev'}, 'created_at': f'2026-10-16T12:{number:02}:00Z'},
            {'id': number*100, 'body': body, 'user': {'login': 'grxr-dev'}})


class Client:
    def __init__(self, pairs):
        self.pairs = pairs
        self.error = None
        self.posts = []

    def private(self):
        if self.error:
            raise self.error

    def pages(self, path):
        if path.startswith('issues?'):
            return [pair[0] for pair in self.pairs]
        if path == 'issues/45/comments':
            return self.posts
        return [pair[1] for pair in self.pairs if str(pair[0]['number']) == path.split('/')[1]]

    def call(self, path, method='GET', data=None):
        if path == 'user':
            return {'login': 'grxr-dev'}
        row = {'id': len(self.posts)+700, 'body': data['body'], 'user': {'login': 'grxr-dev'}}
        self.posts.append(row)
        return row


class Faults(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'continuity.sqlite3'
        self.store = Store(self.path)
        self.client = Client([issue()])
        self.poller = Poller(self.store, self.client, REPO, 'grxr-dev')

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def poll(self, **kwargs):
        return self.poller.tick(**kwargs)

    def count(self, table='results'):
        return self.store.db.execute('SELECT count(*) FROM ' + table).fetchone()[0]

    def test_01_completions_404(self):
        value = self.poll(bridge='HTTP_404')
        self.assertEqual(value['result_count'], 1)
        self.assertTrue(value['workers']['github_poller']['continuity_healthy'])

    def test_02_bridge_unreachable(self):
        self.assertEqual(self.poll(bridge='CONNECTION_REFUSED')['result_count'], 1)

    def test_03_vm_path_lost_localhost_healthy(self):
        value = self.poll(bridge='WINDOWS_LOCAL_HEALTHY_REMOTE_TRANSPORT_ERROR')
        self.assertEqual(value['result_count'], 1)
        self.assertEqual(value['workers']['github_poller']['dependencies']['vm_to_host'], 'NOT_REQUIRED')

    def test_04_stale_pid_or_build(self):
        from reliability import assert_capability
        capability = {'schema': 'muse-capabilities/1', 'pid': 12, 'build_id': 'new',
                      'admin_loaded': True, 'admin_routes': ['operation']}
        assert_capability(capability, 'operation', 12, 'new')
        for field, value in [('pid', 11), ('build_id', 'old'), ('admin_loaded', False), ('admin_routes', [])]:
            bad = dict(capability, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                assert_capability(bad, 'operation', 12, 'new')

    def test_05_inbox_unavailable(self):
        value = self.poll(inbox='UNREACHABLE')
        self.assertTrue(value['workers']['github_poller']['inbox_delivery_degraded'])
        self.assertEqual(value['result_count'], 1)

    def test_06_needs_review_not_planning_barrier(self):
        self.poll(inbox='NEEDS_REVIEW')
        with self.store.db:
            result = self.store.scan(REPO, 'brainage-', paused=False, now=10**12)
        self.assertEqual(result['state'], 'SENIOR_REVIEW_REQUIRED')
        self.assertEqual(self.count('intents'), 1)

    def test_07_stale_control_not_planning_barrier(self):
        self.poll(inbox='STALE_QUEUED_WATCHDOG')
        for unused in range(3):
            with self.store.db:
                self.store.scan(REPO, 'brainage-', paused=False, now=10**12)
        self.assertEqual(self.count('intents'), 1)

    def test_08_duplicate_and_restart(self):
        self.poll()
        self.poll()
        self.store.close()
        self.store = Store(self.path)
        Poller(self.store, self.client, REPO, 'grxr-dev').tick()
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.count('receipts'), 1)

    def test_09_out_of_order_and_bridge_sequence(self):
        self.client.pairs = [issue(2, 'brainage-task-new')]
        self.poll()
        self.client.pairs += [issue(1, 'brainage-task-old')]
        self.poll()
        with self.store.db:
            self.store.enrich(REPO, 'brainage-task-new', 1)
            self.store.enrich(REPO, 'brainage-task-old', 999)
        self.assertEqual(self.count(), 2)
        self.assertEqual(self.store.snapshot()['local_high_water'], 2)
        self.assertEqual(self.store.scan(REPO, 'brainage-', paused=False, now=10**12)['parent'], 'brainage-task-new')

    def test_10_crash_between_fetch_and_commit(self):
        def crash():
            raise RuntimeError('simulated crash')
        with self.assertRaises(RuntimeError):
            self.poll(after_fetch=crash)
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.poll()['result_count'], 1)

    def test_11_corrupt_state_fails_closed(self):
        bad = Path(self.temp.name) / 'bad.db'
        bad.write_bytes(b'partial invalid state')
        with self.assertRaises(sqlite3.DatabaseError):
            Store(bad)
        self.assertTrue(Path(str(bad) + '.error.json').is_file())
        self.assertEqual(bad.read_bytes(), b'partial invalid state')

    def test_12_usage_limit_preserves_request_and_blocks_successor(self):
        self.client.pairs = [issue(status='USAGE_EXHAUSTED', text=json.dumps(
            {'error': {'codexErrorInfo': 'usageLimitExceeded', 'resetsAt': '2026-10-17T00:00:00Z'}}))]
        self.poll()
        retry = self.store.snapshot()['usage_retries'][0]
        self.assertEqual(retry['reset_at'], '2026-10-17T00:00:00Z')
        self.assertEqual(self.store.scan(REPO, 'brainage-', paused=False, now=10**12)['state'], 'RETRY_PENDING')
        self.assertIn('NO INFERENCE', self.store.db.execute('SELECT prompt FROM requests').fetchone()[0])

    def test_13_restoration_and_backfill(self):
        self.client.error = OSError('network down')
        with self.assertRaises(OSError):
            self.poll()
        self.assertEqual(self.store.snapshot()['workers']['github_poller']['state'], 'ERROR')
        self.client.error = None
        self.assertEqual(self.poll(bridge='HEALTHY', inbox='HEALTHY')['result_count'], 1)
        self.assertIsNone(self.store.snapshot()['workers']['github_poller']['last_error'])

    def test_14_aw16_intentional_pause(self):
        self.poll()
        self.assertEqual(self.store.scan(REPO, 'brainage-')['state'], 'INTENTIONAL_PAUSE')
        self.assertEqual(self.count('intents'), 0)
        from reliability import dispatch_paused
        self.assertTrue(dispatch_paused({'request_id': 'brainage-task-aw17-forbidden'}))
        self.assertFalse(dispatch_paused({'request_id': 'infra-only'}))

    def test_transaction_rollback_mid_commit(self):
        self.client.pairs += [issue(2, 'second')]
        with patch.object(self.store, 'assemble', side_effect=RuntimeError('crash inside transaction')):
            with self.assertRaises(RuntimeError):
                self.poll()
        self.assertEqual(self.count('requests'), 0)
        self.assertEqual(self.count('receipts'), 0)
        self.assertEqual(self.poll()['result_count'], 2)

    def test_real_production_result_wire_and_multipart(self):
        from relay_state import result_comments
        original = self.client.pairs[0][0]
        ident = original['title'][len('[CODEX RELAY] '):]
        row = {'request_id': ident, 'route_id': 'sol-high', 'state': 'COMPLETED', 'terminal_reason': 'completed'}
        text = 'wire \u96ea' * 12000
        bodies = result_comments(row, text)
        self.assertGreater(len(bodies), 2)
        with self.store.db:
            self.store.request(REPO, original)
            for number, body in enumerate(bodies):
                self.store.comment(REPO, ident, {'id': number+1, 'body': body})
            self.assertTrue(self.store.assemble(REPO, ident))
        self.assertEqual(self.store.db.execute('SELECT text FROM results').fetchone()[0], text)

    def test_changed_comment_or_hash_rejected(self):
        self.poll()
        self.client.pairs[0][1]['body'] += 'tamper'
        result = self.poll()
        self.assertEqual(result['workers']['github_poller']['quarantined'][0]['reason'], 'terminal_comment_edited')
        self.assertEqual(self.count(), 1)

    def test_conflicting_historical_request_does_not_starve_new_results(self):
        self.poll()
        historical, comment = copy.deepcopy(self.client.pairs[0])
        historical['number'] = 72
        historical['body'] += 'changed historical request'
        self.client.pairs += [(historical, comment), issue(3, 'brainage-task-current')]
        result = self.poll()
        self.assertEqual(self.count(), 2)
        self.assertEqual(result['workers']['github_poller']['state'], 'DEGRADED')
        self.assertEqual(result['workers']['github_poller']['quarantined'][0]['issue'], 72)
        self.assertEqual(self.count('quarantine'), 1)
        self.poll()
        self.assertEqual(self.count('quarantine'), 1)

    def test_exact_duplicate_comment_new_id_deduped(self):
        self.poll()
        self.client.pairs[0][1]['id'] += 1
        self.poll()
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.count('receipts'), 2)

    def test_direct45_uncertain_post_readback_no_resend(self):
        original = self.client.call
        def uncertain(*args):
            original(*args)
            raise TimeoutError('response lost')
        self.client.call = uncertain
        with self.assertRaises(TimeoutError):
            signal(self.store, self.client, REPO, 'synthetic', 'no inference')
        self.client.call = original
        signal(self.store, self.client, REPO, 'synthetic', 'no inference')
        self.assertEqual(len(self.client.posts), 1)

    def test_direct45_uncertain_absent_fails_closed(self):
        with self.store.db:
            self.store.db.execute("INSERT INTO signals VALUES('lost','[RELAY-CONTINUITY/1 lost]\nno inference','POSTING',NULL)")
        with self.assertRaises(IntegrityError):
            signal(self.store, self.client, REPO, 'lost', 'no inference')
        self.assertEqual(len(self.client.posts), 0)

    def test_production_usage_ledger(self):
        from completions import CompletionStore
        store = CompletionStore(Path(self.temp.name) / 'production.db')
        try:
            request = {'request_id': 'exhausted', 'thread_key': 'main', 'route_id': 'sol-high', 'message': 'preserved prompt'}
            store.ledger.intake(request, REPO, 1)
            store.finish(request, 503, {'status': 'failed', 'ok': False, 'response': '',
                'error': {'codexErrorInfo': 'usageLimitExceeded', 'resetsAt': 1792195200}})
            row = store.db.execute('SELECT * FROM usage_retry_intents').fetchone()
            self.assertEqual(row['state'], 'RETRY_WAIT')
            self.assertEqual(json.loads(row['request_json']), request)
        finally:
            store.close()

    def test_actual_usage_message_retains_reset_without_timezone_guess(self):
        from reliability import usage_reset
        error = {'codexErrorInfo': 'usageLimitExceeded', 'message': 'Usage limit; try again at Oct 16th, 2026 1:05 AM.'}
        self.assertEqual(usage_reset(error), ('Oct 16th, 2026 1:05 AM', 'RESET_ZONE_REQUIRED'))
        self.client.pairs = [issue(status='USAGE_EXHAUSTED', text=json.dumps({'error': error}))]
        self.poll()
        self.assertEqual(self.store.snapshot()['usage_retries'][0]['state'], 'RESET_ZONE_REQUIRED')

    def test_production_claim_skips_paused_without_losing_other_work(self):
        from completions import CompletionStore
        from reliability import dispatch_paused
        store = CompletionStore(Path(self.temp.name) / 'production.db')
        try:
            for number, ident in enumerate(('brainage-task-aw17-forbidden', 'infra-task'), 1):
                store.ledger.intake({'request_id': ident, 'thread_key': 'main', 'route_id': 'sol-high', 'message': 'test'}, REPO, number)
            self.assertEqual(store.ledger.claim(blocked=dispatch_paused)['request_id'], 'infra-task')
            self.assertEqual(store.ledger.get('brainage-task-aw17-forbidden')['state'], 'QUEUED')
        finally:
            store.close()

    def test_real_process_crash_uncommitted_transaction_recovers(self):
        code = ('import os,sys;from continuity import Store;store=Store(sys.argv[1]);'
                'store.db.execute("INSERT INTO intents VALUES(?,?,?,?)",("repo","parent","review","PENDING"));'
                'os._exit(23)')
        result = subprocess.run([sys.executable, '-X', 'utf8', '-c', code, str(self.path)],
                                cwd=Path(__file__).parent, check=False)
        self.assertEqual(result.returncode, 23)
        self.assertEqual(self.count('intents'), 0)
        self.assertEqual(self.poll()['result_count'], 1)

    def test_worker_health_persistence_and_corruption(self):
        from reliability import WorkerHealth
        path = Path(self.temp.name) / 'worker.json'
        worker = WorkerHealth(path)
        worker.record(state='HEALTHY')
        worker.record(error='network_down', state='DEGRADED')
        self.assertEqual(WorkerHealth(path).value['failures'], 1)
        worker.record(state='HEALTHY')
        self.assertIsNone(WorkerHealth(path).value['last_error'])
        path.write_text('{partial', encoding='utf-8')
        with self.assertRaises(ValueError):
            WorkerHealth(path)

    def test_actual_http_route_manifest_and_admin_isolation(self):
        from bridge import Server
        fake = SimpleNamespace(turn_lock=threading.Lock(), health=lambda: {'ok': True})
        server = Server(0, fake, 'synthetic-token')
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            connection.request('GET', '/health')
            response = connection.getresponse()
            capability = json.loads(response.read())['capabilities']
            self.assertEqual(response.status, 200)
            self.assertEqual(capability['schema'], 'muse-capabilities/1')
            self.assertFalse(capability['admin_loaded'])
            for route, status in [('/capabilities', 401), ('/local/inbox/admin/supersede-watchdog', 404)]:
                connection.request('GET', route)
                response = connection.getresponse()
                response.read()
                self.assertEqual(response.status, status)
            connection.close()
        finally:
            server.shutdown()
            server.server_close()

    def test_bridge_enrichment_invalid_or_conflicting_never_changes_order(self):
        self.poll()
        for invalid in (-1, 0, True):
            with self.assertRaises(IntegrityError):
                self.store.enrich(REPO, 'brainage-task-aw16-test', invalid)
        with self.store.db:
            self.store.enrich(REPO, 'brainage-task-aw16-test', 112)
        with self.assertRaises(IntegrityError):
            self.store.enrich(REPO, 'brainage-task-aw16-test', 113)
        self.assertEqual(self.store.snapshot()['local_high_water'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
