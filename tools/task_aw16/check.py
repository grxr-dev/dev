"""ROM-free controller certification only. Never link or launch nds_runner."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

from hooks import ROOT, HERE, module, write_overlay
import fixture
from oracle import check_states

SOURCE = ROOT / 'local/ndsrecomp/runner/src'
sys.path.insert(0, str(ROOT / 'tools/task_aw15'))
import model


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, output, name, timeout=180):
    environment = {key: value for key, value in os.environ.items() if not key.startswith('NDS_')}
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout, env=environment)
    (output / (name + '.json')).write_text(json.dumps({'command': [str(part) for part in command],
        'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2))
    return result


def prepare(output):
    authority = json.loads(subprocess.check_output(['git','show',
        '12710efe8a81c15f91a86a637704573899f9cf38:docs/BrainAge_TaskAW15_Result.json'],cwd=ROOT))
    source_evidence = ROOT / authority['evidence']['local'] / 'tests.json'
    require(sha(source_evidence)==authority['evidence']['tests_sha256'],'authenticated AW15 source observations')
    source_identities = {name.replace('\\','/'):identity for name,identity in
                         json.loads(source_evidence.read_text())['protected_artifacts_unchanged'].items()}
    for name in ['runtime_arm.cpp','scheduler.cpp','tier3.cpp','gpu3d.cpp','io.cpp','spu.cpp','wifi_net.cpp','live_overlay.cpp']:
        path = SOURCE / name
        if name=='gpu3d.cpp':
            pinned = subprocess.check_output(['git','-C',str(ROOT / 'local/ndsrecomp'),'show',
                '3a57236bb23d25dcb4caad7d58d733311062ff5e:runner/src/gpu3d.cpp']).decode('utf-8-sig')
            require(path.read_text(encoding='utf-8-sig').splitlines()==pinned.splitlines(),'pinned GPU wrapper source drift')
        else:
            require(sha(path)==source_identities[str(path.relative_to(ROOT)).replace('\\','/')], 'authoritative source drift: ' + name)
    saved = sys.modules['hooks']
    sys.modules['hooks'] = module('aw16_original_hooks', ROOT / 'tools/task_aw12/hooks.py')
    try:
        prior = module('aw16_aw12_checks', ROOT / 'tools/task_aw12/check.py')
    finally:
        sys.modules['hooks'] = saved
    protected, functions, old_hashes, old_overlay = prior.prepare(output)
    protected[str(source_evidence.relative_to(ROOT))] = sha(source_evidence)
    core, identities, gpu, metadata = model.binding()
    (output / 'gpu.hex').write_text(model.state.encode(gpu, []).hex())
    dynamic = {f'timer.{index}.{field}' for index in range(8) for field in ['control','counter','reload','accum','last']}
    dynamic.update(['service.display_last','service.rtc_processed','service.rtc_due'])
    dynamic.update([name + '.deadline' for name in ['div','auxspi','spi','card','sqrt']])
    record = model.state.load()
    readonly = [name for name, owner in record['field_owners'] if owner in ['bus','io','cp15'] and name not in dynamic]
    require(len(readonly) == 219 and len(dynamic) == 48, 'explicit mutable/immutable getter ownership partition')
    (output / 'immutable_keys.inc').write_text(',\n'.join(json.dumps(name) for name in readonly) + '\n')
    overlay = output / 'owned-overlay'
    overlay.mkdir()
    original, patched = write_overlay(overlay, SOURCE)
    fragments = fixture.create(output, patched)
    for name in original:
        protected[str((SOURCE / name).relative_to(ROOT))] = sha(SOURCE / name)
    for name in ['tools/task_aw14/fence.json','tools/task_aw15/certificate.json','tools/task_aw15/model.py']:
        protected[name] = sha(ROOT / name)
    parser = module('aw16_extract', ROOT / 'tools/task_aw6/check.py')
    for target, name, signature in fragments:
        text = patched[name] if name in patched else (SOURCE / name).read_text(encoding='utf-8-sig')
        body = parser.function(text, signature)
        functions['aw16:' + signature] = hashlib.sha256(body.encode()).hexdigest()
    return protected, functions, overlay


def syntax(output, overlay, compiler):
    prior = module('aw16_syntax_checks', ROOT / 'tools/task_aw12/check.py')
    outcomes = prior.runtime_syntax(output, overlay, compiler)
    includes = [overlay, SOURCE, ROOT / 'build/task-o-sdl-runner/generated', SOURCE.parent / 'vendor/melonds',
        ROOT / 'local/ndsrecomp/recompiler/armv4t', ROOT / 'local/ndsrecomp/external/arm-recomp-core/common',
        ROOT / 'local/ndsrecomp/recompiler/support', ROOT / 'local/ndsrecomp/vendor/freebios',
        ROOT / 'local/recomp-ui/src', ROOT / 'local/recomp-ui/src/common',
        ROOT / 'local/toolchain/SDL3-3.4.18/x86_64-w64-mingw32/include',
        SOURCE.parent / 'vendor/melonds/net/libslirp/src', ROOT / 'build/task-o-sdl-runner/vendor/melonds/net/libslirp',
        ROOT / 'local/ndsrecomp/recompiler/third_party']
    flags = [str(compiler), '-std=c++20', '-fsyntax-only'] + ['-I' + str(path) for path in includes]
    for name in ['runtime_arm.cpp','scheduler.cpp','tier3.cpp','gpu3d.cpp','wifi_net.cpp','live_overlay.cpp']:
        result = run(flags + ['-DAW12_DIAGNOSTIC_CAPTURE_ONLY','-DAW16_DIAGNOSTIC_TAIL',str(overlay / name)],
                     output, 'syntax-successor-' + name)
        require(result.returncode == 0, 'actual successor overlay syntax: ' + name)
        outcomes['successor/' + name] = 0
        if name in ['wifi_net.cpp','live_overlay.cpp']:
            result = run(flags + [str(overlay / name)],output,'syntax-default-' + name)
            require(result.returncode == 0,'actual auxiliary default syntax: ' + name)
            outcomes['default/' + name] = 0
    return outcomes


def inspect_audit(path, success):
    records = [json.loads(line) for line in path.read_text().splitlines()]
    disposal = [row for row in records if row['event'] == 'aw16_disposal']
    if not success:
        require(records[-1]['event'] in ['aw16_disposal','failure','terminal'], 'flushed fail-closed audit')
        return {'terminal_event': records[-1]['event'], 'reason': next((row.get('reason') for row in reversed(records) if 'reason' in row), None)}
    require(len(disposal) == 1 and disposal[0]['success'] and disposal[0]['guest'] == disposal[0]['MMIO'] == 0,
            'successor nonreturning terminal')
    seal = next(row for row in records if row['event'] == 'aw16_entry_seal')
    seal_index = records.index(seal)
    metadata = model.binding()[3]
    original_labels = [row['event'] for row in metadata['ownership']['transcript']]
    original_types = ['canonical_snapshot','observation']
    for label in original_labels:
        original_types.append('canonical_snapshot')
        if label in ['gpu_observed','scheduler_admitted_capture_only']:
            original_types.append('gpu_snapshot')
        original_types.append(label)
    require([row['event'] for row in records[:seal_index]] == original_types,'dominating original receipt grammar')
    original_stages = [row for row in records[:seal_index] if row['event'] in original_labels]
    for original, expected in zip(original_stages,metadata['ownership']['transcript']):
        require(all(original[key]==number for key,number in expected.items()) and original['ticket']==1 and original['frame']==566,
                'exact AW14 predecessor chain/latches')
    expected_labels = ['successor_admitted','scheduler_device','timer9_entry','timers9_done','gpu_done',
        'slice7_gate','arm7_entry','arm7_done','timer7_entry','timers7_done','power_checked','display_done','spu_done',
        'wifi_done','rtc_entry','rtc_done','system_entry','system_done','time_published','overlay_done','round_left',
        'next_scheduler','round_entered','target_selected','slice9_gate','slice_begun_stop']
    stages = [row for row in records if row['event'] == 'aw16_stage']
    require([row['event'] for row in records[seal_index+1:]] ==
            ['canonical_snapshot','aw16_gpu','aw16_auxiliary','aw16_stage'] * 26 + ['aw16_terminal','aw16_disposal'],
            'exact successor record grammar; no missing repeated snapshots')
    require([row['label'] for row in stages] == expected_labels and len(stages) == 26, 'complete exact successor phase transcript')
    require(seal['ticket'] == 1 and seal['frame'] == 566, 'actual predecessor receipt')
    previous = seal['predecessor']
    core = geometry = extra = None
    states = []
    for record in records:
        if record['event'] == 'canonical_snapshot':
            core = bytes.fromhex(record['canonical_hex'])
            require(hashlib.sha256(core).hexdigest()==record['sha256'],'core canonical identity')
        elif record['event'] == 'aw16_gpu':
            geometry = bytes.fromhex(record['canonical_hex'])
            require(hashlib.sha256(geometry).hexdigest() == record['sha256'], 'GPU hash')
        elif record['event'] == 'aw16_auxiliary':
            extra = bytes.fromhex(record['canonical_hex'])
            require(hashlib.sha256(extra).hexdigest() == record['sha256'], 'auxiliary hash')
        elif record['event'] == 'aw16_stage':
            index = len(states)
            require(record['index'] == index and record['previous'] == previous, 'no ordinal gap/replay')
            label = record['label'].encode()
            observed_kinds = {'scheduler_device':7,'timer9_entry':7,'arm7_entry':8,'timer7_entry':7,'rtc_entry':7,'system_entry':7,'next_scheduler':6}
            observed = record['label'] in observed_kinds
            kind = observed_kinds.get(record['label'],0)
            require(record['observed']==observed and record['kind']==kind,'actual original observer kind/phase')
            material = previous.encode() + core + geometry + extra + struct.pack('<QBBH', index, observed, kind, len(label)) + label
            previous = hashlib.sha256(material).hexdigest()
            require(previous == record['chain'], 'chained full-state integrity')
            fields, identities = model.state.decode(core)
            gpu_fields, _ = model.state.decode(geometry)
            aux_fields, _ = model.state.decode(extra)
            states.append({'label': record['label'], 'fields': fields, 'identities': identities,
                           'gpu': gpu_fields, 'auxiliary': aux_fields,'core_sha256': hashlib.sha256(core).hexdigest(),
                           'auxiliary_sha256': hashlib.sha256(extra).hexdigest()})
    require(states[0]['core_sha256'] == model.FENCE and len(states[0]['fields']) == 411, 'AW14 complete entry')
    require(states[-1]['core_sha256'] == '68b88b2de2264fb8fc456422de7aa026a8ac00685268f8cd8ea5650d3b01f773' and
            len(states[-1]['fields']) == 361, 'AW15 complete conditional final core')
    require(all(row['identities'] == states[0]['identities'] for row in states), 'all five identities invariant')
    require(disposal[0]['chain'] == previous and disposal[0]['stages'] == 26, 'terminal chain')
    require(seal['predecessor'] == '10bad78f6ef2fd96a21b26be7e074943e6ded5fa5541844c731d3e39892472b4' and
            seal['auxiliary'] == states[0]['auxiliary_sha256'], 'immutable predecessor/auxiliary entry seal')
    check_states(states)
    return {'stages': 26, 'final_core_sha256': states[-1]['core_sha256'], 'entry_auxiliary_sha256': states[0]['auxiliary_sha256'],
            'final_auxiliary_sha256': states[-1]['auxiliary_sha256'], 'final_chain': previous, 'states': states}


def audit_negatives(output):
    records = [json.loads(line) for line in (output / 'success.jsonl').read_text().splitlines()]
    cases = []
    for event in ['aw16_stage','aw16_auxiliary','aw16_gpu','canonical_snapshot']:
        position = next(index for index,row in enumerate(records) if row['event']==event and index>records.index(next(row for row in records if row['event']=='aw16_entry_seal')))
        cases.append(('missing-' + event,records[:position] + records[position+1:]))
        cases.append(('duplicate-' + event,records[:position] + [records[position]] + records[position:]))
    for field, number in [('chain','0'*64),('index',99),('kind',5),('observed',False)]:
        changed = copy.deepcopy(records)
        row = next(row for row in changed if row['event']=='aw16_stage' and row['label']=='scheduler_device')
        row[field] = number
        cases.append((field,changed))
    changed = copy.deepcopy(records)
    next(row for row in changed if row['event']=='aw16_entry_seal')['auxiliary']='0'*64
    cases.append(('entry-seal',changed))
    changed = copy.deepcopy(records)
    position = next(index for index,row in enumerate(changed) if row['event']=='aw16_stage')
    changed[position],changed[position+4] = changed[position+4],changed[position]
    cases.append(('reordered',changed))
    for name, changed in cases:
        path = output / ('tampered-' + name + '.jsonl')
        path.write_text('\n'.join(json.dumps(row) for row in changed) + '\n')
        rejected = False
        try:
            inspect_audit(path,True)
        except (ValueError,TypeError,KeyError):
            rejected = True
        require(rejected,'independent audit tamper accepted: ' + name)
    return len(cases)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--syntax', action='store_true')
    output = parser.parse_args().out.resolve()
    require(output.is_relative_to(ROOT / 'local/task-aw16') and not output.exists(), 'fresh local ROM-free evidence')
    output.mkdir(parents=True)
    tested_inputs = {path.name:sha(path) for path in HERE.iterdir() if path.is_file() and path.suffix in ['.h','.inc','.py','.cpp']}
    subprocess.run(['git','merge-base','--is-ancestor','12710efe8a81c15f91a86a637704573899f9cf38','HEAD'],cwd=ROOT,check=True)
    protected, functions, overlay = prepare(output)
    compiler = ROOT / 'local/toolchain/w64devkit/bin/g++.exe'
    flags = [str(compiler),'-std=c++20','-O2','-DAW16_ROMFREE','-I' + str(output),'-I' + str(overlay),
             '-I' + str(HERE),'-I' + str(SOURCE),'-I' + str(SOURCE.parent),
             '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support')]
    binaries = {}
    for name, defines in [('diagnostic',['-DAW12_DIAGNOSTIC_CAPTURE_ONLY','-DAW16_DIAGNOSTIC_TAIL']),('default',[])]:
        binary = output / (name + '.exe')
        result = run(flags + defines + [str(HERE / 'inspect.cpp'),'-o',str(binary)],output,'compile-' + name)
        require(result.returncode == 0, 'ROM-free compile: compile-' + name + '.json')
        binaries[name] = binary
    arguments = [str(output / 'terminal.hex'),str(output / 'initial.hex'),str(output / 'gpu.hex')]
    result = run([str(binaries['diagnostic']),'units',*arguments,str(output / 'unused')],output,'units')
    require(result.returncode == 0,'native auxiliary/contract units: units.json')
    unit_result = json.loads(result.stdout)
    matrix = ['success','no-bridge','no-device','trace-wrap','legacy-fence','disabled',
        'overlay-entry','wifi-entry','worker-entry','network-entry','trace-overflow','old-ledger','stale-epoch','ledger','ledger-plan','ledger-seal','journal-bound',
        'duplicate-owner','duplicate-arm','missing-owner','overlay-after','wifi-after','trace-after','cap-short','irq','timer','readiness','fetch','dispatch','MMIO',
        'unexpected-service','reordered','quantum','cap-new','omit-phase']
    outcomes = {}
    for mode in matrix:
        binary = binaries['default' if mode == 'disabled' else 'diagnostic']
        audit = output / (mode + '.jsonl')
        child = run([str(binary),mode,*arguments,str(audit)],output,'child-' + mode)
        positive = mode in ['success','no-bridge','no-device','trace-wrap']
        expected = 0 if mode == 'disabled' else 73 if positive or mode=='legacy-fence' else 79
        require(child.returncode == expected, mode + ' exit: child-' + mode + '.json')
        require('SENTINEL' not in child.stdout + child.stderr, mode + ' post-terminal sentinel')
        outcomes[mode] = {'exit': child.returncode}
        if mode != 'disabled':
            outcomes[mode].update(inspect_audit(audit,positive))
    syntax_results = syntax(output,overlay,compiler) if '--syntax' in sys.argv else {}
    audit_cases = audit_negatives(output)
    for name, identity in protected.items():
        require(sha(ROOT / name) == identity, 'source/evidence/consumed lock mutated: ' + name)
    require(all(sha(HERE / name)==identity for name,identity in tested_inputs.items()),'source inputs changed while tests ran')
    summary = {'task':'AW16','all_passed':True,'native_assertions':unit_result['assertions'],'children':outcomes,
        'runtime_syntax':syntax_results,'source_functions':functions,'protected_artifacts_unchanged':protected,
        'independent_audit_negative_cases':audit_cases,'independent_full_state_oracles':4,
        'tested_inputs':tested_inputs,
        'guest_instructions':0,'BrainAge_MMIO':0,'live_replays':0,'runtime_hooks_installed':False}
    (output / 'summary.json').write_text(json.dumps(summary,indent=2) + '\n')
    print(json.dumps({'all_passed':True,'native_assertions':unit_result['assertions'],'children':len(outcomes),
        'source_compiles':len(syntax_results),'final_core':outcomes['success']['final_core_sha256']},indent=2))


if __name__ == '__main__':
    main()
