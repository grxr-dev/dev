"""Lossless scalar-only AW9 terminal binding. No guest, bus, or runner APIs."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AW9 = 'fb3e417aa48cc70cc4c05f796263c9cf87b791af'
AW10 = 'c699e3a21207abaa72b8130bf54c0f189c846412'
FINAL = 'ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526'
SCHEMA = 'AW11 scalar terminal metadata v1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def committed(path, authority=AW9):
    return subprocess.check_output(['git', 'show', authority + ':' + path], cwd=ROOT)


def ownership(name):
    if name.startswith('cap.') or name in ['capture.epoch', 'capture.serial', 'capture.rom_epoch']:
        return 'journal'
    if name in ['capture.end_cycle', 'capture.end_ordinal']:
        return 'io'
    if name.startswith(('code.', 'literal.', 'protected.', 'timing.')) or name == 'dtcm_stack_word':
        return 'bus'
    if name.startswith(('cp15.', 'itcm.', 'dtcm_map.', 'hidden.permission.')):
        return 'cp15'
    if name in ['hidden.code_pc9', 'hidden.code_pc7', 'hidden.data_addr9', 'hidden.data_addr7',
                'hidden.cache_page', 'hidden.cache_generation', 'hidden.cache_class',
                'hidden.region_class', 'hidden.region_valid', 'hidden.class_ready'] or name.startswith(('hidden.code_bit.', 'hidden.data_bit.')):
        return 'bus'
    if re.fullmatch(r'r\d+', name) or name.startswith(('return.', 'hidden.bank.')) or name in [
            'cpsr', 'cycle9', 'ordinal9', 'ordinal7', 'snapshot_ordinal', 'active_cpu', 'force_tier3',
            'slice_cap', 'fast_limit', 'deferred9', 'terminal', 'insn_stop', 'event_break', 'unwinding',
            'return_depth', 'hidden.yield', 'hidden.cpu_poll', 'hidden.force_misses', 'hidden.fast_enabled',
            'hidden.break_pc', 'hidden.static_changed', 'hidden.fast_publishes', 'hidden.dispatch_epoch']:
        return 'runtime'
    if name.startswith(('scheduler.', 'slot9.')) or name in [
            'owner_thread', 'round_active', 'current_slot', 'system_timestamp', 'cycle7', 'deferred7',
            'arm7_started', 'arm7_terminal', 'synth_config', 'wifi.deadline', 'service.spu_mixes', 'service.gpu_debt']:
        return 'scheduler'
    if name.startswith(('irq9.', 'irq7.', 'timer.', 'dma.', 'div.', 'service.halt_epoch.', 'service.dma_entry.')) or name in [
            'halt9', 'halt7', 'gpu_stall', 'card_end', 'card.deadline', 'spi.deadline', 'auxspi.deadline',
            'sqrt.deadline', 'service.irq_cache9', 'service.irq_cache7', 'service.card_control',
            'service.spi_control', 'service.auxspi_control', 'service.powered_off', 'service.firmware_dirty',
            'service.display_last', 'service.rtc_processed', 'service.rtc_due', 'save_dirty', 'logical_saves', 'flash_commits']:
        return 'io'
    raise ValueError('Unowned protected field: ' + name)


OWNERS = {
    'journal': ['tools/task_aw3/bridge.h', 'export_history'],
    'runtime': ['tools/task_aw3/runtime.inc', 'runtime_snapshot'],
    'scheduler': ['tools/task_aw3/scheduler.inc', 'scheduler_snapshot'],
    'bus': ['tools/task_aw3/bus.inc', 'bus_snapshot'],
    'cp15': ['tools/task_aw3/cp15.inc', 'cp15_snapshot'],
    'io': ['tools/task_aw3/io.inc', 'io_snapshot']
}
IDENTITY_OWNERS = {'dtcm': 'bus', 'mainram': 'bus', 'save': 'io', 'rom': 'io', 'framework_commit': 'io'}


def encode(fields, identities):
    data = bytearray(b'AW2S\x01\x00')
    def number(value, width):
        require(type(value) is int and 0 <= value < 1 << (width * 8), 'scalar domain/width')
        data.extend(value.to_bytes(width, 'little'))
    def text(value):
        raw = value.encode('ascii')
        number(len(raw), 2)
        data.extend(raw)
    number(len(fields), 4)
    previous = ''
    for name, width, value in fields:
        require(re.fullmatch(r'[a-z0-9_.]+', name) and name > previous, 'field order/duplicate/name')
        require(width in [1, 2, 4, 8], 'scalar width')
        text(name)
        number(width, 1)
        number(value, width)
        previous = name
    number(len(identities), 4)
    previous = ''
    for name, value in identities:
        require(name > previous and re.fullmatch(r'[a-z0-9_.]+', name), 'identity order/name')
        require(len(value) in [40, 64] and re.fullmatch(r'[a-f0-9]+', value), 'identity digest')
        text(name)
        text(value)
        previous = name
    return bytes(data)


def decode(data):
    require(data[:6] == b'AW2S\x01\x00', 'AW2S version')
    cursor = 6
    def number(width):
        nonlocal cursor
        require(cursor + width <= len(data), 'truncated integer')
        value = int.from_bytes(data[cursor:cursor + width], 'little')
        cursor += width
        return value
    def text():
        nonlocal cursor
        size = number(2)
        require(cursor + size <= len(data), 'truncated string')
        value = data[cursor:cursor + size].decode('ascii')
        cursor += size
        return value
    fields = []
    count = number(4)
    require(count <= 4096, 'field count')
    for _ in range(count):
        name, width = text(), number(1)
        require(width in [1, 2, 4, 8], 'decoded width')
        fields.append([name, width, number(width)])
    count = number(4)
    require(count <= 128, 'identity count')
    identities = [[text(), text()] for _ in range(count)]
    require(cursor == len(data) and encode(fields, identities) == data, 'canonical round trip')
    return fields, identities


def validate(record):
    require(record['schema'] == SCHEMA and record['AW9_commit'] == AW9, 'metadata authority')
    live = json.loads(committed('docs/BrainAge_TaskAW9_Result.json'))
    require(record['audit_sha256'] == live['audit_sha256'], 'audit binding')
    require(record['canonical_sha256'] == live['final_digest'] == FINAL, 'terminal commitment')
    require(record['owners'] == OWNERS and record['identity_owners'] == IDENTITY_OWNERS, 'ownership specification')
    fields, identities = record['fields'], record['identities']
    require(len(fields) == 411 and len(identities) == 5, 'complete terminal cardinality')
    require(record['field_owners'] == [[row[0], ownership(row[0])] for row in fields], 'missing/wrong field ownership')
    data = encode(fields, identities)
    require(hashlib.sha256(data).hexdigest() == FINAL, 'terminal scalar identity')
    require(dict(identities) == live['final_identities'], 'immutable identities')
    projection = json.loads(committed('tools/task_aw10/certificate.json', AW10))['certificate']['entry']
    values = {name: {'width': width, 'value': value} for name, width, value in fields}
    require(all(values.get(name) == cell for name, cell in projection['scalars'].items()), 'AW10 89-scalar reconciliation')
    return data


def load():
    record = json.loads((Path(__file__).parent / 'terminal.json').read_text())
    validate(record)
    return record


def promote():
    target = Path(__file__).parent / 'terminal.json'
    require(not target.exists(), 'immutable fixture already exists')
    live = json.loads(committed('docs/BrainAge_TaskAW9_Result.json'))
    capture = ROOT / 'local/task-aw9/attempt-001/capture.jsonl'
    raw = capture.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == live['audit_sha256'], 'historical audit authentication')
    rows = [json.loads(line) for line in raw.splitlines()]
    snapshots = [row for row in rows if row['event'] == 'canonical_snapshot']
    require(rows[-1]['event'] == 'terminal', 'historical terminal event')
    snapshot = snapshots[-1]
    require(snapshot['sha256'] == FINAL, 'historical terminal identity')
    data = bytes.fromhex(snapshot['canonical_hex'])
    require(hashlib.sha256(data).hexdigest() == FINAL, 'historical canonical bytes')
    fields, identities = decode(data)
    record = {'schema': SCHEMA, 'AW9_commit': AW9, 'audit_sha256': live['audit_sha256'],
              'canonical_sha256': FINAL, 'owners': OWNERS, 'identity_owners': IDENTITY_OWNERS,
              'fields': fields, 'identities': identities,
              'field_owners': [[row[0], ownership(row[0])] for row in fields]}
    validate(record)
    sections = []
    for name, value in record.items():
        if name in ['fields', 'field_owners']:
            rendered = '[\n' + ',\n'.join('    ' + json.dumps(row) for row in value) + '\n  ]'
        else:
            rendered = json.dumps(value, sort_keys=True)
        sections.append('  ' + json.dumps(name) + ': ' + rendered)
    body = '{\n' + ',\n'.join(sections) + '\n}\n'
    patch = '*** Begin Patch\n*** Add File: tools/task_aw11/terminal.json\n'
    patch += ''.join('+' + line + '\n' for line in body.splitlines()) + '*** End Patch\n'
    subprocess.run([str(Path.home() / 'AppData/Local/OpenAI/Codex/bin/9691020b546a15b2/codex.exe'),
                    '--codex-run-as-apply-patch', patch], cwd=ROOT, check=True)
    require(hashlib.sha256(capture.read_bytes()).hexdigest() == live['audit_sha256'], 'historical evidence changed')
    print(json.dumps({'promoted_scalars': len(fields), 'identities': len(identities), 'canonical_sha256': FINAL}))


if __name__ == '__main__':
    promote()
