"""Produce a source-bound static fence certificate, never a launch permit."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/task_aw11'))
from state import FINAL, encode, load, require, validate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def certificate(evidence):
    require(evidence.is_relative_to(ROOT / 'local/task-aw12'), 'local ROM-free certification evidence')
    summary = json.loads((evidence / 'summary.json').read_text())
    require(summary['all_passed'] and summary['guest_instructions'] == summary['MMIO'] == 0, 'passing ROM-free proof')
    for name, identity in summary['tested_inputs_sha256'].items():
        require(sha(Path(__file__).parent / name) == identity, 'stale implementation evidence: ' + name)
    for name, identity in summary['original_source_hashes'].items():
        require(sha(ROOT / name) == identity, 'stale original source/evidence: ' + name)
    record = load()
    validate(record)
    fields = [row[:] for row in record['fields']]
    next(row for row in fields if row[0] == 'unwinding')[2] = 1
    preserved = hashlib.sha256(encode(fields, record['identities'])).hexdigest()
    next(row for row in fields if row[0] == 'slot9.cycle')[2] = 3416875777
    fenced = hashlib.sha256(encode(fields, record['identities'])).hexdigest()
    phases = ['yield_requested', 'tier3_exit', 'unwind_preserved', 'slice_consumed', 'slot_saved',
              'pre_device_fence', 'gpu_observed', 'scheduler_admitted_capture_only']
    for mode in ['success', 'runtime-facade', 'prior-frames']:
        outcome = summary['outcomes'][mode]
        require(outcome['exit'] == 73 and [item['event'] for item in outcome['observations']] == phases, 'complete proof transcript')
        require([item['core_sha256'] for item in outcome['observations']] == [FINAL, FINAL, preserved, preserved] + [fenced]*4, 'complete protected state transitions')
    return {
        'schema': 'AW12 conditional zero-guest pre-device-fence certificate v1',
        'classification': 'FULL PASS',
        'classification_scope': 'ROM-free one-use capture-only handoff to a terminal pre-device fence, not a complete scheduler tail or new guest slice',
        'authority': {'AW11': 'b10e83d9f5e236930d7b2fd8e1b2b301e978decc',
                      'AW10': 'c699e3a21207abaa72b8130bf54c0f189c846412',
                      'AW9': 'fb3e417aa48cc70cc4c05f796263c9cf87b791af',
                      'framework': '3a57236bb23d25dcb4caad7d58d733311062ff5e'},
        'entry': {'metadata': 'tools/task_aw11/terminal.json', 'canonical_schema': 'AW2S v1',
                  'scalars': 411, 'identities': 5, 'bytes': 8862, 'sha256': FINAL,
                  'PC': '0x020019B4', 'last_retired': '0x020019B0', 'cycle9': 3416875777,
                  'cap': 3416875778, 'cap_expired': False,
                  'extra_runtime_preconditions': ['old AU/AW7 guards and all 69 reduced observations accepted',
                      'no active access; original bus_calls=18; same observer/thread ownership',
                      'AW12 installed once in explicitly compiled diagnostic process with exclusive fresh audit',
                      'outermost tracked runtime_dispatch_impl; actual g_tail_dispatch null at entry',
                      'actual g_static_guard null at entry; saved-unwind-valid false',
                      'AW6 ready_before(entry,3416875777) passes unchanged; repeat passive snapshots exact']},
        'ownership': {'ticket': 'first and only process ticket; no overflow/rearm',
                      'frame_serial': 'runtime-owned increasing dispatch serial, sealed at offer; not assumed historically equal to 1',
                      'epoch': 'all captured cap/ROM/scheduler epochs remain exact, no import/normalization',
                      'phase_order': phases,
                      'saved_unwind_valid': [False, False, True, False, False, False, False, False],
                      'frame_depth': [1, 1, 1, 0, 0, 0, 0, 0],
                      'failure': 'sticky nonreturning failure disposal; no old-halt or redispatch fallback'},
        'state_transitions': {'entry_sha256': FINAL, 'unwind_preserved_sha256': preserved,
                             'fence_core_sha256': fenced,
                             'only_core_deltas': {'unwinding': [0, 1], 'slot9.cycle': [3416875650, 3416875777]},
                             'all_other_scalars_and_identities': 'exactly constant',
                             'CPU_registers_flags_cycles_ordinals': 'unchanged', 'cap_journal': 'unchanged; no append or reset'},
        'GPU': {'schema': 'AW2S v1 with gpu.schema uint16=1, independent extension',
                'base_scalars': 19, 'source': 'runtime g_nds.GPU.GPU3D plus ARM9Timestamp/ARM9ClockShift; direct const fields and logical FIFO Peek',
                'fields': ['GeometryEnabled', 'FlushRequest', 'GXStat', 'CycleCount', 'Timestamp',
                           'VertexPipeline', 'NormalPipeline', 'PolygonPipeline', 'VertexSlotCounter', 'VertexSlotsFree',
                           'NumPushPopCommands', 'NumTestCommands', 'ExecParamCount', 'ARM9Timestamp', 'ARM9ClockShift',
                           'schema', 'CmdPIPE count/ordered Command+Param', 'CmdFIFO count/ordered Command+Param',
                           'CmdStallQueue count/ordered Command+Param'],
                'queue_limits': [4, 256, 64],
                'Run_work_branch': 'GeometryEnabled && !FlushRequest && (CmdPIPE not empty || GXStat.bit27)',
                'capture_admission': ['complete schema and exact repeat sampling on owner thread',
                                     'clock shift=1; max(raw signed CycleCount,0) equals protected GPU debt=0',
                                     'Run work branch false; all three queues empty',
                                     'vertex/normal/polygon pipelines and push/pop/test/exec-parameter counts zero',
                                     'raw CycleCount<=0 and GXStat.bit27 clear',
                                     'GPU Timestamp<=cycle9>>1 and ARM9Timestamp<=cycle9'],
                'historical_AW9_extended_GPU_identity_known': False,
                'synthetic_idle_fixture_sha256_not_historical': summary['outcomes']['success']['gpu_sha256'],
                'new_live_measurement_required': True, 'Run_called': False},
        'scheduler_transition': {'escape': 'retired observer offer -> Tier-3 sync_out/preserve/break before IRQ/next loop',
                                 'consume': 'run_slice after original restore_unwind_state, before terminal/DMA/HALT/event/slice checks',
                                 'fence': 'after original ARM9 slot save; before first Kind::device, ARM9 timers and GPU3D Run',
                                 'admission_scope': 'capture-only terminal fence; no service is admitted',
                                 'new_slice_or_cap': None, 'cap_relation': '3416875777 < 3416875778 remains unchanged',
                                 'next_guest_PC': '0x020019B4', 'next_guest_dispatch_certified': False},
        'invariants': {'guest_instructions': 0, 'fetch_account_dispatch_B4': 0, 'MMIO': 0,
                       'device_GPU_IRQ_ARM7_service': 0, 'scheduler_tail_or_next_round': 0,
                       'RAM_DTCM_save_writes': 0, 'logical_saves': 0, 'Flash_commits': 0,
                       'save_checkpoint_opened': False},
        'disposal': {'success_exit': 73, 'failure_exit': 79, 'audit_IO_failure_exit': 78,
                     'primitive': 'audit fflush/fclose then std::_Exit; no shutdown/persistence/destructor tail'},
        'implementation_sha256': summary['tested_inputs_sha256'],
        'private_overlay_sha256': summary['overlay_hashes'],
        'evidence': {'path': str(evidence.relative_to(ROOT)).replace('\\', '/') + '/',
                     'summary_sha256': sha(evidence / 'summary.json'),
                     'native_assertions': summary['native_assertions'], 'children': summary['children'],
                     'success_children': summary['disposal_successes'], 'failure_children': summary['disposal_failures'],
                     'disabled_children': summary['default_children'], 'audit_tamper_rejections': summary['audit_negative_cases'],
                     'actual_runtime_syntax_checks': len(summary['runtime_syntax']), 'actual_GPU_type_check': True},
        'disabled': 'no installation available without compile macro; null owners/hooks preserve original behavior; original runner untouched',
        'static_zero_guest_handoff_certified': True,
        'conditional_capture_only_transition_ready': True,
        'dynamic_execution_ready': False,
        'live_validation_authorized_by_this_certificate': False,
        'next_safe_task': 'Separately authorize one terminal-to-pre-device-fence capture-only validation, no B4 fetch/account/dispatch or service; reject any core/host-context/GPU mismatch and dispose. A fresh narrowly bounded prerequisite replay/permit requires explicit separate authorization; consumed AW9 permits cannot be reused.'
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    require(output.is_relative_to(ROOT / 'local/task-aw12') and not output.exists(), 'fresh local static decision only')
    value = certificate(args.evidence.resolve())
    output.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'classification': value['classification'], 'dynamic_execution_ready': False, 'certificate_sha256': sha(output)}))


if __name__ == '__main__':
    main()
