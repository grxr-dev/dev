"""Emit the static negative handoff decision from passing ROM-free evidence only."""
import argparse
import hashlib
import json
from pathlib import Path

from state import ROOT, AW9, AW10, FINAL, load, require, validate


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def decision(evidence):
    record = load()
    data = validate(record)
    tests = json.loads((evidence / 'tests.json').read_text())
    require(tests['all_passed'] and tests['python_cases'] == 1257 and tests['native_assertions'] == 1260, 'focused tests incomplete')
    require(tests['terminal_scalar_count'] == 411 and tests['digest'] == FINAL and
            tests['GPU_projection_ambiguity_proven'] and tests['run_slice_model_redispatch_proven'], 'binding/path proof incomplete')
    require([row['exit'] for row in tests['disposal_children']] == [73, 79] and
            all(row['tail_sentinels'] == 0 for row in tests['disposal_children']), 'disposal proof incomplete')
    for name, expected in tests['protected_artifacts_unchanged'].items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, 'protected input drift: ' + name)
    return {
        'schema': 'AW11 static handoff decision v1', 'classification': 'PARTIAL',
        'kind': 'positive lossless terminal-metadata binding and negative existing scheduler-handoff certificate',
        'authority': {'AW10': AW10, 'AW9': AW9, 'framework': '3a57236bb23d25dcb4caad7d58d733311062ff5e'},
        'entry': {'metadata': 'tools/task_aw11/terminal.json', 'scalar_count': 411, 'identities': 5,
                  'canonical_schema': 'AW2S v1', 'canonical_bytes': len(data), 'canonical_sha256': FINAL,
                  'metadata_logical_sha256': digest(record), 'AW10_cells_reconciled': 89, 'additional_cells_bound': 322,
                  'getter_ownership_counts': {owner: sum(value == owner for name, value in record['field_owners'])
                                            for owner in record['owners']},
                  'PC': '0x020019B4', 'cycle9': 3416875777, 'cap': 3416875778,
                  'fast_limit': 3416875778, 'CPSR': 31,
                  'snapshot_is_resumable_process_or_full_savestate': False},
        'zero_guest_scheduler_handoff_certified': False, 'dynamic_execution_ready': False,
        'runtime_activation_installed': False, 'live_execution_authorized': False,
        'guest_instructions_certified': 0, 'MMIO_ledger': [],
        'existing_safe_terminal': 'AW9 retired callback -> audit flush/close -> nonreturning _Exit; no caller continuation',
        'equivalent_resumed_boundary': {'cap_expired': False, 'poll_before': False,
            'next_read_cost': 8, 'hypothetical_read_commit': 3416875785,
            'next_fetch_account_dispatch_forbidden': '0x020019B4 / E1D100B0',
            'ordinary_or_unwind_only_return': 'run_slice redispatches while cycles < local cap',
            'existing_legal_early_yield_reason': None},
        'required_owned_phase_not_installed': 'one-use diagnostic pre-dispatch exit propagated through run_slice, with dominating pre-device fence and strict expected-service ledger',
        'tail_order': ['ARM9_slot_save', 'ARM9_timers', 'GPU3D', 'ARM7_HALT_catchup', 'ARM7_timers',
                       'poweroff_check', 'display', 'SPU', 'Wifi', 'RTC', 'system_events',
                       'system_timestamp', 'next_round', 'next_slice_begin'],
        'conditional_submodels_not_full_tail_certificate': {
            'rendezvous': 1708437888, 'ARM7_HALT_catchup_cycles': 63, 'ARM7_debt_after': 2,
            'timer_counter_accum': {'0': [14558, 62], '4': [50776, 43], '5': [64195, 39]},
            'timer_banks_last': 1708437888, 'timer_overflow_IRQ': 0,
            'if_all_hidden_service_effects_inert_next_event': 1708437913,
            'if_all_hidden_service_effects_inert_next_ARM9_target': 3416875826,
            'new_cap_certified_or_set': False, 'post_tail_state_digest_issued': False},
        'missing_peripheral_branch_facts': {
            'first_unresolved_service': 'nds_gpu3d_run -> GPU3D::Run', 'recorded_projection': 'service.gpu_debt = 0',
            'projection_is_non_injective': True,
            'facts_not_in_411': ['GeometryEnabled', 'FlushRequest', 'CmdPIPE empty/contents', 'GXStat bit27',
                                 'GPU Timestamp', 'raw CycleCount and relevant pipeline state'],
            'source_model_witness': 'same CyclesToRunFor()=0, disabled path dispatches 0 commands; enabled/nonempty path reaches ExecuteCommand once',
            'actual_AW9_GPU_branch_claimed': False},
        'forbidden_effects': ['B4 fetch/account/dispatch or MMIO read', 'cap/cycle normalization', 'fake event or HALT',
                              'silently dropping protected fields or removing observer ownership',
                              'unmodeled scheduler/device/IRQ/ARM7/shutdown/persistence continuation'],
        'blocked_on': [
            'No owned pre-dispatch early-yield/phase transfer exists at the bound under-cap entry; ordinary return redispatches.',
            'The complete existing 411-field observation does not identify the GPU Run branch, so a unique full scheduler-tail transcript/new-slice state cannot be certified.'
        ],
        'tests': {'python_cases': 1257, 'native_assertions': 1260, 'disposal_children': 2,
                  'local_evidence': str(evidence.relative_to(ROOT)).replace('\\', '/') + '/',
                  'summary_sha256': hashlib.sha256((evidence / 'tests.json').read_bytes()).hexdigest(),
                  'source_function_sha256': tests['source_functions']},
        'safety': {'guest_instructions': 0, 'live_replays': 0, 'runtime_BrainAge_MMIO': 0,
                   'ROM_save_checkpoint_opened_or_mutated': False, 'normal_runtime_semantics_changed': False,
                   'old_guards_and_nonreturning_disposal_preserved': True,
                   'logical_save_requests': 0, 'Flash_commits': 0, 'changed_save_bytes': 0},
        'next_safe_task': 'Separately authorized ROM-free one-use early-yield ownership plus pre-device fence, and minimal passive GPU branch/readiness projection; no replay or status-read execution.'
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    evidence, output = args.evidence.resolve(), args.out.resolve()
    require(evidence.is_relative_to(ROOT / 'local/task-aw11') and
            output.is_relative_to(ROOT / 'local/task-aw11') and not output.exists(), 'isolated fresh decision output')
    body = decision(evidence)
    output.write_text(json.dumps({'sha256': digest(body), 'certificate': body}, indent=2) + '\n')
    print(json.dumps({'classification': body['classification'], 'terminal_binding': True,
        'zero_guest_scheduler_handoff_certified': False, 'certificate_payload_sha256': digest(body)}, indent=2))


if __name__ == '__main__':
    main()
