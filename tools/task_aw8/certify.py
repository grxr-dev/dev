"""Verify ROM-free evidence and freeze readiness metadata. Never arms or executes a runner."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('aw6_verify', ROOT / 'tools/task_aw6/check.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    output = args.out.resolve()
    assert evidence.is_relative_to(ROOT / 'local/task-aw8')
    assert output.is_relative_to(ROOT / 'local/task-aw8') and not output.exists()
    result = json.loads((evidence / 'tests.json').read_text())
    assert result['actual_provider_entry_matches_AW5'] and result['actual_provider_69_observation_success']
    assert result['default_build_arming_rejected'] and result['production_binding_header_rejected']
    assert result['runtime_bus_still_closed'] and not result['BrainAge_execution'] and not result['AX_executed']
    assert len(result['children']) == 56 and len(result['identity_tamper_children']) == 5
    assert sum(child['exit'] == 79 for child in result['children']) == 54
    for name, digest in result['fixture_sources_sha256'].items():
        assert sha(ROOT / name) == digest
    for name, digest in result['generated_sources_sha256'].items():
        assert sha(evidence / name) == digest
    for name, digest in result['preserved_artifacts'].items():
        assert sha(ROOT / name) == digest
    assert sha(evidence / 'build/aw8_provider_test.exe') == result['fixture_executable_sha256']
    for child in result['children']:
        audit = [json.loads(line) for line in (evidence / child['mode'] / 'audit.jsonl').read_text().splitlines()]
        assert checks.verify_chain(audit) == child['observations']
        assert child['mode'] == 'inspect' or audit[-1]['event'] == ('terminal' if child['mode'] == 'success' else 'failure')
        if child['mode'] != 'inspect':
            for sentinel in ['scheduler', 'device', 'IRQ', 'ARM7', 'guest', 'halt', 'shutdown', 'persistence', 'real-bus', 'real-MMIO', 'forbidden']:
                assert not (evidence / child['mode'] / sentinel).exists()
    static = json.loads((ROOT / 'tools/task_aw6/certificate.json').read_text())
    assert hashlib.sha256(json.dumps(static['certificate'], sort_keys=True, separators=(',', ':')).encode()).hexdigest() == static['sha256']
    payload = {
        'task': 'AW8', 'kind': 'ROM-free exact-profile provider/controller readiness, not execution authorization',
        'dynamic_execution_ready': True, 'live_execution_authorized': False, 'runtime_execution_armed': False,
        'authority': {'AW7': '01fe942d8d42b0dc819acf92836c7cfb845a6470', 'AW6': '1d4aeb1e17486b1db2276931f43a9c5d9a540f1b',
                      'AW5': 'e366a8b8811668ae9bd22bd34b661799c6058bad'},
        'AW6_certificate_payload_sha256': static['sha256'],
        'entry_canonical_sha256': static['certificate']['entry_canonical_sha256'],
        'entry_scalars': 361, 'entry_identities': 5,
        'start_pc': '0x02001980', 'stop_pc': '0x020019B4', 'terminal_event': 'retired for 0x020019B0 before IRQ/scheduler tail',
        'instructions': static['certificate']['instructions'], 'instruction_count': 11, 'observations': 69, 'cycles': 56,
        'MMIO_writes': 5, 'MMIO_reads': 0, 'data_accesses': static['certificate']['data_accesses'],
        'final_cycle9': 3416875777, 'retained_cap': 3416875778, 'cap_margin': 1,
        'final_canonical_sha256': static['certificate']['final_canonical_sha256'],
        'final_registers': static['certificate']['final_registers'], 'final_CPSR': 31,
        'unchanged_identities': static['certificate']['unchanged_identities'],
        'forbidden_next': static['certificate']['forbidden_next'],
        'RAM_DTCM_save_deltas': 0, 'unexpected_services_tolerated': 0,
        'entry_guards': 'All AU guards, exact computed live identities and full AW5 canonical entry; no normalization or metadata substitution in live path',
        'per_instruction_guards': 'Unchanged AW6 prospective cost/debt/cap/readiness and AW7 full-state/chain/journal/access-owner checks',
        'terminal': 'Exclusive audit flush/close + nonreturning std::_Exit before next fetch/accounting/dispatch or scheduler/IRQ tail',
        'test_identity_binding': 'Authenticated AW5 metadata sealed to computed synthetic surrogate digests; not new measurements of original image bytes',
        'fixture_provenance': result['provenance'], 'fixture_sources_sha256': result['fixture_sources_sha256'],
        'tests_sha256': sha(evidence / 'tests.json'), 'success_audit_sha256': sha(evidence / 'success/audit.jsonl'),
        'fixture_executable_sha256': result['fixture_executable_sha256'],
        'local_evidence': str(evidence.relative_to(ROOT)).replace('\\', '/'),
        'limits': ['No Brain Age execution or replay', 'No runtime MMIO or status-read certification',
                   'Test-only identity adapters must never enter a live runner', 'Real-bus interlock remains closed',
                   'Later one-shot diagnostic arming/backend permission requires separate authorization and all live guards',
                   'No full 12-instruction, compiled-parity, gameplay or save claim']
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    output.write_text(json.dumps({'sha256': digest, 'certificate': payload}, indent=2) + '\n')
    print(json.dumps({'dynamic_execution_ready': True, 'live_execution_authorized': False, 'certificate_sha256': digest}, indent=2))


if __name__ == '__main__':
    main()
