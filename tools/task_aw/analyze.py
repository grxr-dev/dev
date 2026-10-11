"""Read-only source/metadata audit; --export writes ROM-free AW result only."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FW = ROOT / 'local/ndsrecomp'
SRC = FW / 'runner/src'
BASE = '3a57236bb23d25dcb4caad7d58d733311062ff5e'
AV = '524acc6bead2768183e45ae4913b00ea811b274b'


def body(text, signature):
    start = text.index(signature)
    return text[start:text.index('\n}', start)+2]


def ordered(text, *tokens):
    positions = [text.index(token) for token in tokens]
    assert positions == sorted(positions), tokens


def analyze():
    assert subprocess.check_output(['git','-C',str(FW),'rev-parse','HEAD'],text=True).strip()==BASE
    subprocess.run(['git','merge-base','--is-ancestor',AV,'HEAD'],cwd=ROOT,check=True)
    av = json.loads((ROOT/'docs/BrainAge_TaskAV_Result.json').read_text())
    preserved=0
    modified={f'dev\\local\\ndsrecomp\\runner\\src\\{name}' for name in
              ['tier3.cpp','runtime_arm.cpp','scheduler.cpp','io.cpp','bus.cpp']}
    for relative, expected in av['input_sha256'].items():
        if relative in modified:
            continue
        with (ROOT.parent/relative).open('rb') as source:
            assert hashlib.file_digest(source,'sha256').hexdigest()==expected,relative
        preserved+=1
    text = {name:(SRC/name).read_text(encoding='utf-8-sig') for name in
            ['tier3.cpp','runtime_arm.cpp','scheduler.cpp','io.cpp']}
    original = subprocess.check_output(['git','-C',str(FW),'show',BASE+':runner/src/io.cpp']).decode()
    signatures = ['uint64_t active_system_timestamp()', 'void start_div()', 'void finish_div()',
                  'uint32_t math_reg_read32(', 'bool math_addr(', 'void math_reg_write(',
                  'uint64_t nds_next_system_event_time()', 'void nds_run_system_events(']
    for signature in signatures:
        observed = body(text['io.cpp'],signature).replace(
            '\n    task_aw::emit(task_aw::Kind::device);','')
        assert observed == body(original,signature), signature
    ordered(body(text['runtime_arm.cpp'],'extern "C" void nds_reschedule_slice('),
            'cpu_deadline < g_cycle_cap','g_cycle_cap = cpu_deadline','g_nds_fast_limit = 0u')
    assert 'g_nds_terminal = true' in body(text['runtime_arm.cpp'],'extern "C" void nds_halt(')
    ordered(text['tier3.cpp'],'sync_out(ic);\n        task_aw::emit(task_aw::Kind::instruction',
            'brainage_task_au::control(ic)','const bool covered = nds_has_bank',
            '++g_stats.instructions','r = Interpreter::step',
            'g_runtime_cycles += cyc + runtime_deferred_cycles_take()',
            'task_aw::Kind::cycle_commit','task_aw::Kind::retired',
            'nds_note_irq_accept(g_nds_active','poll_after && nds_slice_over()')
    ordered(body(text['scheduler.cpp'],'void scheduler_run_round()'),
            'task_aw::Kind::scheduler','run_slice(0,',
            'task_aw::Kind::device','nds_tick_timers(0,','nds_gpu3d_run(',
            'run_slice(1,','nds_tick_display(','nds_run_system_events(')
    for name in ['runtime','scheduler','bus','io']:
        provider=(ROOT/f'tools/task_aw/{name}.inc').read_text()
        for forbidden in ['bus_read_u','bus_write_u','scheduler_run_round(',
                          'save_current(', 'runtime_code_cycles(', 'runtime_data_cycles(',
                          'nds_run_system_events(', 'nds_tick_timers(']:
            assert forbidden not in provider, (name,forbidden)
    tests=json.loads((ROOT/'local/task-aw/tests.json').read_text())
    encoded=(ROOT/'local/task-aw/compile.log').read_bytes()
    compile_log=encoded.decode('utf-16' if encoded.startswith(b'\xff\xfe') else 'utf-8-sig')
    assert 'error:' not in compile_log and 'FAILED:' not in compile_log
    source_hashes={name:hashlib.sha256((SRC/name).read_bytes()).hexdigest() for name in text}
    return {
        'task':'AW', 'classification':'PARTIAL', 'authoritative_AV':AV,
        'authoritative_AU':'f17f95ae2b2a15f7fced6f04d82d2593350d37a4',
        'framework_baseline':BASE, 'rom_sha1':av['rom_sha1'],
        'brainage_guest_execution':False, 'brainage_runtime_mmio':False,
        'checkpoint_or_save_mutation':False, 'generated_recomp_C_edited':False,
        'runner_executable_relinked_or_launched':False,
        'tests':{'unit':tests['unit'],'process_disposal':tests['children'],
                 'five_runtime_objects_compile':True,'divider_source_model_unchanged':True,
                 'passive_provider_source_checks':True,'AV_original_inputs_hash_preserved':preserved},
        'terminal_primitive':'explicit audit flush/close then std::_Exit; no scheduler return or destructors',
        'runtime_observer':'null by default; no environment activation or candidate launch',
        'preflight':'exact complete map/blob equality; required fields; exact AU registers/flags/clocks; readiness/cap/timing gates; three explicit caller attestations default false',
        'ledger':'strict ordered event and snapshot matching, sticky failure, forbids IRQ/scheduler/device/ARM7; armed-only and exact terminal completeness',
        'missing_live_certification':[
            'trusted entry cap provenance and exact timing classification/cost evaluation from copied CP15/latches',
            'complete passive peripheral/periodic-service readiness and ARM7 catch-up predicate',
            'canonical logical serialization rather than raw padded object representations',
            'verified immutable AU RAM/DTCM/save/code/ROM identity manifest bound to preflight',
            'complete per-instruction fetch/data/model/cycle transcript bound to a runtime controller',
            'prospective cost/debt/cap guard and exact terminal/failure controller replacing AU halt without bypassing its guards',
            'actual runtime snapshot/ledger-to-disposal coupling tested ROM-free, not only the process primitive'
        ],
        'AX':{'certificate_issued':False,'execution_authorized':False,
              'status':'WITHHELD; conditional AV specification only, not an executable certificate',
              'candidate':av['AW']},
        'evidence_limits':'Synthetic fixture is not an AU peripheral reconstruction. No compiled parity, actual scheduler-tail execution, or full live-state comparability certification.',
        'source_sha256':source_hashes
    }


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--export',action='store_true')
    args=parser.parse_args()
    result=analyze()
    if args.export:
        (ROOT/'docs/BrainAge_TaskAW_Result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS AW source/metadata checks; PARTIAL runtime certification; AX WITHHELD. Zero Brain Age execution.')
