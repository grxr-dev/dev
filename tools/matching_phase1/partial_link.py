"""One real -r authored-object pilot; validated existing output is reused, not relinked."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from batch import ROOT,HERE,read_json,validate_manifest,verify_inputs,verify_hashes,sha,command
from partial_link_audit import inspect,validate_inputs,validate_output,CLUSTER_NAMES

PRESERVED_PHASE1='234671ea4194fe37283b4fa9ec38c0a96a1fd494'
INPUT_ROOT=ROOT/'local/matching_phase1/runs/utility-batch'
BASELINE_OUTPUT=ROOT/'local/matching_phase1/runs/partial-link'
BASELINE_SHA256='36acd51ab2f5d1f14490e5ad3b5e660e24a054efe794216757c0b2d66ad4de4c'
DEFAULT_OUTPUT=ROOT/'local/matching_phase1/runs/partial-link-context-protocol-v1'
LINK_FLAGS=['-r','-m','armelf','--build-id=none','--no-gc-sections','--icf=none',
            '--no-merge-exidx-entries','--no-allow-multiple-definition']


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def inputs(manifest):
    report=read_json(INPUT_ROOT/'batch_status.json')
    count=len(manifest['symbols'])
    if report['classification']!='BATCH_CHECKS_COMPLETED_NOT_AUTHENTIC_MATCH' or report['summary']['compile_pass']!=count or report['summary']['semantic_pass']!=count or report['summary']['errors'] or report['summary']['exact_matches']+report['summary']['exact_mismatches']!=count or report['compiler']!=manifest['compiler']:
        raise ValueError('run the current successful manifest batch before partial linking')
    header=ROOT/manifest['shared_header']
    if sha(header.read_text().encode())!=report['shared_header_sha256_lf']:raise ValueError('shared declarations changed since compile')
    by_name={row['symbol']:row for row in report['symbols']}
    if len(by_name)!=count or len(report['symbols'])!=count:raise ValueError('duplicate/missing batch status records')
    models=[];paths=[];records=[]
    for row in manifest['symbols']:
        prior=by_name[row['symbol']]
        if sha((ROOT/row['source']).read_text().encode())!=prior['source_sha256_lf']:
            raise ValueError('source changed since independent compilation')
        path=INPUT_ROOT/row['symbol']/'leaf.o';data=path.read_bytes()
        if sha(data)!=prior['object_sha256']:raise ValueError('compiled input object identity changed')
        model=inspect(data,allowed_calls=call_names(manifest))
        if set(model['functions'])!={row['symbol']} or model['functions'][row['symbol']]['size']!=prior['generated_size']:
            raise ValueError('per-source object does not contain exactly its own function')
        models.append(model);paths.append(path.resolve())
        records.append({'symbol':row['symbol'],'source':row['source'],'object':path.relative_to(ROOT).as_posix(),
            'object_sha256':sha(data),'size':len(data),'function_size':prior['generated_size'],
            'compile_status':prior['compile_status'],'semantic_status':prior['semantic_status'],
            'unchanged_original_byte_diagnostic':prior['exact_status']})
    if len(set(paths))!=count:raise ValueError('independent object paths required')
    validate_inputs(models,manifest)
    return models,paths,records


def call_names(manifest):
    return {row['symbol'] for row in manifest['symbols']}|set().union(*(set(row['direct_call_targets']) for row in manifest['symbols']))


def baseline_records(manifest):
    records=[]
    for entry in manifest['partial_link']['baselines']:
        path=(ROOT/entry['report']).resolve()
        if not path.is_relative_to(ROOT/'docs/matching_phase1') or sha(path.read_text().encode())!=entry['report_sha256_lf']:
            raise ValueError('immutable baseline report identity/path changed')
        report=read_json(path);object_path=(ROOT/report['output_path']).resolve()
        if not object_path.is_relative_to(ROOT/'local/matching_phase1/runs') or report['output']['output_sha256']!=entry['output_sha256'] or sha(object_path.read_bytes())!=entry['output_sha256']:
            raise ValueError('immutable baseline object identity/path changed')
        records.append((entry,report,object_path))
    if len(records)!=2 or [entry['symbol_count'] for entry,_,_ in records]!=[6,8]:raise ValueError('required six/eight baseline chain missing')
    return records


def baseline_check(models,manifest=None):
    manifest=manifest or read_json(HERE/'batch.json')
    current={name:body for model in models for name,body in model['bodies'].items()}
    current_objects={name:model['sha256'] for model in models for name in model['functions']};audits=[]
    for entry,report,object_path in baseline_records(manifest):
        original=inspect(object_path.read_bytes(),allowed_calls=call_names(manifest))
        names=set(original['functions']);rows=report['output']['functions']
        if len(names)!=entry['symbol_count'] or len(rows)!=len(names) or {row['symbol'] for row in rows}!=names or {row['symbol'] for row in report['inputs']}!=names:
            raise ValueError('baseline coverage')
        for row in rows:
            if row['symbol'] not in current or current[row['symbol']]!=original['bodies'][row['symbol']] or sha(current[row['symbol']])!=row['input_raw_sha256']:
                raise ValueError('old six/eight raw function bodies changed')
        if any(current_objects.get(row['symbol'])!=row['object_sha256'] for row in report['inputs']):raise ValueError('old input object identity changed')
        audits.append(dict(entry,old_raw_bodies_identical=True,old_input_objects_identical=True,baseline_relinked=False))
    return {'output_sha256':BASELINE_SHA256,'old_six_raw_bodies_identical':True,'old_eight_raw_bodies_identical':True,'baseline_relinked':False,'baselines':audits}


def run(output=None,publish=False):
    manifest=read_json(HERE/'batch.json');validate_manifest(manifest)
    destination=(ROOT/manifest['partial_link']['status']).resolve()
    if not destination.is_relative_to(ROOT/'docs/matching_phase1') or any(destination==(ROOT/entry['report']).resolve() for entry in manifest['partial_link']['baselines']):
        raise ValueError('cannot overwrite immutable baseline status')
    out=Path(output or ROOT/manifest['partial_link']['output']).resolve()
    allowed=(ROOT/'local/matching_phase1/runs').resolve()
    protected_directories=[path.parent for _,_,path in baseline_records(manifest)]+[INPUT_ROOT.resolve()]
    if not out.is_relative_to(allowed) or out==allowed or any(out.is_relative_to(path) or path.is_relative_to(out) for path in protected_directories):
        raise ValueError('dedicated output below ignored local/matching_phase1/runs required')
    out.mkdir(parents=True,exist_ok=True)
    protected,_=verify_inputs(manifest)
    model_inputs,paths,records=inputs(manifest)
    baseline=baseline_check(model_inputs,manifest)
    tool=ROOT/manifest['compiler']['compiler']
    env=dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(ROOT/'local/matching_phase0/toolchains/zig-cache'),
        ZIG_LOCAL_CACHE_DIR=str(out/'cache'),TEMP=str(out),TMP=str(out))
    version=command([tool,'ld.lld','--version'],out,env,15)
    if version['exit_code'] or not version['stdout'].startswith('LLD 20.1.2 '):raise ValueError('bundled LLD version mismatch')
    identity=sha(json.dumps({'inputs':records,'flags':LINK_FLAGS,'zig_sha256':manifest['compiler']['compiler_sha256'],
        'lld_banner':version['stdout'].strip(),'baselines':baseline},sort_keys=True,separators=(',',':')).encode())
    object_path=out/'linked-authored.o';map_path=out/'linked-authored.map'
    argv=[tool,'ld.lld',*LINK_FLAGS,'--Map='+str(map_path),'-o',object_path,*paths]
    marker=out/'attempt.json';reused=False;link_record=None
    try:
        if marker.exists():
            attempt=read_json(marker)
            if attempt.get('identity')!=identity or attempt.get('status')!='VALIDATED':
                raise ValueError('earlier/stale/unvalidated attempt exists; no automatic retry')
            if not object_path.exists() or sha(object_path.read_bytes())!=attempt['output_sha256']:
                raise ValueError('validated linked output changed; no relink fallback')
            link_record=read_json(out/'link-command.json');reused=True
        else:
            if object_path.exists() or map_path.exists():raise ValueError('untracked existing link artifacts; preserve and inspect')
            attempt={'schema':'authored-partial-link-attempt/1','identity':identity,'status':'DISPATCHING','link_invocations':1}
            with marker.open('x',encoding='utf-8') as handle:
                handle.write(json.dumps(attempt,indent=2));handle.flush();os.fsync(handle.fileno())
            link_record=command(argv,out,env)
            write(out/'link-command.json',link_record)
            if link_record['exit_code']!=0:raise ValueError('LLD -r failed: '+link_record['stderr'])
        audit=validate_output(model_inputs,inspect(object_path.read_bytes(),allowed_calls=call_names(manifest)),manifest)
        if not map_path.is_file():raise ValueError('link map missing')
        report={'schema':'brainage-authored-partial-link/1','classification':'PASS_AUTHORED_RELOCATABLE_PARTIAL_LINK',
            'preserved_phase1_commit':PRESERVED_PHASE1,'input_identity':identity,'inputs':records,'immutable_baseline':baseline,
            'linker':{'driver':manifest['compiler']['compiler'],'driver_sha256':manifest['compiler']['compiler_sha256'],
                      'version':version['stdout'].strip(),'flags':LINK_FLAGS,'exit_code':link_record['exit_code'],
                      'stderr':link_record['stderr'],'stdout':link_record['stdout']},
            'output':audit,'map_sha256':sha(map_path.read_bytes()),'output_path':object_path.relative_to(ROOT).as_posix(),
            'link_invocations_for_this_artifact':1,'new_link_invocations_this_run':0 if reused else 1,
            'protected_input_count':len(protected),'protected_inputs_unchanged':True,'original_object_or_module_claimed':False,
            'original_toolchain_verified_matches':0,'gate0':'OPEN'}
        verify_hashes(protected)
        baseline_check(model_inputs,manifest)
        for path,record in zip(paths,records):
            if sha(path.read_bytes())!=record['object_sha256']:raise ValueError('input object changed during link')
        if not reused:write(marker,dict(attempt,status='VALIDATED',output_sha256=audit['output_sha256']))
        write(out/'partial_link_status.json',report)
        if publish:write(destination,report)
        print('PASS_AUTHORED_RELOCATABLE_PARTIAL_LINK: '+str(len(records))+' independent inputs, '+str(len(audit['undefined_symbols']))+' opaque imports; output='+audit['output_sha256'])
        print('new linker invocations='+str(report['new_link_invocations_this_run'])+'; genuine matches=0; Gate0 OPEN')
        return 0
    finally:
        verify_hashes(protected)


def cli(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--publish-status',action='store_true')
    args=parser.parse_args(argv)
    try:return run(args.output,args.publish_status)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        print('PARTIAL_LINK_ERROR: '+type(error).__name__+': '+str(error),file=sys.stderr)
        (ROOT/'local/matching_phase1').mkdir(parents=True,exist_ok=True)
        write(ROOT/'local/matching_phase1/partial-link-error.json',{'classification':'PARTIAL_LINK_ERROR',
            'error':type(error).__name__+': '+str(error),'genuine_original_matches':0,'gate0':'OPEN','automatic_retry':False})
        return 2


if __name__=='__main__':raise SystemExit(cli())
