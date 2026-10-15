"""Single-attempt AW9 artifact preflight. No runner launch or guest execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = 'c0ac62cae632715157fcb3db52b982cc86104baa'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = ROOT / 'local/task-aw9'
    root.mkdir(exist_ok=True)
    attempt = root / 'attempt-001'
    with (root / 'one-shot.lock').open('x') as lock:
        lock.write(str(attempt) + '\n')
    attempt.mkdir()
    result = {'task': 'AW9', 'authority': AUTHORITY, 'artifact_preflight_passed': False,
              'runner_launches': 0, 'bounded_prefix_executed': False, 'retry_authorized': False}
    try:
        def exact(name, actual, expected):
            if actual != expected:
                raise RuntimeError(f'{name}: expected {expected!r}, observed {actual!r}')

        exact('checkout', subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), AUTHORITY)
        exact('branch', subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(), 'codex/brainage')
        frozen = json.loads((ROOT / 'tools/task_aw8/certificate.json').read_text())
        payload = hashlib.sha256(json.dumps(frozen['certificate'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        exact('AW8 certificate payload', payload, frozen['sha256'])
        exact('AW8 authoritative certificate', payload, '8381e1335266a05767982f292eb5237eb157bb5d8d9ea431c1a81d7552bae417')
        exact('AW8 mechanical readiness', frozen['certificate']['dynamic_execution_ready'], True)
        evidence = ROOT / frozen['certificate']['local_evidence']
        exact('AW8 tests identity', sha(evidence / 'tests.json'), frozen['certificate']['tests_sha256'])
        exact('AW8 success audit identity', sha(evidence / 'success/audit.jsonl'), frozen['certificate']['success_audit_sha256'])
        tests = json.loads((evidence / 'tests.json').read_text())
        for group in ['fixture_sources_sha256', 'preserved_artifacts']:
            for name, digest in tests[group].items():
                exact(name, sha(ROOT / name), digest)
        for name, digest in tests['generated_sources_sha256'].items():
            exact(name, sha(evidence / name), digest)
        exact('AW8 fixture executable', sha(evidence / 'build/aw8_provider_test.exe'), tests['fixture_executable_sha256'])
        output = ROOT / 'local/task-aw8/aw9-preflight-once.json'
        command = [sys.executable, str(ROOT / 'tools/task_aw8/certify.py'), '--evidence', str(evidence), '--out', str(output)]
        child = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        (attempt / 'aw8-preflight-command.json').write_text(json.dumps({'command': command, 'exit': child.returncode,
            'stdout': child.stdout, 'stderr': child.stderr}, indent=2) + '\n')
        exact('unchanged AW8 certification preflight exit', child.returncode, 0)
        repeated = json.loads(output.read_text())
        exact('repeated AW8 certificate', repeated, frozen)
        freeze = json.loads((ROOT / 'tools/task_y/freeze.json').read_text())
        source = ROOT / 'local/task-g/session-001/11-answer-01-63'
        exact('immutable source checkpoint', sha(source / 'checkpoint.state'), freeze['checkpoint_sha256'])
        exact('immutable source save', sha(source / 'after.sav'), frozen['certificate']['unchanged_identities']['save'])
        definition = json.loads((ROOT / 'tools/task_y/input.json').read_text())
        exact('frozen AU input', hashlib.sha256(json.dumps(definition, sort_keys=True, separators=(',', ':')).encode()).hexdigest(), freeze['sha256'])
        original = json.loads((ROOT / 'local/task-n/normal-enabled-002/session.json').read_text())['command']
        rom = Path(original[original.index('--rom') + 1])
        exact('actual ROM SHA1', hashlib.sha1(rom.read_bytes()).hexdigest(), frozen['certificate']['unchanged_identities']['rom'])
        result.update(artifact_preflight_passed=True, certificate_payload_sha256=payload,
                      checkpoint_sha256=freeze['checkpoint_sha256'], input_sha256=freeze['sha256'],
                      live_entry_preflight_still_required=True)
    except Exception as error:
        result['first_mismatch'] = str(error)
    (attempt / 'preflight.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if not result['artifact_preflight_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
