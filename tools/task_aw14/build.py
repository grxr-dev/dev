"""One private native-source build. No launcher, generator or old-permit reuse."""
import concurrent.futures
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from common import ROOT, SOURCE, ATTEMPT, BUILD, load, module, preserved, require, sha, write_new


def main():
    preflight=load(ATTEMPT/'preflight.json')
    require(preflight['artifact_preflight_passed'] and not (ATTEMPT/'launch.claim').exists(),'preflight/launch guard')
    require((ATTEMPT.parent/'one-shot.lock').read_text().strip()==str(ATTEMPT),'reservation mismatch')
    preserved(preflight['protected_artifacts'])
    require(not BUILD.exists(),'build already exists; no replacement')
    BUILD.mkdir()
    overlay=BUILD/'source'; overlay.mkdir()
    originals={}
    for path in SOURCE.rglob('*'):
        if path.is_file() and path.suffix in ['.cpp','.h','.hpp','.inc','.inl','.tpp']:
            relative=path.relative_to(SOURCE)
            target=overlay/relative; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target); originals[str(relative)]=sha(path)
    hooks=module('aw14_aw12_hooks',ROOT/'tools/task_aw12/hooks.py')
    names=['tier3.cpp','runtime_arm.cpp','scheduler.cpp','gpu3d.cpp','aw7/integration.h','brainage_task_au.h']
    before={name:(overlay/name).read_text(encoding='utf-8-sig') for name in names}
    patched=hooks.patch_sources(before)
    for name,text in patched.items():
        (overlay/name).write_text(text,encoding='utf-8')
    (overlay/'aw12').mkdir()
    for name in ['controller.h','gpu.h']:
        shutil.copy2(ROOT/'tools/task_aw12'/name,overlay/'aw12'/name)
    path=overlay/'aw7/integration.h'
    text=path.read_text(encoding='utf-8')
    text=hooks.once(text,'inline bool armed=false,owned=false;','inline bool armed=false,owned=false;\ninline bool runtime_authorized=false;')
    text=hooks.once(text,'        if constexpr (!Model) fail("runtime bus interlock remains closed pending actual-provider certification");',
                    '        if constexpr (!Model) require(runtime_authorized,"AW14 runtime permission absent");')
    path.write_text(text,encoding='utf-8')
    shutil.copy2(ROOT/'tools/task_aw14/permission.h',overlay/'aw14_permission.h')
    (overlay/'aw14_contract.h').write_text('#pragma once\nnamespace task_aw14 { inline constexpr const char* contract_identity="'+preflight['contract_sha256']+'"; }\n',encoding='utf-8')
    path=overlay/'brainage_task_au.h'
    path.write_text('#include "aw14_permission.h"\n'+path.read_text(encoding='utf-8'),encoding='utf-8')
    path=overlay/'task_au_setup.inc'
    original=path.read_text(encoding='utf-8-sig')
    addition='        if (task_aw14::selected()) { task_aw14::handoff(); return 0; }\n'
    updated=hooks.once(original,'        if (task_aw7::waiting())',addition+'        if (task_aw7::waiting())')
    require(updated.replace(addition,'')==original,'AU guard source changed')
    require(updated.index('AU forbidden STRH not dispatched')<updated.index(addition)<updated.index('if (task_aw3::armed)'),'AU guards no longer dominate handoff')
    path.write_text(updated,encoding='utf-8')
    path=overlay/'scheduler.cpp'
    text=path.read_text(encoding='utf-8')
    text='#include "aw14_permission.h"\n'+text
    text=hooks.once(text,'void scheduler_run_round() {','void scheduler_run_round() {\n    task_aw14::prepare();')
    path.write_text(text,encoding='utf-8')
    for name in ['bus.inc','io.inc','runtime.inc','scheduler.inc','cp15.inc']:
        require(sha(overlay/'aw3'/name)==sha(SOURCE/'aw3'/name),'actual provider changed')
    require(not (overlay/'aw8').exists(),'fixture adapters forbidden')
    for name in ['controller.h','gpu.h']:
        require(sha(overlay/'aw12'/name)==load(ROOT/'tools/task_aw12/certificate.json')['implementation_sha256'][name],'AW12 runtime source mismatch')
    changed={str(path.relative_to(overlay)):sha(path) for path in overlay.rglob('*') if path.is_file() and
             (str(path.relative_to(overlay)) not in originals or sha(path)!=originals[str(path.relative_to(overlay))])}
    allowed=set(names+['task_au_setup.inc','aw14_permission.h','aw14_contract.h','aw12/controller.h','aw12/gpu.h'])
    require(all(name.replace('\\','/') in allowed for name in changed),'unexpected overlay edit')
    prior=ROOT/'build/task-o-sdl-runner'
    tool=ROOT/'local/toolchain/w64devkit/bin'
    environment={key:value for key,value in os.environ.items() if not key.startswith('NDS_')}
    environment['PATH']=str(tool)+os.pathsep+environment['PATH']
    database=json.loads(subprocess.check_output([str(tool/'ninja.exe'),'-C',str(prior),'-t','compdb'],env=environment))
    link=subprocess.check_output([str(tool/'ninja.exe'),'-C',str(prior),'-t','commands','nds_runner'],env=environment,text=True).splitlines()[-1]
    imported={}
    for name in re.findall(r'(?<!\S)([^\s"]+\.(?:obj|a))(?=\s|$)',link):
        if Path(name).is_absolute() or name.startswith('-'):
            continue
        source=prior/name; target=BUILD/name
        require(source.resolve().is_relative_to(prior.resolve()) and source.is_file(),'invalid existing object path')
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target); imported[name]=sha(source)
    native=[row for row in database if row['output'].startswith('CMakeFiles/nds_runner.dir/src/') and SOURCE.resolve() in Path(row['file']).resolve().parents]
    require(len(native)>=40,'native build inventory mismatch')
    logs=[]
    def compile_one(row):
        target=BUILD/row['output']; target.parent.mkdir(parents=True,exist_ok=True)
        command=row['command'].replace(row['output'],target.as_posix()).replace(row['output'].replace('/','\\')+'.d',target.as_posix()+'.d')
        command=command.replace(SOURCE.as_posix(),overlay.as_posix())
        command+=' -I'+SOURCE.as_posix()+' -DAW7_DIAGNOSTIC_HARNESS=1 -DAW14_LIVE_ONCE=1 -DAW12_DIAGNOSTIC_CAPTURE_ONLY=1'
        source=overlay/Path(row['file']).relative_to(SOURCE)
        child=subprocess.run(command,cwd=prior,env=environment,capture_output=True,text=True,errors='replace',timeout=600)
        return {'source':str(source),'source_sha256':sha(source),'command':command,'exit':child.returncode,'stdout':child.stdout,'stderr':child.stderr}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for log in pool.map(compile_one,native):
            logs.append(log); (BUILD/'compile.json').write_text(json.dumps(logs,indent=2)+'\n',encoding='utf-8')
            require(log['exit']==0,'native compilation failure: '+log['source'])
            print('compiled '+Path(log['source']).name,flush=True)
    child=subprocess.run(link,cwd=BUILD,env=environment,capture_output=True,text=True,errors='replace',timeout=600)
    write_new(BUILD/'link.json',{'command':link,'exit':child.returncode,'stdout':child.stdout,'stderr':child.stderr})
    require(child.returncode==0,'native link failure')
    shutil.copy2(prior/'SDL3.dll',BUILD/'SDL3.dll')
    preserved(preflight['protected_artifacts'])
    require(all(sha(prior/name)==identity for name,identity in imported.items()),'original objects changed')
    result={'safe':True,'native_sources_recompiled':len(native),'original_source_hashes':originals,'overlay_changes':changed,
            'imported_existing_objects_archives':imported,'protected_artifacts':preflight['protected_artifacts'],
            'runner_sha256':sha(BUILD/'nds_runner.exe'),'runtime_dll_sha256':sha(BUILD/'SDL3.dll'),
            'fixture_adapters_present':False,'generated_C_edited_or_regenerated':False,'runner_launched':False,
            'contract_sha256':preflight['contract_sha256'],
            'helper_sha256':{path.name:sha(path) for path in (ROOT/'tools/task_aw14').glob('*') if path.is_file()}}
    write_new(BUILD/'build.json',result)
    print(json.dumps({'safe':True,'runner_sha256':result['runner_sha256'],'runner_launched':False}))


if __name__=='__main__':
    main()
