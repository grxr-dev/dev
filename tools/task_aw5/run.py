"""One capture-only replay. Never enables AX or uses ordinary halt as terminal."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines(keepends=True) if line.endswith('\n')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runner', type=Path, required=True)
    parser.add_argument('--preflight', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    executable = args.runner.resolve()
    assert output.is_relative_to(ROOT / 'local/task-aw5') and not output.exists()
    assert json.loads(args.preflight.read_text())['safe']
    build = json.loads((executable.parent / 'build.json').read_text())
    assert build['safe'] and digest(executable.read_bytes()) == build['runner_sha256']
    for row in json.loads((executable.parent / 'compile.json').read_text()):
        assert digest(Path(row['source']).read_bytes()) == row['source_sha256']
    installation = json.loads((ROOT / 'local/task-aw5/installation.json').read_text())
    for name, expected in installation['sources'].items():
        assert digest((ROOT / 'local/ndsrecomp/runner/src' / name).read_bytes()) == expected
    source = ROOT / 'local/task-g/session-001/11-answer-01-63'
    state = (source / 'checkpoint.state').read_bytes()
    save = (source / 'after.sav').read_bytes()
    definition = json.loads((ROOT / 'tools/task_y/input.json').read_text())
    freeze = json.loads((ROOT / 'tools/task_y/freeze.json').read_text())
    assert digest(json.dumps(definition, sort_keys=True, separators=(',', ':')).encode()) == freeze['sha256']
    assert digest(state) == freeze['checkpoint_sha256']
    assert digest(save) == 'a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
    command = json.loads((ROOT / 'local/task-n/normal-enabled-002/session.json').read_text())['command']
    command[0] = str(executable)
    command[1] = str(output)
    command[command.index('--serve')] = '--interactive'
    command[command.index('--port') + 1] = '20255'
    command[command.index('--save-path') + 1] = str(output / 'session.sav')
    assert '--force-tier3' not in command
    rom = Path(command[command.index('--rom') + 1])
    assert hashlib.sha1(rom.read_bytes()).hexdigest() == 'b8a105bacc3234dede8d4465df0869f2b922a0e2'
    output.mkdir(parents=True)
    attempt = ROOT / 'local/task-aw5/live-attempt.lock'
    with attempt.open('x') as lock:
        lock.write(str(output) + '\n')
    (output / 'source.state').write_bytes(state)
    for name in ['initial.sav', 'session.sav']:
        (output / name).write_bytes(save)
    for name in ['requests.jsonl', 'flash.jsonl', 'frontend-input.jsonl']:
        (output / name).touch()
    token = uuid.uuid4().hex
    sequence = 0
    environment = {key: value for key, value in os.environ.items() if not key.startswith(('NDS_TASK_', 'NDS_BRAINAGE_', 'NDS_FRONTEND_', 'NDS_FLASH_'))}
    environment.update(NDS_TASK_AU_OUT=str(output), NDS_TASK_AU_PUBLICATION='1',
                       NDS_TASK_AW3_CAPTURE_ONLY='1', NDS_TASK_AW5_CAPTURE_ONLY='1',
                       NDS_TASK_AW3_AUDIT=str(output / 'capture.jsonl'),
                       NDS_TASK_O_START_STATE=str(output / 'source.state'),
                       NDS_TASK_F_RTC_PLUS_ONE_DAY='1', NDS_SDL_RENDER_DRIVER='software',
                       NDS_TASK_O_WINDOW_CONTROL=str(output / 'window-control.txt'),
                       NDS_TASK_O_CONTROL_TOKEN=token, NDS_TASK_O_FRONTEND_TRACE=str(output / 'frontend-input.jsonl'),
                       NDS_TASK_C_TRACE=str(output / 'requests.jsonl'), NDS_FLASH_TRACE=str(output / 'flash.jsonl'))
    evidence = {'command': command, 'runner_sha256': build['runner_sha256'], 'input_sha256': freeze['sha256'],
                'checkpoint_sha256': digest(state), 'source_save_sha256': digest(save), 'events': [],
                'backend': 'existing AU guarded replay, forced Tier-3 after restore', 'AX_enabled': False}
    (output / 'session.json').write_text(json.dumps(evidence, indent=2) + '\n')
    with (output / 'stdout.log').open('wb') as stdout, (output / 'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
    evidence['pid'] = process.pid

    def safety():
        assert not (output / 'requests.jsonl').stat().st_size and not (output / 'flash.jsonl').stat().st_size, 'STOP save activity'
        captured = rows(output / 'capture.jsonl')
        failed = next((row for row in captured if row['event'] == 'failure'), None)
        assert failed is None, failed
        assert process.poll() in (None, 73), 'capture process failed: ' + str(process.poll())
        return captured

    def wait(predicate, seconds=90):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            safety()
            value = predicate()
            if value:
                return value
            time.sleep(.05)
        raise TimeoutError('bounded capture observation timeout; no retry authorized')

    try:
        wait(lambda: any(row['event'] == 'panel_active' for row in rows(output / 'audit.jsonl')))
        time.sleep(2)
        for stroke_index, stroke in enumerate(definition['strokes'], 1):
            for kind, point in [(1, stroke[0]), *[(2, point) for point in stroke[1:]], (0, stroke[-1])]:
                safety()
                sequence += 1
                client = [point[0] * 2, (192 + point[1]) * 2]
                temporary = output / 'window-control.next'
                temporary.write_text(f'{token} {sequence} {kind} {client[0]} {client[1]}\n')
                temporary.replace(output / 'window-control.txt')
                wait(lambda: any(row.get('control_sequence') == sequence for row in rows(output / 'frontend-input.jsonl')))
                evidence['events'].append({'sequence': sequence, 'kind': kind, 'stroke': stroke_index, 'ds': point, 'client': client})
                time.sleep(.12)
            wait(lambda: sum(row['event'] == 'recognition' for row in rows(output / 'audit.jsonl')) == stroke_index)
        wait(lambda: any(row['event'] == 'aw5_capture_terminal' for row in rows(output / 'capture.jsonl')))
        evidence['exit_code'] = process.wait(timeout=10)
        assert evidence['exit_code'] == 73
        evidence['admitted'] = True
    except Exception as error:
        evidence['admitted'] = False
        evidence['failure'] = str(error)
        if process.poll() is None:
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                evidence['emergency_process_termination'] = True
                process.terminate()
                process.wait(timeout=10)
    finally:
        evidence['exit_code'] = process.poll()
        evidence['capture'] = rows(output / 'capture.jsonl')
        evidence['source_checkpoint_unchanged'] = (source / 'checkpoint.state').read_bytes() == state
        evidence['source_save_unchanged'] = (source / 'after.sav').read_bytes() == save
        evidence['disposable_save_sha256'] = digest((output / 'session.sav').read_bytes())
        evidence['save_files_unchanged'] = (output / 'session.sav').read_bytes() == save
        evidence['logical_request_trace_bytes'] = (output / 'requests.jsonl').stat().st_size
        evidence['flash_trace_bytes'] = (output / 'flash.jsonl').stat().st_size
        evidence['ordinary_final_save_written'] = (output / 'final.sav').exists()
        evidence['preserved_runners_unchanged'] = all(digest((ROOT / name).read_bytes()) == expected for name, expected in build['preserved_runners'].items())
        (output / 'session.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({key: evidence.get(key) for key in ['admitted', 'failure', 'exit_code', 'save_files_unchanged', 'emergency_process_termination']}, indent=2))
    if not evidence['admitted']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
