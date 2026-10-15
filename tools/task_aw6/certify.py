"""Emit static certificate metadata from ROM-free passing evidence; never authorize or run it."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from check import verify_chain

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/task_aw5'))
from analyze import decode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    assert output.is_relative_to(ROOT / 'local/task-aw6') and not output.exists()
    tests = json.loads((args.evidence / 'tests.json').read_text())
    assert tests['assertions'] >= 56951 and tests['AX_executed'] is False
    for name, expected in tests['contract_sources'].items():
        assert hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() == expected
    rows = [json.loads(line) for line in (args.evidence / 'success/audit.jsonl').read_text().splitlines()]
    assert verify_chain(rows) == 69 and rows[-1]['event'] == 'terminal'
    snapshots = [row for row in rows if row['event'] == 'canonical_snapshot']
    initial, identities = decode(bytes.fromhex(snapshots[0]['canonical_hex']))
    final, final_identities = decode(bytes.fromhex(snapshots[-1]['canonical_hex']))
    assert identities == final_identities and len(initial) == 361 and len(final) == 411
    assert final['cycle9'] == 3416875777 and final['r15'] == 0x020019b4
    instruction_rows = []
    ledger = []
    previous_state = None
    start_cycle = None
    for row in rows:
        if row['event'] == 'canonical_snapshot':
            previous_state, _ = decode(bytes.fromhex(row['canonical_hex']))
        if row['event'] != 'observation':
            continue
        assert row['accepted']
        if row['kind'] == 0:
            start_cycle = previous_state['cycle9']
        if row['kind'] == 3:
            instruction_rows.append({'pc': f"0x{row['pc']:08X}", 'opcode': f"0x{initial['code.' + format(row['pc'], '08x')]:08X}",
                                     'cost': row['value'], 'cycle_before': start_cycle, 'cycle_after': previous_state['cycle9']})
        if row['kind'] == 2 and row['address'] != row['pc']:
            ledger.append({'pc': f"0x{row['pc']:08X}", 'address': f"0x{row['address']:08X}",
                           'width': row['width'], 'write': row['write'], 'value': row['value'],
                           'precommit_cycle': previous_state['cycle9'], 'divider_control': previous_state['div.control'],
                           'divider_deadline': previous_state['div.deadline'], 'cap': previous_state['slice_cap'],
                           'cap_records': previous_state['cap.count'], 'serial': previous_state['capture.serial']})
    assert len(instruction_rows) == 11 and sum(row['cost'] for row in instruction_rows) == 56
    assert len(ledger) == 7 and sum(row['write'] for row in ledger) == 5
    certificate = {
        'kind': 'static reduced-prefix source/model certificate; not runtime activation or execution authorization',
        'entry_canonical_sha256': snapshots[0]['sha256'], 'final_canonical_sha256': snapshots[-1]['sha256'],
        'schema': 'AW2S v1, complete AW4/AW5 observation set retained',
        'start_pc': '0x02001980', 'stop_pc': '0x020019B4', 'stop_observation': 'retired for 0x020019B0',
        'instruction_count': 11, 'observations': 69, 'candidate_cost': 56, 'remaining_cap_margin': 1,
        'instructions': instruction_rows, 'data_accesses': ledger,
        'final_registers': [f"0x{final['r' + str(index)]:08X}" for index in range(16)],
        'final_CPSR': final['cpsr'], 'final_ordinal9': final['ordinal9'], 'final_ordinal7': final['ordinal7'],
        'final_cap': final['slice_cap'], 'final_fast_limit': final['fast_limit'],
        'final_cap_records': final['cap.count'], 'final_serial': final['capture.serial'], 'capture_epoch': final['capture.epoch'],
        'final_divider': {name: value for name, value in final.items() if name.startswith('div.')},
        'unchanged_identities': identities, 'predicted_RAM_DTCM_save_changed_bytes': 0,
        'forbidden_next': {'pc': '0x020019B4', 'opcode': '0xE1D100B0', 'effect': 'divider status read',
                           'modeled_cost': 8, 'hypothetical_cycle_after': 3416875785},
        'full_12_instruction_certificate': False, 'AX_executed': False, 'AX_execution_authorized': False,
        'activation_installed': False,
        'required_integration': 'Separately reviewed AU-guard-dominating transfer, exclusive controller access ownership, trusted actual passive source and terminal/failure wiring; existing runner still denies AX',
        'prospective_guards': 'exact captured identity and complete logical schema; source-derived readiness; derived cost with checked arithmetic; both old and prospective cap strictly above commit; all deadlines beyond stop; no unknown state changes',
        'terminal': 'exclusive audit flush/close + nonreturning _Exit at observation 69 before IRQ, cap polling, status fetch or scheduler return',
        'forbidden_services_tolerated': 0,
        'evidence_limits': 'Current positive coupling uses extracted actual source bodies on synthetic captured scalar objects, not newly executing the actual runtime provider or interpreter'
    }
    certificate['source_function_sha256'] = tests['source_functions']
    certificate['contract_source_sha256'] = tests['contract_sources']
    certificate['runtime_source_sha256'] = {name: identity for name, identity in tests['protected_artifacts_unchanged'].items() if name.startswith('local\\ndsrecomp\\runner\\src\\')}
    encoded = json.dumps(certificate, sort_keys=True, separators=(',', ':')).encode()
    output.write_text(json.dumps({'sha256': hashlib.sha256(encoded).hexdigest(), 'certificate': certificate}, indent=2) + '\n')
    print(json.dumps({'certificate_sha256': hashlib.sha256(encoded).hexdigest(), 'final_state_sha256': snapshots[-1]['sha256'], 'instructions': 11, 'observations': 69}, indent=2))


if __name__ == '__main__':
    main()
