"""Fixed AW14 paths and artifact checks. Importing this module executes no guest."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / 'local/task-aw14/attempt-001'
BUILD = ROOT / 'build/task-aw14-once'
SOURCE = ROOT / 'local/ndsrecomp/runner/src'
AUTHORITY = '1d64040633738bc63b5f49d2718d5c30dbad801c'
ENTRY = '0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c'
TERMINAL = 'ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526'


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as output:
        json.dump(value, output, indent=2)
        output.write('\n')


def rows(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines(keepends=True) if line.endswith('\n')]


def preserved(expected):
    for name, identity in expected.items():
        require(sha(ROOT / name) == identity, 'protected artifact changed: ' + name)
