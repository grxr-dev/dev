"""Build one isolated diagnostic overlay. Never edits production source or launches a runner."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'local/ndsrecomp/runner/src'
ATTEMPT = ROOT / 'local/task-aw9/attempt-001'
OUTPUT = ROOT / 'build/task-aw9-once'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert json.loads((ATTEMPT / 'preflight.json').read_text())['artifact_preflight_passed']
    assert (ATTEMPT.parent / 'one-shot.lock').read_text().strip()==str(ATTEMPT)
    assert not OUTPUT.exists() and not (ATTEMPT / 'launch.claim').exists()
    OUTPUT.mkdir()
    overlay=OUTPUT / 'source'; overlay.mkdir()
    preserved=json.loads((ROOT / 'local/task-aw8/certification-008/tests.json').read_text())['preserved_artifacts']
    assert all(sha(ROOT / name)==digest for name,digest in preserved.items())
    originals={}
    for path in SOURCE.rglob('*'):
        if path.is_file() and path.suffix in ['.cpp','.h','.hpp','.inc','.inl','.tpp']:
            name=path.relative_to(SOURCE)
            destination=overlay / name; destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,destination); originals[str(name)]=sha(path)
    changed={}
    path=overlay / 'aw7/integration.h'
    original=path.read_text(encoding='utf-8-sig')
    updated=original.replace('inline bool armed=false,owned=false;','inline bool armed=false,owned=false;\ninline bool runtime_authorized=false;')
    anchor='        if constexpr (!Model) fail("runtime bus interlock remains closed pending actual-provider certification");'
    assert updated.count(anchor)==1
    updated=updated.replace(anchor,'        if constexpr (!Model) require(runtime_authorized,"AW9 runtime permission absent");')
    path.write_text(updated,encoding='utf-8'); changed['aw7/integration.h']=sha(path)
    permission=(ROOT / 'tools/task_aw9/permission.h').read_bytes()
    (overlay / 'aw9_permission.h').write_bytes(permission); changed['aw9_permission.h']=sha(overlay / 'aw9_permission.h')
    path=overlay / 'brainage_task_au.h'
    path.write_text('#include "aw9_permission.h"\n'+path.read_text(encoding='utf-8-sig'),encoding='utf-8')
    changed['brainage_task_au.h']=sha(path)
    path=overlay / 'task_au_setup.inc'
    original=path.read_text(encoding='utf-8-sig')
    anchor='        if (task_aw7::waiting())'
    assert original.count(anchor)==1
    addition='        if (task_aw9::selected()) { task_aw9::handoff(); return 0; }\n'
    updated=original.replace(anchor,addition+anchor)
    assert updated.replace(addition,'')==original
    assert updated.index('AU forbidden STRH not dispatched')<updated.index(addition)<updated.index('if (task_aw3::armed)')
    path.write_text(updated,encoding='utf-8'); changed['task_au_setup.inc']=sha(path)
    for name,digest in originals.items():
        if name.replace('\\','/') not in changed:
            assert sha(overlay / name)==digest
    for name in ['bus.inc','io.inc','runtime.inc','scheduler.inc','cp15.inc']:
        assert sha(overlay / 'aw3' / name)==sha(SOURCE / 'aw3' / name)
    assert not (overlay / 'aw8').exists()
    prior=ROOT / 'build/task-o-sdl-runner'
    tool=ROOT / 'local/toolchain/w64devkit/bin'
    environment={key:value for key,value in os.environ.items() if not key.startswith('NDS_')}
    environment['PATH']=str(tool)+os.pathsep+environment['PATH']
    database=json.loads(subprocess.check_output([str(tool/'ninja.exe'),'-C',str(prior),'-t','compdb'],env=environment))
    link=subprocess.check_output([str(tool/'ninja.exe'),'-C',str(prior),'-t','commands','nds_runner'],env=environment,text=True).splitlines()[-1]
    imported={}
    for name in re.findall(r'(?<!\S)([^\s"]+\.(?:obj|a))(?=\s|$)',link):
        if Path(name).is_absolute() or name.startswith('-'): continue
        source=prior/name; destination=OUTPUT/name
        assert source.resolve().is_relative_to(prior.resolve()) and source.is_file()
        destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,destination)
        imported[name]=sha(source)
    rows=[row for row in database if row['output'].startswith('CMakeFiles/nds_runner.dir/src/') and SOURCE.resolve() in Path(row['file']).resolve().parents]
    assert len(rows)>=40
    logs=[]

    def compile_one(row):
        destination=OUTPUT/row['output']; destination.parent.mkdir(parents=True,exist_ok=True)
        command=row['command'].replace(row['output'],destination.as_posix())
        command=command.replace(row['output'].replace('/','\\')+'.d',destination.as_posix()+'.d')
        command=command.replace(SOURCE.as_posix(),overlay.as_posix())
        command += ' -I'+SOURCE.as_posix()+' -DAW7_DIAGNOSTIC_HARNESS=1 -DAW9_LIVE_ONCE=1'
        source=overlay/Path(row['file']).relative_to(SOURCE)
        child=subprocess.run(command,cwd=prior,env=environment,capture_output=True,text=True,errors='replace',timeout=600)
        return {'source':str(source),'source_sha256':sha(source),'command':command,'exit':child.returncode,'stdout':child.stdout,'stderr':child.stderr}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for log in pool.map(compile_one,rows):
            logs.append(log); (OUTPUT/'compile.json').write_text(json.dumps(logs,indent=2)+'\n')
            assert log['exit']==0,log['source']+'\n'+log['stderr']
            print('compiled',Path(log['source']).name,flush=True)
    child=subprocess.run(link,cwd=OUTPUT,env=environment,capture_output=True,text=True,errors='replace',timeout=600)
    (OUTPUT/'link.json').write_text(json.dumps({'command':link,'exit':child.returncode,'stdout':child.stdout,'stderr':child.stderr},indent=2)+'\n')
    assert child.returncode==0,child.stdout+child.stderr
    shutil.copy2(prior/'SDL3.dll',OUTPUT/'SDL3.dll')
    assert all(sha(ROOT/name)==digest for name,digest in preserved.items())
    assert all(sha(prior/name)==digest for name,digest in imported.items())
    result={'safe':True,'native_sources_recompiled':len(rows),'original_source_hashes':originals,'overlay_changes':changed,
            'imported_existing_objects_archives':imported,'preserved_artifacts':preserved,'runner_sha256':sha(OUTPUT/'nds_runner.exe'),
            'runtime_dll_sha256':sha(OUTPUT/'SDL3.dll'),'fixture_adapters_present':False,'runner_launched':False,
            'generated_C_edited_or_regenerated':False}
    (OUTPUT/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'safe':True,'runner_sha256':result['runner_sha256'],'runner_launched':False},indent=2))


if __name__=='__main__':
    main()
