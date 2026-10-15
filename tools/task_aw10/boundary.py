"""Committed-evidence-only negative certification. No runner or bus entry points."""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = 'fb3e417aa48cc70cc4c05f796263c9cf87b791af'
FINAL = 'ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526'
MAX_CYCLE = (1 << 64) - 1


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def committed(path):
    return subprocess.check_output(['git', 'show', AUTHORITY + ':' + path], cwd=ROOT)


def payload(path):
    envelope = json.loads(committed(path))
    encoded = json.dumps(envelope['certificate'], sort_keys=True, separators=(',', ':')).encode()
    require(hashlib.sha256(encoded).hexdigest() == envelope['sha256'], 'certificate payload identity')
    return envelope['certificate']


def evidence():
    live = json.loads(committed('docs/BrainAge_TaskAW9_Result.json'))
    aw6 = payload('tools/task_aw6/certificate.json')
    aw8 = payload('tools/task_aw8/certificate.json')
    require(live['classification'] == 'FULL PASS' and live['attempts'] == 1, 'AW9 authority')
    require(live['final_digest'] == aw6['final_canonical_sha256'] == aw8['final_canonical_sha256'] == FINAL,
            'terminal commitment')
    require(live['final_registers'] == aw6['final_registers'] == aw8['final_registers'], 'terminal registers')
    require(live['final_identities'] == aw6['unchanged_identities'] == aw8['unchanged_identities'], 'terminal identities')
    require(live['final_cycle9'] == aw8['final_cycle9'] == 3416875777, 'terminal cycle')
    require(live['cap'] == aw6['final_cap'] == aw8['retained_cap'] == 3416875778, 'retained cap')
    require(live['cycle_cost'] == sum(row['cost'] for row in live['instructions']) == 56, 'prefix costs')
    require(live['MMIO_reads'] == live['unexpected_service_observations'] == live['remaining_authorized_runs'] == 0,
            'consumed run boundary')
    scalars = {}
    manifest = committed('tools/task_aw2/au_manifest.h').decode()
    for name, width, value in re.findall(r'expected.put\("([^"]+)",(\d+),(\d+)ULL\);', manifest):
        scalars[name] = {'width': int(width), 'value': int(value)}
    require(len(scalars) == 74, 'AU immutable manifest shape')
    for index, value in enumerate(live['final_registers']):
        scalars['r' + str(index)]['value'] = int(value, 16)
    updates = {
        'cpsr': (4, live['final_CPSR']), 'cycle9': (8, live['final_cycle9']),
        'cycle7': (8, live['cycle7']), 'ordinal9': (8, live['final_ordinal9']),
        'ordinal7': (8, live['ordinal7']), 'slice_cap': (8, live['cap']),
        'fast_limit': (8, aw6['final_fast_limit']), 'cap.count': (4, aw6['final_cap_records']),
        'capture.serial': (8, aw6['final_serial']), 'capture.epoch': (8, aw6['capture_epoch']),
    }
    for name, value in aw6['final_divider'].items():
        updates[name] = (2 if name == 'div.control' else 8 if name == 'div.deadline' else 4, value)
    for name, (width, value) in updates.items():
        scalars[name] = {'width': width, 'value': value}
    projection = {'schema': 'AW10 committed terminal projection v1; NOT a complete AW2S snapshot',
                  'full_state_commitment': FINAL, 'full_scalar_count': 411,
                  'full_identity_count': 5, 'scalars': scalars, 'identities': live['final_identities']}
    return live, aw6, aw8, projection


def check_projection(actual, expected):
    require(actual == expected, 'committed terminal projection mismatch')
    require(len(actual['scalars']) < actual['full_scalar_count'], 'projection must not impersonate full state')


def prospective(cycle, cap, cost, debt=0, eligible=False):
    require(all(type(value) is int and 0 <= value <= MAX_CYCLE for value in [cycle, cap, cost, debt]), 'cycle domain')
    require(cost > 0 and cap > 0, 'unknown cost/cap')
    require(cost <= MAX_CYCLE - cycle and debt <= MAX_CYCLE - cycle - cost, 'cycle overflow')
    require(not eligible, 'unexpected service eligibility')
    commit = cycle + cost + debt
    return {'commit': commit, 'strictly_before_cap': commit < cap,
            'poll_before': cycle >= cap, 'poll_after': commit >= cap,
            'overrun': max(0, commit - cap), 'remaining_before': max(0, cap - cycle)}


def status_projection(control, deadline, cycle, expected_read):
    require(control == 0x8001 and deadline == 1708437913, 'divider entry mismatch')
    require(cycle >> 1 < deadline, 'divider service boundary')
    require(expected_read == control & 0xffff, 'wrong status result')
    return {'value': expected_read, 'divider_model_mutation': False,
            'deadline_changed': False, 'active_system_timestamp': cycle >> 1}


def no_service_path(events):
    expected = ['entry_verified', 'prospective_rejected', 'audit_flush_close', 'nonreturning_disposal']
    require(events == expected, 'missing/extra/reordered event or forbidden service/effect')
    return True


def instruction_map():
    source = json.loads(committed('docs/BrainAge_TaskAV_Result.json'))
    arrays = [value for value in source.values() if isinstance(value, list)]
    rows = [row for array in arrays for row in array if isinstance(row, dict) and 'opcode' in row and 'pc' in row]
    result = {row['pc'].upper(): row for row in rows}
    addresses = ['0X020019B4', '0X020019B8', '0X020019BC']
    require(all(address in result for address in addresses), 'committed lookahead unavailable')
    return [result[address] for address in addresses]


def certificate():
    live, aw6, aw8, projection = evidence()
    check_projection(projection, copy.deepcopy(projection))
    next_instruction = aw8['forbidden_next']
    require(next_instruction['opcode'] == '0xE1D100B0' and next_instruction['modeled_cost'] == 8, 'read identity/cost')
    bound = prospective(live['final_cycle9'], live['cap'], next_instruction['modeled_cost'])
    require(not bound['strictly_before_cap'] and not bound['poll_before'] and bound['poll_after'], 'cap contradiction')
    read = status_projection(aw6['final_divider']['div.control'], aw6['final_divider']['div.deadline'],
                             live['final_cycle9'], 0x8001)
    return {
        'task': 'AW10', 'classification': 'PARTIAL', 'kind': 'negative admission certificate; no execution authorization',
        'authority': AUTHORITY, 'entry': projection, 'next_instructions': instruction_map(),
        'static_read_projection': read, 'prospective': bound,
        'instruction_semantics_not_execution': [
            {'pc': '0x020019B4', 'opcode': '0xE1D100B0', 'operation': 'LDRH r0,[r1]',
             'address': '0x04000280', 'width': 2, 'write': False, 'numC': 1, 'numD': 8, 'cost': 8,
             'conditional_R0': '0x00008001', 'conditional_next_PC': '0x020019B8',
             'NZCV': 'unchanged 0000', 'SP_LR_other_registers': 'unchanged',
             'order': 'account/fetch -> data timing latch -> MMIO selection -> register write -> cycle commit -> retired -> IRQ -> slice unwind',
             'divider_effect': 'no acknowledge, clear-busy, finish, reschedule or operand/result change',
             'other_effects': 'fetch/data timing latches and diagnostic counters/ordinals would change; not a full-state no-op'},
            {'pc': '0x020019B8', 'opcode': '0xE2100902', 'operation': 'ANDS r0,r0,#0x8000',
             'cached_numC': 3, 'cost': 3, 'conditional_R0': '0x00008000', 'conditional_NZCV': '0000',
             'conditional_next_PC': '0x020019BC', 'note': 'local opcode semantics only; normal slice polling already follows B4'},
            {'pc': '0x020019BC', 'opcode': '0x1AFFFFFC', 'operation': 'BNE 0x020019B4',
             'taken_cached_refill_cost': 4, 'conditional_taken': True, 'NZCV': 'unchanged',
             'not_taken_PC': '0x020019C0', 'note': 'next control-flow boundary; no loop or fallthrough certified'}
        ],
        'guest_instructions_certified': 0, 'dynamic_execution_ready': False,
        'runtime_execution_armed': False, 'live_execution_authorized': False,
        'start_pc': '0x020019B4', 'stop_pc': '0x020019B4', 'MMIO_ledger': [],
        'post_read_CPU_or_state_digest_certified': False,
        'unchanged_if_disposed_at_entry': {'registers': live['final_registers'], 'CPSR': live['final_CPSR'],
                                         'full_state_commitment': FINAL, 'RAM_DTCM_save_deltas': 0},
        'natural_pre_read_slice_transition': False,
        'required_transition': 'New separately certified diagnostic pre-dispatch yield through run_slice and scheduler round; none installed or certified here',
        'scheduler_tail_order': ['save ARM9 slot cycles/debt', 'ARM9 timers', 'GPU3D', 'ARM7 catch-up / timers',
                                 'power-off check', 'display', 'SPU', 'Wifi', 'RTC', 'system events', 'system timestamp',
                                 'later round selects target / nds_slice_begin'],
        'forbidden_next_effect': 'Fetch/account/dispatch 0x020019B4; any divider read, cap normalization, or scheduler tail',
        'terminal_requirement': 'Retain AW9 retired-boundary flush/close + nonreturning _Exit; no continuation',
        'full_terminal_snapshot_reconstructed': False,
        'blockers': [
            'Committed artifacts bind the complete 411-field terminal identity but do not serialize its full values; historical canonical audit is local-only.',
            'Current Tier-3 has no pre-dispatch prospective-yield transition at cycle 3416875777 < fast_limit 3416875778; ordinary atomic read overshoots to 3416875785.',
            'No exact all-field scheduler-tail/new-slice transcript or guarded early-return handoff is certified.'
        ],
        'limits': ['Negative cap proof applies even without the missing scalar values.',
                   'Busy status 0x8001 is a source-model counterfactual, not an observed or authorized MMIO read.',
                   'No full canonical digest is invented for a projected post-read or scheduler state.']
    }
