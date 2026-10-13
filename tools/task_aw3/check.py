"""AW3 focused ROM-free tests; never launches a runner or loads Brain Age images."""
import hashlib
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'local/task-aw3/certification-005'


def main():
    global OUT
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=str(OUT))
    args=parser.parse_args()
    OUT=Path(args.output).resolve()
    assert OUT.is_relative_to((ROOT/'local/task-aw3').resolve()), 'Local evidence root required.'
    assert not OUT.exists(), 'Preserve evidence; choose a new certification directory.'
    OUT.mkdir(parents=True)
    tool=ROOT/'local/toolchain/w64devkit/bin'
    env=dict(os.environ)
    env['PATH']=str(tool)+os.pathsep+env['PATH']
    logs=[]

    def run(command,expected=0):
        child=subprocess.run([str(value) for value in command],cwd=ROOT,env=env,capture_output=True,
                             text=True,encoding='utf-8',errors='replace')
        logs.append({'command':[str(value) for value in command],'exit':child.returncode,
                     'stdout':child.stdout,'stderr':child.stderr})
        (OUT/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
        assert child.returncode==expected, child.stdout+child.stderr
        return child.stdout.strip()

    run(['python',HERE/'install.py'])
    model=OUT/'model.exe'
    run([tool/'g++.exe','-std=c++20','-O2','-Wall','-Wextra','-Werror',
         '-I'+str(ROOT/'local/ndsrecomp/runner/src'),'-I'+str(ROOT/'local/ndsrecomp/recompiler/support'),
         HERE/'test.cpp',ROOT/'build/task-o-sdl-runner/libnds_support.a','-o',model])
    unit_dir=OUT/'unit';unit_dir.mkdir()
    unit=run([model,'unit',unit_dir])
    build=OUT/'native-build'
    run([tool/'cmake.exe','-S',HERE,'-B',build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release'])
    run([tool/'cmake.exe','--build',build,'-j','4'])
    native=run([build/'aw3_runtime_test.exe',OUT/'native-audit.jsonl'])
    children=[]
    cases=[('terminal',73),('stale',79),('manifest',79),('hidden',79),('readiness',79),
           ('guard',79),('bad-au',79),('rom',79),('overflow',79),('thread',79),('missing',79),('bound-cap',79),('bound-import',79),('disabled',99)]
    for mode,code in cases:
        directory=OUT/mode;directory.mkdir()
        run([model,mode,directory],code)
        rows=[json.loads(line) for line in (directory/'audit.jsonl').read_text().splitlines()]
        if mode=='disabled':
            assert (directory/'old-halt').exists() and (directory/'legacy-file-output').exists()
        else:
            assert rows and rows[-1]['event']==('capture_only_terminal' if mode=='terminal' else 'failure')
            assert not (directory/'old-halt').exists() and not (directory/'legacy-file-output').exists()
        for name in ['post-boundary-instruction','device-tail','IRQ-tail','ARM7-tail','destructor','persistence-shutdown']:
            assert not (directory/name).exists(), name
        for row in rows:
            if row['event']=='canonical_snapshot':
                assert hashlib.sha256(bytes.fromhex(row['canonical_hex'])).hexdigest()==row['sha256']
        children.append({'mode':mode,'exit':code,'audit_events':[row['event'] for row in rows],
                         'old_halt_reached':mode=='disabled','post_terminal_sentinels_reached':False})
    run([tool/'ninja.exe','-C',ROOT/'build/task-o-sdl-runner',
         *[f'CMakeFiles/nds_runner.dir/src/{name}.cpp.obj' for name in ['runtime_arm','scheduler','bus','io','cp15','tier3']],'-j','4'])
    result={'task':'AW3','classification':'PARTIAL','brainage_guest_execution':False,'runtime_MMIO':False,
            'AX_executed':False,'optional_live_capture':False,
            'assertions':int(re.search(r'assertions: (\d+)',unit)[1]),'actual_runtime_checks':10,
            'children':children,'six_actual_objects_compile':True,
            'exact_remaining_transcript_contradiction':'Runtime journal grows on every reschedule and snapshot ordinal advances; AW2 expected states freeze those fields. Dropping them is forbidden.',
            'sources':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in HERE.iterdir() if path.is_file()}}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
