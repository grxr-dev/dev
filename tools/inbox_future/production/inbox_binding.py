"""Single local recipient source of truth. Rebind never grants delivery authority."""
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid

BUILD = 'inbox-binding-20261101-01'
SCHEMA = 'middleman-inbox-binding/1'
LEGACY = '6acab580-d218-83ea-9598-0ff64dc33aa7'
UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
COMPONENTS=('inbox_binding.py','inbox_recovery.py','inbox-v1/native-host/jarvis_inbox_host.py',
 'inbox-v1/native-host/readiness_diagnostic.py','inbox-v1/extension/binding_contract.js',
 'inbox-v1/extension/background.js','inbox-v1/extension/chatgpt_content.js','inbox-v1/extension/manifest.json',
 'inbox_one.py','inbox_queue.py','inbox_api.py','inbox_local.py','inbox_wire.py','inbox-v1/extension/one_contract.js','inbox_future.py','inbox-v1/extension/future_contract.js','completions.py','relay_state.py')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def unique(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('duplicate binding key')
        result[name] = value
    return result


def target_id(value):
    if not isinstance(value, str):
        raise ValueError('exact conversation URL or lowercase UUID required')
    if value.startswith('https://chatgpt.com/c/'):
        value = value[len('https://chatgpt.com/c/'):]
    if not re.fullmatch(UUID, value):
        raise ValueError('exact https://chatgpt.com/c/UUID required; no query, fragment, alias or trailing path')
    return value


def path_for(runtime):
    return Path(runtime) / 'inbox_binding.json'


def validate(value):
    required = {'schema','build','conversation_id','generation','epoch','delivery_policy','updated_at','previous','protected_history','components','identity'}
    if not isinstance(value, dict) or set(value) != required or value['schema'] != SCHEMA or value['build'] != BUILD:
        raise ValueError('binding schema/build mismatch')
    target_id(value['conversation_id'])
    if type(value['generation']) is not int or not 1 <= value['generation'] <= 1000000:
        raise ValueError('invalid binding generation')
    if not re.fullmatch('[0-9a-f]{32}', value['epoch']) or value['delivery_policy'] != 'HOLD':
        raise ValueError('binding must be held')
    if not isinstance(value['previous'], list) or len(value['previous']) > 64 or type(value['updated_at']) not in (int, float):
        raise ValueError('invalid binding history')
    if not isinstance(value['protected_history'], dict) or any(not re.fullmatch('[0-9a-f]{64}', item) for item in value['protected_history'].values()):
        raise ValueError('invalid protected history hashes')
    if not isinstance(value['components'],dict) or set(value['components'])!=set(COMPONENTS) or any(not isinstance(item,str) or not re.fullmatch('[0-9a-f]{64}',item) for item in value['components'].values()):
        raise ValueError('incomplete component binding')
    if digest({key:item for key,item in value.items() if key != 'identity'}) != value['identity']:
        raise ValueError('binding identity mismatch')
    return value


def load(runtime):
    path = path_for(runtime)
    if path.stat().st_size > 65536:
        raise ValueError('binding size bound')
    value=validate(json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique))
    root=Path(__file__).resolve().parent
    if any(hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected for name,expected in value['components'].items()):
        raise ValueError('recipient components changed/incomplete; HOLD until coherent source restored')
    return value


def public(value):
    validate(value)
    return {key:value[key] for key in ('schema','build','conversation_id','generation','epoch','delivery_policy','identity')}


def atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as handle:
            handle.write(canonical(value));handle.flush();os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def change(runtime, target, expected_id, expected_identity, rollback=False):
    runtime = Path(runtime)
    target = target_id(target)
    expected_id = target_id(expected_id)
    path = path_for(runtime)
    if not (runtime/'inbox_readiness_request.json').is_file():
        raise ValueError('existing no-send hold required before rebind')
    hold=json.loads((runtime/'inbox_readiness_request.json').read_text())
    if not isinstance(hold,dict) or set(hold)!={'probe_id'} or not re.fullmatch('[0-9a-f]{32}',hold['probe_id']):
        raise ValueError('valid existing no-send hold required')
    pending = json.loads((runtime/'inbox_native_recovery.json').read_text(encoding='utf-8'))
    if pending is not None:
        raise ValueError('native outcome pending; no rebind or ACK allowed')
    current = load(runtime) if path.exists() else None
    if current and current['conversation_id'] == target:
        previous=current['previous'][-1] if current['previous'] else {}
        if current['identity']==expected_identity and current['conversation_id']==expected_id or previous.get('identity')==expected_identity and previous.get('conversation_id')==expected_id:
            return current, False
    if current:
        if current['conversation_id'] != expected_id or current['identity'] != expected_identity:
            raise ValueError('stale expected recipient/identity; inspect status again')
        if rollback and (not current['previous'] or current['previous'][-1]['conversation_id'] != target):
            raise ValueError('rollback must name immediately previous recorded recipient')
    elif expected_id != LEGACY or expected_identity != 'LEGACY_UNCONFIGURED' or rollback:
        raise ValueError('explicit legacy bootstrap identity required')
    protected = {}
    for name in ('inbox_queue.json','inbox_native_recovery.json','inbox_readiness_request.json'):
        protected[name] = hashlib.sha256((runtime/name).read_bytes()).hexdigest()
    history = list(current['previous']) if current else []
    if current:
        history.append(public(current))
    else:
        history.append({'conversation_id': LEGACY, 'identity': 'LEGACY_UNCONFIGURED'})
    value = {'schema': SCHEMA, 'build': BUILD, 'conversation_id': target, 'epoch': uuid.uuid4().hex,
             'generation': current['generation']+1 if current else 1, 'delivery_policy': 'HOLD',
             'updated_at': time.time(), 'previous': history, 'protected_history': protected,
             'components': {name:hashlib.sha256((Path(__file__).resolve().parent/name).read_bytes()).hexdigest() for name in COMPONENTS}}
    value['identity'] = digest(value)
    validate(value)
    backups = runtime / 'inbox-binding-history'
    backups.mkdir(exist_ok=True)
    backup = backups / ((current['identity'] if current else 'legacy') + '.json')
    if not backup.exists():
        with backup.open('x', encoding='utf-8') as handle:
            handle.write(canonical(current or {'conversation_id': LEGACY, 'protected_history': protected}));handle.flush();os.fsync(handle.fileno())
    if (load(runtime)['identity'] if path.exists() else 'LEGACY_UNCONFIGURED') != expected_identity:
        raise ValueError('binding changed during rebind')
    if any(hashlib.sha256((runtime/name).read_bytes()).hexdigest()!=expected for name,expected in protected.items()):
        raise ValueError('protected history changed during rebind')
    atomic(path, value)
    return value, True


def status(runtime):
    value = load(runtime)
    result_path = Path(runtime)/'inbox_binding_readiness.json'
    result = json.loads(result_path.read_text()) if result_path.exists() else None
    fresh = bool(result and result.get('binding_identity') == value['identity'] and
                 0 <= time.time()*1000-result.get('observed_ms',0) <= 60000)
    return {'binding': public(value), 'url': 'https://chatgpt.com/c/'+value['conversation_id'],
            'history_held': True, 'delivery_authorized': False,
            'readiness': result if fresh else None,
            'no_send_ready': bool(fresh and result.get('ready')), 'readiness_fresh': fresh}
