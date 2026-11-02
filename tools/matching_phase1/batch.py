"""Six-source compile/model/exact ledger plus authored-object comparison controls."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PHASE0=ROOT/'tools/matching_phase0'
sys.path.insert(0,str(PHASE0))
import diagnostic
from elf_function import function
from nul_count_pilot import decode
from behavior import verify as behavior_check
from object_inventory import inventory,layout


def sha(data):return hashlib.sha256(data).hexdigest()


def read_json(path):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('duplicate JSON key: '+key)
            result[key]=value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique)


def validate_manifest(manifest):
    if manifest['schema']!='brainage-source-batch/1' or not 6<=len(manifest['symbols'])<=8:
        raise ValueError('batch schema/coverage')
    seen=set();spans=[]
    for row in manifest['symbols']:
        name=row['symbol'];address=int(row['address'],16);size=row['reference_size']
        if name in seen or name!=f'func_{address:08x}' or address&3 or size%4 or size<=0 or row['mode']!='ARM_LE':
            raise ValueError('duplicate symbol or invalid ARM boundary')
        if not re.fullmatch('[0-9a-f]{64}',row['reference_sha256']):raise ValueError('reference hash syntax')
        seen.add(name);spans.append((address,address+size))
        source=(ROOT/row['source']).resolve()
        if not source.is_relative_to((ROOT/'src/arm9/utility_hypotheses').resolve()) or not source.is_file():raise ValueError('canonical source path')
        literals=sorted(int(at,16) for at in row['literal_words'])
        if row['code_bytes']%4 or literals!=list(range(address+row['code_bytes'],address+size,4)):
            raise ValueError('code/pool partition mismatch')
        config=read_json(ROOT/row['legacy_config'])
        expected={'address':address,'size':size,'symbol':name,'reference_sha256':row['reference_sha256']}
        if any((int(config[key],16) if key=='address' else config[key])!=value for key,value in expected.items()):raise ValueError('legacy symbol/reference identity changed')
        if config.get('arm_call_targets',{})!=row['direct_call_targets'] or config.get('original_literal_words',{})!=row['literal_words'] or config.get('expected_original_relocations',[])!=row['original_relocations']:
            raise ValueError('relocation/literal policy changed')
        for key in ('compiler','compiler_sha256','zig_version','archive_sha256','flags'):
            if manifest['compiler'][key]!=config[key]:raise ValueError('compiler profile differs across batch')
        for key in ('rom_name','rom_sha1','rom_sha256'):
            if manifest['inputs'][key]!=config[key]:raise ValueError('ROM gate differs across batch')
        if config.get('metadata_sha256',manifest['inputs']['metadata_sha256'])!=manifest['inputs']['metadata_sha256']:
            raise ValueError('metadata pins differ')
    spans.sort()
    if any(left[1]>right[0] for left,right in zip(spans,spans[1:])):raise ValueError('overlapping reference symbols')
    pilots={read_json(path)['symbol'] for path in PHASE0.glob('*config.json')}
    if not pilots<=seen:raise ValueError('an existing Phase0 symbol was omitted')
    cluster=(ROOT/manifest['cluster_source']).read_text()
    includes=re.findall(r'^#include "(func_[0-9a-f]{8}\.c)"$',cluster,re.M)
    if len(includes)!=len(seen) or {name[:-2] for name in includes}!=seen:raise ValueError('cluster source coverage/duplicate include')


def hashes(paths):return {str(path):sha(path.read_bytes()) for path in paths}


def verify_hashes(expected):
    for path,digest in expected.items():
        if sha(Path(path).read_bytes())!=digest:raise ValueError('protected input changed: '+str(path))


def verify_inputs(manifest):
    config=manifest['inputs'];rom=ROOT.parent/config['rom_name'];module=ROOT/config['arm9_path']
    expected={str(rom):config['rom_sha256'],str(module):config['arm9_sha256']}
    expected.update({str(ROOT/path):digest for path,digest in config['metadata_sha256'].items()})
    actual_metadata={str(path) for path in (ROOT/config['metadata_root']).rglob('*') if path.is_file()}
    if len(config['metadata_sha256'])!=10 or actual_metadata!={str(ROOT/path) for path in config['metadata_sha256']}:
        raise ValueError('exact ten-file metadata inventory changed')
    verify_hashes(expected)
    raw=rom.read_bytes();image=module.read_bytes()
    if hashlib.sha1(raw).hexdigest()!=config['rom_sha1']:raise ValueError('ROM SHA1')
    offset,entry,base,size=struct.unpack_from('<4I',raw,0x20)
    if base!=0x02000000 or len(image)>size or raw[offset:offset+len(image)]!=image:raise ValueError('extracted ARM9 is not exact ROM prefix')
    for row in manifest['symbols']:
        start=int(row['address'],16)-base;length=row['reference_size']
        if not 0<=start<=len(image)-length or sha(image[start:start+length])!=row['reference_sha256']:
            raise ValueError('reference range/hash mismatch: '+row['symbol'])
    section_text=(ROOT/config['metadata_root']/'arm9/delinks.txt').read_text()
    section=re.search(r'\.text\s+start:0x([0-9a-f]+) end:0x([0-9a-f]+) kind:code align:(\d+)',section_text)
    if not section or any(not int(section[1],16)<=int(row['address'],16)<int(row['address'],16)+row['reference_size']<=int(section[2],16) for row in manifest['symbols']):
        raise ValueError('reference .text section attribution changed')
    compiler=ROOT/manifest['compiler']['compiler']
    if sha(compiler.read_bytes())!=manifest['compiler']['compiler_sha256']:raise ValueError('compiler checksum gate')
    return expected,image


def statuses(report, behavior):
    compile_status='PASS' if report['compile']['exit_code']==0 else 'FAIL'
    exact='NOT_CHECKED'
    if compile_status=='PASS' and 'comparison' in report:
        exact='MATCH' if report['comparison']['equal'] else 'MISMATCH'
    return {'compile_status':compile_status,'semantic_status':behavior['status'] if behavior else 'NOT_CHECKED',
            'exact_status':exact,'genuine_original_match':False}


def summarize(rows):
    return {'source_symbols':len(rows),'compile_pass':sum(row['compile_status']=='PASS' for row in rows),
        'semantic_pass':sum(row['semantic_status']=='PASS_BOUNDED_MODEL' for row in rows),
        'exact_matches':sum(row['exact_status']=='MATCH' for row in rows),
        'exact_mismatches':sum(row['exact_status']=='MISMATCH' for row in rows),
        'errors':sum(row.get('error') is not None or row['compile_status']!='PASS' or row['semantic_status']!='PASS_BOUNDED_MODEL' for row in rows),
        'genuine_original_matches':0,'gate0':'OPEN'}


def command(argv, directory, env, timeout=120):
    process=subprocess.run([str(value) for value in argv],cwd=directory,env=env,capture_output=True,
        encoding='utf-8',errors='replace',timeout=timeout,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    return {'argv':[str(value) for value in argv],'exit_code':process.returncode,'stdout':process.stdout,'stderr':process.stderr}


def objdiff_scores(report, expected_names, repeat):
    values=[row for row in report['left']['symbols'] if row.get('kind')=='SYMBOL_FUNCTION']
    if len(values)!=len(expected_names) or {row['name'] for row in values}!=expected_names:raise ValueError('objdiff function coverage mismatch')
    result={row['name']:row['match_percent'] for row in values}
    if any(type(value) not in (int,float) or not 0<=value<=100 for value in result.values()):raise ValueError('invalid objdiff scores')
    if repeat and any(value!=100 for value in result.values()):raise ValueError('authored repeat control is not identical')
    if not repeat and all(value==100 for value in result.values()):raise ValueError('negative object control was not distinguished')
    return result


def object_pilot(manifest, out):
    config=manifest['compiler'];compiler=ROOT/config['compiler'];source=ROOT/manifest['cluster_source']
    env=dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(ROOT/'local/matching_phase0/toolchains/zig-cache'),
        ZIG_LOCAL_CACHE_DIR=str(out/'cache'),TMP=str(out),TEMP=str(out))
    builds=[];paths=[];inventories=[]
    for name,extra in [('authored-a',[]),('authored-b',[]),('authored-o0-negative',['-O0','-fno-sanitize=all'])]:
        path=out/(name+'.o');path.unlink(missing_ok=True)
        record=command([compiler,'cc',*config['flags'],'-fno-inline','-ffunction-sections',*extra,'-c',source,'-o',path],out,env)
        (out/(name+'.compile.json')).write_text(json.dumps(record,indent=2))
        if record['exit_code']:raise ValueError('cluster compile failed: '+record['stderr'])
        data=path.read_bytes();objects=inventory(data)
        if {symbol['name'] for symbol in objects['functions']}!={row['symbol'] for row in manifest['symbols']} or len(objects['functions'])!=len(manifest['symbols']):
            raise ValueError('cluster object definitions differ from manifest')
        expected_undefined=set().union(*(set(row['direct_call_targets']) for row in manifest['symbols']))-{row['symbol'] for row in manifest['symbols']}
        if set(objects['undefined_symbols'])!=expected_undefined:raise ValueError('unexpected cluster externs')
        builds.append({'name':name,'sha256':sha(data),'size':len(data),'compile_exit':record['exit_code'],'extra_flags':['-fno-inline','-ffunction-sections',*extra]})
        paths.append(path);inventories.append(objects)
    if builds[0]['sha256']!=builds[1]['sha256']:raise ValueError('independent authored rebuilds differ')
    if builds[0]['sha256']==builds[2]['sha256']:raise ValueError('negative object control unchanged')
    for index,objects in enumerate(inventories):
        (out/(builds[index]['name']+'.inventory.json')).write_text(json.dumps(objects,indent=2))
    tool=manifest['objdiff'];binary=ROOT/tool['path']
    result={'scope':'AUTHORED_REBUILD_AND_O0_NEGATIVE_CONTROL_ONLY','original_object_available':False,
        'original_object_comparison':'BLOCKED_UNKNOWN_ORIGINAL_OBJECT_PARTITION','builds':builds,
        'cluster_symbols':inventories[0]['functions'],'undefined_symbols':inventories[0]['undefined_symbols'],
        'relocations':inventories[0]['relocations'],'linked':False,'tool':tool}
    if not binary.exists():
        return result|{'cli_status':'NOT_INSTALLED','reason':'optional official CLI missing; byte diagnostics remain available'}
    if sha(binary.read_bytes())!=tool['sha256']:raise ValueError('objdiff checksum gate')
    version=command([binary,'--version'],out,env,15)
    if version['exit_code'] or not version['stdout'].strip().endswith(' '+tool['version']):raise ValueError('objdiff version mismatch')
    checks=[]
    for label,base in [('authored-repeat',paths[1]),('authored-o0-negative',paths[2])]:
        output=out/(label+'.objdiff.json')
        output.unlink(missing_ok=True)
        record=command([binary,'diff','-1',paths[0],'-2',base,'--format','json','-o',output],out,env)
        (out/(label+'.objdiff.command.json')).write_text(json.dumps(record,indent=2))
        if record['exit_code'] or not output.is_file():raise ValueError('objdiff failed: '+record['stderr'])
        data=output.read_bytes();parsed=json.loads(data)
        if not parsed:raise ValueError('empty objdiff output')
        scores=objdiff_scores(parsed,{row['symbol'] for row in manifest['symbols']},label=='authored-repeat')
        checks.append({'name':label,'exit_code':record['exit_code'],'report_sha256':sha(data),'report':str(output.relative_to(ROOT)),
                       'authored_control_match_percent_NOT_original':scores})
    project={'min_version':tool['version'],'build_target':False,'build_base':False,'units':[
        {'name':'AUTHORED_REPEAT_NOT_ORIGINAL','target_path':str(paths[0]),'base_path':str(paths[1])},
        {'name':'AUTHORED_O0_NEGATIVE_NOT_ORIGINAL','target_path':str(paths[0]),'base_path':str(paths[2])}]}
    (out/'objdiff.json').write_text(json.dumps(project,indent=2))
    project_output=out/'authored-project-check.objdiff.json';project_output.unlink(missing_ok=True)
    project_command=command([binary,'diff','-p',out,'-u','AUTHORED_REPEAT_NOT_ORIGINAL','-o',project_output,'--format','json'],out,env)
    (out/'authored-project-check.command.json').write_text(json.dumps(project_command,indent=2))
    if project_command['exit_code'] or not project_output.is_file():raise ValueError('objdiff project configuration failed')
    project_data=project_output.read_bytes()
    project_scores=objdiff_scores(json.loads(project_data),{row['symbol'] for row in manifest['symbols']},True)
    checks.append({'name':'authored-project-config','exit_code':project_command['exit_code'],'report_sha256':sha(project_data),
        'report':str(project_output.relative_to(ROOT)),'authored_control_match_percent_NOT_original':project_scores})
    return result|{'cli_status':'PASS_AUTHORED_OBJECT_PIPELINE_ONLY','version':version['stdout'].strip(),'checks':checks}


def regression_tests(out):
    suite=unittest.TestSuite()
    for directory in (PHASE0,HERE):
        suite.addTests(unittest.TestLoader().discover(str(directory),pattern='test_*.py',top_level_dir=str(directory)))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (out/'regressions.txt').write_text(stream.getvalue(),encoding='utf-8')
    return {'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'pass':result.wasSuccessful()}


def run(output=None, require_exact=False, publish_status=False):
    out=(output or ROOT/'local/matching_phase1/runs/utility-batch').resolve()
    if not out.is_relative_to((ROOT/'local/matching_phase1/runs').resolve()):raise ValueError('outputs must stay under ignored local/matching_phase1/runs/')
    out.mkdir(parents=True,exist_ok=True)
    manifest=read_json(HERE/'batch.json');validate_manifest(manifest)
    protected,image=verify_inputs(manifest)
    rows=[]
    counter_record=next(row for row in manifest['symbols'] if row['behavior_model']=='nul_count')
    counter_start=int(counter_record['address'],16)-0x02000000
    counter=decode(image[counter_start:counter_start+counter_record['code_bytes']],int(counter_record['address'],16))
    try:
        for entry in manifest['symbols']:
            directory=out/entry['symbol'];directory.mkdir(exist_ok=True)
            result_path=directory/'result.json';result_path.unlink(missing_ok=True)
            row=dict(entry,compile_status='ERROR',semantic_status='NOT_CHECKED',exact_status='NOT_CHECKED',genuine_original_match=False)
            source=ROOT/entry['source'];row['source_sha256_lf']=sha(source.read_text().replace('\r\n','\n').encode())
            log=io.StringIO()
            try:
                with contextlib.redirect_stdout(log):
                    diagnostic.run(source,directory,ROOT/entry['legacy_config'])
                report=read_json(result_path)
                row.update(statuses(report,None),behavior=None,compile_exit=report['compile']['exit_code'],
                    compiler_stderr=report['compile']['stderr'],compiler_stdout=report['compile']['stdout'],
                    generated_size=report.get('elf',{}).get('symbol_size'),generated_sha256=report.get('compiled_sha256'),
                    generated_raw_sha256=sha(bytes.fromhex(report['elf']['unresolved_symbol_hex'])) if report.get('elf') else None,
                    object_sha256=report.get('object_sha256'),generated_section=report.get('elf',{}).get('section'),
                    generated_elf_flags=report.get('elf',{}).get('elf_flags'),
                    resolved_call_relocations=report.get('elf',{}).get('resolved_code_relocations'),
                    generated_relocations=report.get('elf',{}).get('relocations',[]),
                    differing_offsets=len(report['comparison']['differences']) if report.get('comparison') else None,
                    generated_code_bytes=report['elf']['symbol_size']-len(entry['literal_words'])*4 if report.get('elf') else None)
                if row['compile_status']=='PASS':
                    partition=layout((directory/'leaf.o').read_bytes(),entry['symbol'])
                    row['generated_code_bytes']=sum(span['size'] for span in partition if span['kind']=='ARM_CODE')
                    row['generated_layout']=partition
                    body=bytes.fromhex(report['compiled_hex'])
                    row['generated_literal_words']={hex(int(entry['address'],16)+at):hex(struct.unpack_from('<I',body,at)[0])
                        for span in partition if span['kind']=='LITERAL_DATA' for at in range(span['offset'],span['offset']+span['size'],4)}
                    row['generated_fits_original_symbol_range']=row['generated_size']<=entry['reference_size']
                    row['semantic_status']='FAIL_BOUNDED_MODEL'
                    modeled=behavior_check(entry['behavior_model'],bytes.fromhex(report['reference_hex']),bytes.fromhex(report['compiled_hex']),int(entry['address'],16),counter)
                    row.update(semantic_status=modeled['status'],behavior=modeled)
                if row['compile_status']!='PASS':row['error']='compiler failed; see per-symbol stderr'
            except Exception as error:
                row['error']=type(error).__name__+': '+str(error)
                if row['compile_status']=='ERROR':row['exact_status']='ERROR'
            (directory/'diagnostic.log').write_text(log.getvalue(),encoding='utf-8')
            (directory/'status.json').write_text(json.dumps(row,indent=2)+'\n')
            rows.append(row)
            print(f"{entry['symbol']}: compile={row['compile_status']} semantics={row['semantic_status']} exact={row['exact_status']}")
        try:objects=object_pilot(manifest,out)
        except Exception as error:objects={'cli_status':'ERROR','error':type(error).__name__+': '+str(error)}
        tests=regression_tests(out)
    finally:
        verify_hashes(protected)
    summary=summarize(rows)
    report={'schema':'brainage-source-batch-result/1','classification':'BATCH_CHECKS_COMPLETED_NOT_AUTHENTIC_MATCH',
        'summary':summary,'symbols':rows,'object_comparison':objects,'regressions':tests,
        'protected_inputs_unchanged':True,'protected_input_sha256':protected,'protected_input_count':len(protected),
        'compiler':manifest['compiler'],'shared_header_sha256_lf':sha((ROOT/manifest['shared_header']).read_text().replace('\r\n','\n').encode()),
        'cluster_source':manifest['cluster_source'],'original_compiler_and_compilation_units_qualified':False}
    if summary['errors'] or not tests['pass'] or objects.get('cli_status')=='ERROR':report['classification']='BATCH_ERROR'
    (out/'batch_status.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if publish_status:
        published=dict(report)
        published['protected_input_sha256']={str(Path(path).relative_to(ROOT) if Path(path).is_relative_to(ROOT) else Path('..')/Path(path).name):digest for path,digest in protected.items()}
        destination=ROOT/'docs/matching_phase1/batch_status.json';destination.parent.mkdir(exist_ok=True)
        destination.write_text(json.dumps(published,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary));print('objects='+objects['cli_status']+'; regressions='+str(tests['run'])+'; inputs unchanged=12')
    if report['classification']=='BATCH_ERROR':return 2
    return 1 if require_exact and summary['exact_matches']!=len(rows) else 0


def cli(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--require-exact',action='store_true');parser.add_argument('--publish-status',action='store_true')
    args=parser.parse_args(argv)
    try:return run(args.output,args.require_exact,args.publish_status)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        failed={'schema':'brainage-source-batch-result/1','classification':'BATCH_ERROR','error':type(error).__name__+': '+str(error),
                'symbols':[],'genuine_original_matches':0,'gate0':'OPEN','protected_inputs_unchanged':'NOT_ESTABLISHED'}
        out=(args.output or ROOT/'local/matching_phase1/runs/utility-batch').resolve()
        if out.is_relative_to((ROOT/'local/matching_phase1/runs').resolve()):
            out.mkdir(parents=True,exist_ok=True)
            (out/'batch_status.json').write_text(json.dumps(failed,indent=2)+'\n')
            if args.publish_status:
                destination=ROOT/'docs/matching_phase1/batch_status.json';destination.parent.mkdir(exist_ok=True)
                destination.write_text(json.dumps(failed,indent=2)+'\n')
        print('BATCH_ERROR: '+str(error),file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(cli())
