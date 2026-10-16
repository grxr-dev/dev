"""Offline scalar proof only. No runtime, image, checkpoint, or launch API."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = '9c2b342f4fdf1f09316ce7d62ac2240edc0f9589'
sys.path.insert(0, str(ROOT / 'tools/task_aw11'))
import state

FENCE = '3528c2be122178850a3d3c78157cdd1adaf5409e5eb32f6d794e1c3f81d27d84'
GPU = '708de6de2568d09123820267c9daaa7abd49321e90e275923ac93d96513ad5d4'
STAGES = ['fence_bound', 'device_observer', 'ARM9_timers', 'GPU_wrapper',
          'ARM7_HALT_catchup', 'ARM7_timers', 'poweroff_check', 'display',
          'SPU', 'Wifi_no_event', 'RTC', 'system_events', 'system_timestamp',
          'pre_overlay_stop']


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def committed(path):
    return subprocess.check_output(['git', 'show', AUTHORITY + ':' + path], cwd=ROOT)


def binding():
    metadata = json.loads(committed('tools/task_aw14/fence.json'))
    require(json.loads((ROOT / 'tools/task_aw14/fence.json').read_text()) == metadata, 'committed metadata drift')
    baseline = state.load()
    core = copy.deepcopy(baseline['fields'])
    for change in metadata['core']['changes']:
        row = next(item for item in core if item[0] == change['name'])
        require(row[1:] == [change['width'], change['before']], 'base delta')
        row[2] = change['after']
    identities = baseline['identities']
    gpu = metadata['GPU']['fields']
    validate(core, identities, gpu)
    previous = baseline['canonical_sha256']
    names = ['yield_requested', 'tier3_exit', 'unwind_preserved', 'slice_consumed', 'slot_saved',
             'pre_device_fence', 'gpu_observed', 'scheduler_admitted_capture_only']
    for index, record in enumerate(metadata['ownership']['transcript']):
        fields = copy.deepcopy(baseline['fields'])
        if index >= 2:
            put(fields, 'unwinding', 1)
        if index >= 4:
            put(fields, 'slot9.cycle', 3416875777)
        require(record['event'] == names[index] and record['index'] == index, 'fence event order')
        extension = state.encode(gpu, []) if index >= 6 else state.encode([], [])
        material = previous.encode() + state.encode(fields, identities) + extension
        material += struct.pack('<QQBBIQ', index, 1, record['phase'], record['saved_valid'],
                                record['frame_depth'], metadata['ownership']['frame'])
        label = record['event'].encode()
        previous = sha(material + struct.pack('<H', len(label)) + label)
        require(previous == record['chain'], 'fence ownership chain')
    require(len(metadata['ownership']['transcript']) == 8 and metadata['ownership']['frame'] == 566
            and metadata['ownership']['ticket'] == 1, 'fence ownership identity')
    return core, identities, gpu, metadata


def validate(core, identities, gpu):
    require(len(core) == 411 and len(identities) == 5 and len(gpu) == 19, 'complete entry')
    require(sha(state.encode(core, identities)) == FENCE, 'immutable fence binding')
    require(sha(state.encode(gpu, [])) == GPU, 'immutable GPU binding')


def value(fields, name):
    return next(row[2] for row in fields if row[0] == name)


def put(fields, name, number):
    row = next(item for item in fields if item[0] == name)
    require(0 <= number < 1 << (row[1] * 8), 'transition overflow')
    row[2] = number


def tick(fields, cpu, timestamp):
    last = value(fields, f'timer.{cpu * 4}.last')
    require(timestamp >= last, 'timer rewind')
    for index in range(cpu * 4, cpu * 4 + 4):
        prefix = f'timer.{index}.'
        require(value(fields, prefix + 'last') == last, 'timer shared-latch disagreement')
        put(fields, prefix + 'last', timestamp)
        control = value(fields, prefix + 'control')
        if not control & 128:
            continue
        ticks = 0
        if not control & 4:
            prescale = [1, 64, 256, 1024][control & 3]
            ticks, accum = divmod(value(fields, prefix + 'accum') + timestamp - last, prescale)
            put(fields, prefix + 'accum', accum)
        counter = value(fields, prefix + 'counter')
        require(counter + ticks < 65536, 'timer overflow/service forbidden')
        put(fields, prefix + 'counter', counter + ticks)


def projections(core, identities, gpu):
    validate(core, identities, gpu)
    core, gpu = copy.deepcopy(core), copy.deepcopy(gpu)
    result = []
    rendezvous = value(core, 'cycle9') >> 1
    require(rendezvous == 1708437888, 'half-rate conversion')
    for stage in STAGES:
        if stage == 'ARM9_timers':
            tick(core, 0, rendezvous)
        elif stage == 'GPU_wrapper':
            require(not value(gpu, 'gpu.pipe.count') and not value(gpu, 'gpu.stat') & (1 << 27), 'GPU work eligible')
            put(gpu, 'gpu.arm9_timestamp', value(core, 'cycle9'))
            put(gpu, 'gpu.timestamp', rendezvous)
        elif stage == 'ARM7_HALT_catchup':
            require(value(core, 'halt7') == 1 and value(core, 'deferred7') == 2, 'ARM7 HALT/debt provenance')
            require(not value(core, 'irq7.ie') & value(core, 'irq7.if'), 'ARM7 wake eligible')
            require(all(not value(core, f'dma.{index}.active') for index in range(4, 8)), 'ARM7 DMA eligible')
            put(core, 'cycle7', rendezvous)
        elif stage == 'ARM7_timers':
            tick(core, 1, rendezvous)
        elif stage == 'poweroff_check':
            require(not value(core, 'service.powered_off'), 'poweroff')
        elif stage == 'display':
            last = value(core, 'service.display_last')
            require(last // 2130 == rendezvous // 2130 and
                    (last - 1584) // 2130 == (rendezvous - 1584) // 2130, 'display edge eligible')
            put(core, 'service.display_last', rendezvous)
        elif stage == 'SPU':
            require(value(core, 'service.spu_mixes') >= rendezvous // 1024, 'SPU mix eligible')
        elif stage == 'Wifi_no_event':
            require(value(core, 'wifi.deadline') > rendezvous, 'Wifi event eligible')
        elif stage == 'RTC':
            require(value(core, 'service.rtc_processed') >= ((rendezvous + 1) * 32768 - 1) // 33513982, 'RTC work eligible')
        elif stage == 'system_events':
            require(all(value(core, name + '.deadline') > rendezvous
                        for name in ['auxspi', 'spi', 'card', 'div', 'sqrt']), 'system event eligible')
        elif stage == 'system_timestamp':
            put(core, 'system_timestamp', rendezvous)
            put(core, 'service.rtc_due', rendezvous * 32768 // 33513982)
        result.append({'event': stage, 'core': copy.deepcopy(core), 'gpu': copy.deepcopy(gpu),
                       'core_sha256': sha(state.encode(core, identities)), 'GPU_sha256': sha(state.encode(gpu, []))})
    return result


class Ledger:
    def __init__(self, core, identities, gpu):
        self.plan = projections(core, identities, gpu)
        self.identities = copy.deepcopy(identities)
        self.cursor, self.failed, self.previous = 0, False, FENCE

    def accept(self, event, core, identities, gpu, previous):
        try:
            require(not self.failed and self.cursor < len(self.plan), 'sticky failure/extra event')
            expected = self.plan[self.cursor]
            require(previous == self.previous, 'chain rewind/tamper')
            require(event == expected['event'], 'missing/duplicate/reordered/forbidden event')
            require(core == expected['core'] and gpu == expected['gpu'] and identities == self.identities, 'full protected transition mismatch')
            material = previous.encode() + state.encode(core, identities) + state.encode(gpu, [])
            self.previous = sha(material + struct.pack('<QH', self.cursor, len(event)) + event.encode())
            self.cursor += 1
        except Exception:
            self.failed = True
            raise

    def finish(self):
        require(not self.failed and self.cursor == len(self.plan), 'incomplete/sticky transcript')
        return self.previous


def conditional_next(core):
    timestamp = value(core, 'system_timestamp')
    line = timestamp // 2130 * 2130
    lcd = line + (1584 if timestamp - line < 1584 else 2130)
    spu = (timestamp // 1024 + 1) * 1024
    ordinal = timestamp * 32768 // 33513982 + 1
    rtc = ordinal * 33513982 // 32768
    while rtc <= timestamp:
        ordinal += 1
        rtc = ordinal * 33513982 // 32768
    candidates = {name: value(core, name + '.deadline') for name in ['auxspi', 'spi', 'card', 'div', 'sqrt', 'wifi']}
    candidates.update(LCD=lcd, SPU=spu, RTC=rtc)
    selected = min(candidates.values())
    planned = selected if selected < timestamp + 72 else timestamp + 64
    return {'conditional_only': True, 'deadlines': candidates, 'rendezvous': timestamp,
            'system_target': planned, 'ARM9_target': planned << 1,
            'quantum': (planned << 1) - value(core, 'slot9.cycle'),
            'next_PC': '0x020019B4', 'fetch_authorized': False}


def conditional_slice_state(core):
    result = conditional_next(core)
    projected = [row[:] for row in core if not row[0].startswith('cap.')]
    for name, number in [('capture.epoch', value(core, 'capture.epoch') + 1),
                         ('capture.serial', value(core, 'capture.serial') + 1),
                         ('scheduler.round_epoch', value(core, 'scheduler.round_epoch') + 1),
                         ('scheduler.planned_target', result['ARM9_target']),
                         ('scheduler.next_event', result['system_target']),
                         ('slot9.target', result['ARM9_target']), ('slice_cap', result['ARM9_target']),
                         ('fast_limit', 0), ('hidden.yield', 1), ('terminal', 0)]:
        put(projected, name, number)
    projected.append(['cap.count', 4, 1])
    entries = {'kind': (1, 0), 'cpu': (1, 0), 'cycle': (8, value(core, 'cycle9')),
               'before': (8, 0), 'after': (8, result['ARM9_target']),
               'base': (8, value(core, 'cycle9')), 'quantum': (8, result['quantum']),
               'deadline': (8, 0), 'serial': (8, value(core, 'capture.serial') + 1),
               'observed_before': (8, value(core, 'slice_cap'))}
    projected.extend([[f'cap.0.{name}', width, number] for name, (width, number) in entries.items()])
    return sorted(projected)
