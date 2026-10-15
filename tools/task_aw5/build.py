"""Relink an isolated SDL capture runner, reusing immutable compiled ROM banks."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prior = ROOT / 'build/task-o-sdl-runner'
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'build/task-aw5-capture')
    output = parser.parse_args().out.resolve()
    assert output.is_relative_to(ROOT / 'build')
    assert not output.exists()
    output.mkdir()
    tool = ROOT / 'local/toolchain/w64devkit/bin'
    environment = dict(os.environ)
    environment['PATH'] = str(tool) + os.pathsep + environment['PATH']
    preserved = [prior / 'nds_runner.exe', ROOT / 'build/task-u-runner/nds_runner.exe']
    before = {str(path.relative_to(ROOT)): digest(path) for path in preserved}
    database = json.loads(subprocess.check_output([str(tool / 'ninja.exe'), '-C', str(prior), '-t', 'compdb'], env=environment))
    link = subprocess.check_output([str(tool / 'ninja.exe'), '-C', str(prior), '-t', 'commands', 'nds_runner'], env=environment, text=True).splitlines()[-1]
    relative_inputs = re.findall(r'(?<!\S)([^\s"]+\.(?:obj|a))(?=\s|$)', link)
    imported = {}
    for name in relative_inputs:
        source = prior / name
        if Path(name).is_absolute() or name.startswith('-'):
            continue
        assert source.resolve().is_relative_to(prior.resolve()) and source.is_file(), name
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        imported[name] = digest(source)
    rows = [row for row in database if row['output'].startswith('CMakeFiles/nds_runner.dir/src/')
            and (ROOT / 'local/ndsrecomp/runner/src').resolve() in Path(row['file']).resolve().parents]
    assert len(rows) >= 40
    logs = []

    def compile_one(row):
        destination = output / row['output']
        destination.parent.mkdir(parents=True, exist_ok=True)
        command = row['command'].replace(row['output'], destination.as_posix())
        command = command.replace(row['output'].replace('/', '\\') + '.d', destination.as_posix() + '.d')
        child = subprocess.run(command, cwd=prior, env=environment, capture_output=True, text=True, errors='replace', timeout=600)
        return {'source': row['file'], 'source_sha256': digest(Path(row['file'])), 'command': command,
                'exit': child.returncode, 'stdout': child.stdout, 'stderr': child.stderr}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for log in pool.map(compile_one, rows):
            logs.append(log)
            (output / 'compile.json').write_text(json.dumps(logs, indent=2) + '\n')
            assert log['exit'] == 0, log['source'] + '\n' + log['stderr']
            print('compiled', Path(log['source']).name, flush=True)
    child = subprocess.run(link, cwd=output, env=environment, capture_output=True, text=True, errors='replace', timeout=600)
    (output / 'link.json').write_text(json.dumps({'command': link, 'exit': child.returncode, 'stdout': child.stdout, 'stderr': child.stderr}, indent=2) + '\n')
    assert child.returncode == 0, child.stdout + child.stderr
    shutil.copy2(prior / 'SDL3.dll', output / 'SDL3.dll')
    assert before == {str(path.relative_to(ROOT)): digest(path) for path in preserved}
    for name, expected in imported.items():
        assert digest(prior / name) == expected
    result = {'safe': True, 'native_sources_recompiled': len(rows), 'generated_C_regenerated_or_edited': False,
              'imported_existing_objects_archives': imported, 'preserved_runners': before,
              'runner_sha256': digest(output / 'nds_runner.exe'), 'runtime_dll_sha256': digest(output / 'SDL3.dll')}
    (output / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['safe', 'native_sources_recompiled', 'runner_sha256']}, indent=2))


if __name__ == '__main__':
    main()
