"""ROM-free unit/child-process tests. Never launches a runner or opens a ROM."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'local/task-aw'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    executable = OUT / 'synthetic.exe'
    compiler = ROOT / 'local/toolchain/w64devkit/bin/g++.exe'
    subprocess.run([str(compiler), '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                    str(HERE/'test.cpp'), '-o', str(executable)], check=True)
    unit = subprocess.check_output([str(executable)], text=True).strip()
    children = []
    for name, expected in [('terminal', 73), ('failure', 79)]:
        directory = OUT / name
        directory.mkdir(exist_ok=True)
        assert not any((directory/path).exists() for path in
                       ['scheduler-tail','device-service','arm7-catchup','shutdown-save','destructor'])
        child = subprocess.run([str(executable), name, str(directory)])
        assert child.returncode == expected, child.returncode
        audit = (directory/'terminal.jsonl').read_text()
        rows = [json.loads(line) for line in audit.splitlines()]
        if name == 'terminal':
            assert rows[0]['event'] == 'snapshot' and rows[0]['entries'] == 6
            assert rows[0]['values']['cycle9'] == 3416875721
            assert rows[0]['bytes_hex']['cpu'] == '01020304'
        for sentinel in ['scheduler-tail','device-service','arm7-catchup','shutdown-save','destructor']:
            assert not (directory/sentinel).exists(), sentinel
        children.append({'test': name, 'exit_code': child.returncode,
                         'audit_events': [row['event'] for row in rows],
                         'tail_sentinels_reached': False})
    result = {'guest_execution': False, 'runtime_mmio': False, 'unit': unit,
              'children': children, 'compiler': str(compiler),
              'source_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in HERE.iterdir() if path.is_file()}}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
