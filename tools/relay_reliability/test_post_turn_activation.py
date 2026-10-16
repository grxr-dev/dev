"""No production shutdown, task registration, admin POST or GitHub writes in tests."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import hashlib
import os
from unittest.mock import patch

import post_turn_activation as activation


def fixture():
    plan = {'old': {'pid': 10, 'ticks': 100}, 'tray': {'pid': 20, 'ticks': 200},
            'old_health_started_at': 1000, 'turn_id': 'exact-turn', 'deadline': 1000,
            'modules': {'module': 'digest'}, 'build_id': 'expected-build', 'routes': {'GET': ['/health']}}
    health = {'bridge_pid': 10, 'bridge_started_at': 1000, 'bridge_source_sha256': activation.OLD_SOURCE,
              'turn_active': False, 'active_async_request': None, 'maintenance_active': False,
              'human_review_required': False, 'relay_ready': True}
    sample = {'request': {'codex_turn_id': 'exact-turn', 'terminal_at': 'terminal', 'state': 'COMPLETED'},
              'active': [], 'pending': 0, 'outbox': [{'state': 'CLOSED', 'comment_id': 55}]}
    return plan, health, sample


class Admission(unittest.TestCase):
    def test_exact_positive(self):
        self.assertIsNone(activation.idle_reason(*fixture()))

    def test_every_required_idle_guard_independently(self):
        plan, health, sample = fixture()
        mutations = [('health', 'bridge_pid', 11), ('health', 'bridge_started_at', 999),
            ('health', 'bridge_source_sha256', 'other'), ('health', 'turn_active', True),
            ('health', 'active_async_request', {'request_id': 'other'}), ('health', 'maintenance_active', True),
            ('health', 'human_review_required', True), ('health', 'relay_ready', False),
            ('sample', 'request', None), ('sample', 'active', [{'request_id': 'other'}]),
            ('sample', 'pending', 1), ('sample', 'outbox', []),
            ('sample', 'outbox', [{'state': 'POSTING', 'comment_id': None}])]
        for which, name, value in mutations:
            with self.subTest(which=which, name=name):
                changed_health, changed_sample = copy.deepcopy(health), copy.deepcopy(sample)
                (changed_health if which == 'health' else changed_sample)[name] = value
                self.assertIsNotNone(activation.idle_reason(plan, changed_health, changed_sample))
        for name, value in [('codex_turn_id', 'other'), ('terminal_at', None), ('state', 'USAGE_EXHAUSTED')]:
            with self.subTest(request=name):
                changed = copy.deepcopy(sample)
                changed['request'][name] = value
                self.assertIsNotNone(activation.idle_reason(plan, health, changed))

    def test_new_capability_requires_all_fields(self):
        plan, unused, sample = fixture()
        capability = {'schema': 'muse-capabilities/1', 'loaded_modules': plan['modules'], 'pid': 11,
            'build_id': plan['build_id'], 'bind': {'relay': ['127.0.0.1', 8766], 'inbox': ['127.0.0.1', 18741]},
            'admin_loaded': True, 'admin_routes': ['/local/inbox/admin/supersede-watchdog'], 'routes': plan['routes']}
        health = {'bridge_pid': 11, 'bridge_started_at': 1001, 'capabilities': capability,
                  'relay_ready': True, 'relay_v2': {'browser_enabled': False}}
        self.assertEqual(activation.validate_capability(plan, health), capability)
        for name, value in [('schema', 'old'), ('loaded_modules', {}), ('pid', 10), ('build_id', 'old'),
                            ('bind', {}), ('admin_loaded', False), ('admin_routes', []), ('routes', {})]:
            with self.subTest(capability=name):
                changed = copy.deepcopy(health)
                changed['capabilities'][name] = value
                with self.assertRaises(RuntimeError):
                    activation.validate_capability(plan, changed)


class Handoff(unittest.TestCase):
    def simulate(self, busy_race=False, never_idle=False, wrong_source=False):
        plan, health, sample = fixture()
        clock = [0]
        operations = []
        state = {}
        race_until = [0]
        def now():
            return clock[0]
        def sleep(seconds):
            clock[0] += seconds
        def observe():
            value = copy.deepcopy(health)
            value['turn_active'] = never_idle or clock[0] < race_until[0]
            if wrong_source:
                value['bridge_source_sha256'] = 'wrong'
            return value
        def invoke(unused_plan, mode):
            self.assertFalse(observe()['turn_active'])
            operations.append((mode, clock[0]))
            if mode == 'shutdown-if-idle' and busy_race and sum(item[0] == mode for item in operations) == 1:
                race_until[0] = clock[0] + 8
            return {'operation': mode}
        def exited(unused_pid, unused_ticks):
            commands = sum(item[0] == 'shutdown-if-idle' for item in operations)
            return commands >= (2 if busy_race else 1)
        with patch.object(activation, 'http', side_effect=observe), patch.object(activation, 'database_sample', return_value=sample), \
             patch.object(activation, 'validate_sources'), patch.object(activation, 'process', side_effect=lambda pid: plan['old'] if pid == 10 else plan['tray']), \
             patch.object(activation, 'native', side_effect=invoke), patch.object(activation, 'process_exited', side_effect=exited), \
             patch.object(activation, 'record', side_effect=lambda value, phase, **fields: value.update(phase=phase, **fields)), \
             patch.object(activation.time, 'time', side_effect=now), patch.object(activation.time, 'sleep', side_effect=sleep):
            try:
                activation.wait_and_shutdown(plan, state)
            except RuntimeError:
                if never_idle or wrong_source:
                    self.assertEqual(operations, [])
                    return
                raise
        self.assertEqual(state['phase'], 'OLD_PROCESS_EXIT_PROVEN')
        self.assertGreaterEqual(operations[0][1], 15)
        self.assertGreaterEqual(len(state['idle_transcript']), 4)

    def test_stable_idle_then_atomic_managed_handoff(self):
        self.simulate()

    def test_new_turn_race_waits_then_rechecks_no_force(self):
        self.simulate(busy_race=True)

    def test_active_turn_never_receives_shutdown(self):
        self.simulate(never_idle=True)

    def test_wrong_old_source_never_receives_shutdown(self):
        self.simulate(wrong_source=True)

    def test_source_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source.py'
            source.write_text('original')
            plan = {'sources': {'source.py': activation.sha(source)}}
            with patch.object(activation, 'ROOT', Path(temporary)):
                activation.validate_sources(plan)
                source.write_text('changed')
                with self.assertRaises(RuntimeError):
                    activation.validate_sources(plan)

    def test_evidence_atomic_and_arm_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            area = Path(temporary)
            plan = {'request_id': activation.REQUEST}
            (area / 'plan.json').write_text(json.dumps(plan))
            with patch.object(activation, 'AREA', area), patch('builtins.print'):
                activation.record({}, 'WAITING_FOR_TERMINAL', helper_pid=44)
                with patch.object(activation.subprocess, 'run') as external:
                    activation.arm()
                    activation.arm()
                    external.assert_not_called()
            self.assertEqual(json.loads((area / 'evidence.json').read_text())['phase'], 'WAITING_FOR_TERMINAL')


class Controller(unittest.TestCase):
    def execute(self, uncertain=False, changed_target=False):
        plan, unused, sample = fixture()
        watchdog = {'state': 'QUEUED', 'attempt_count': 0, 'delivered_at': None, 'outcome': None}
        seq94 = {'state': 'FAILED_PERMANENT', 'attempt_count': 3}
        proof = {'fixture': 'immutable provenance'}
        proof_hash = hashlib.sha256(activation.canonical(proof).encode()).hexdigest()
        plan.update(watchdog_before=watchdog, seq94_before=seq94, supersession_proof_sha256=proof_hash)
        before = {'watchdog': copy.deepcopy(watchdog), 'seq94': seq94, 'audit': None, 'eligible': [activation.WATCHDOG]}
        after = {'watchdog': {'state': 'FAILED_PERMANENT', 'attempt_count': 0, 'delivered_at': None,
                  'outcome': {'state': 'SUPERSEDED', 'authorization_id': 'audit-id'}},
                 'seq94': seq94, 'eligible': [], 'audit': {'disposition': 'SUPERSEDED', 'delivery_id': activation.WATCHDOG,
                  'entry_before': watchdog, 'proof_sha256': proof_hash, 'proof': proof, 'authorization_id': 'audit-id'}}
        if changed_target:
            before['watchdog']['attempt_count'] = 1
        capability = {'schema': 'muse-capabilities/1', 'loaded_modules': plan['modules'], 'pid': 11,
            'build_id': plan['build_id'], 'bind': {'relay': ['127.0.0.1', 8766], 'inbox': ['127.0.0.1', 18741]},
            'admin_loaded': True, 'admin_routes': ['/local/inbox/admin/supersede-watchdog'], 'routes': plan['routes']}
        health = {'bridge_pid': 11, 'bridge_started_at': 1001, 'capabilities': capability,
                  'relay_ready': True, 'relay_v2': {'browser_enabled': False}}
        posts = []
        def http(path='/health', local_admin=False, data=None):
            if data is not None:
                posts.append(data)
                if uncertain:
                    raise OSError('response lost after durable audit')
                return {'ok': True}
            if path == '/health':
                return health
            if path == '/local/inbox/capabilities':
                return {'pid': 11, 'build_id': plan['build_id']}
            return {'evidence_verified': True, 'proof_sha256': proof_hash, 'queue_fingerprint': 'f'*64}
        with tempfile.TemporaryDirectory() as temporary:
            area = Path(temporary)
            (area / 'plan.json').write_text(json.dumps(plan))
            (area / 'evidence.json').write_text(json.dumps({'phase': 'ARMED', 'old': plan['old']}))
            with patch.object(activation, 'AREA', area), patch.object(activation, 'http', side_effect=http), \
                 patch.object(activation, 'validate_sources'), patch.object(activation, 'queue_sample', side_effect=[before, after]), \
                 patch.object(activation, 'wait_and_shutdown'), patch.object(activation, 'report'), patch.object(activation, 'prove_scheduler', return_value={'fixture': True}), \
                 patch.object(activation, 'process', side_effect=lambda pid: {'pid': pid, 'parent': 20 if pid == 11 else 0, 'image': 'svchost.exe'}):
                activation.run()
                result = json.loads((area / 'evidence.json').read_text())
                if not changed_target:
                    activation.run()
            self.assertEqual(len(posts), 0 if changed_target else 1)
            self.assertEqual(result['phase'], 'FAILED_CLOSED' if changed_target else 'SUCCESS')
            if not changed_target:
                self.assertFalse(result['seq94_preflight']['recovery_or_resend_performed'])
                self.assertTrue(result['seq94_preflight']['queue_unblocked'])

    def test_success_one_post_one_restart_phase_no_reexecution(self):
        self.execute()

    def test_uncertain_post_readback_only_never_resends(self):
        self.execute(uncertain=True)

    def test_changed_target_rejects_before_admin_post(self):
        self.execute(changed_target=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
