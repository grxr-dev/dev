"""Independent protected-state oracle using committed AW14/AW15 scalar metadata."""
import copy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/task_aw15'))
import model


def check_states(observed):
    core, identities, gpu, metadata = model.binding()
    prior = {row['event']: row for row in model.projections(core, identities, gpu)}
    mapping = [
        ('successor_admitted','fence_bound'),('scheduler_device','fence_bound'),('timer9_entry','fence_bound'),
        ('timers9_done','ARM9_timers'),('gpu_done','GPU_wrapper'),('slice7_gate','GPU_wrapper'),('arm7_entry','GPU_wrapper'),
        ('arm7_done','ARM7_HALT_catchup'),('timer7_entry','ARM7_HALT_catchup'),('timers7_done','ARM7_timers'),
        ('power_checked','poweroff_check'),('display_done','display'),('spu_done','SPU'),('wifi_done','Wifi_no_event'),
        ('rtc_entry','Wifi_no_event'),('rtc_done','RTC'),('system_entry','RTC'),('system_done','system_events'),
        ('time_published','system_timestamp'),('overlay_done','system_timestamp'),('round_left','system_timestamp'),
        ('next_scheduler','system_timestamp'),('round_entered','system_timestamp'),('target_selected','system_timestamp'),
        ('slice9_gate','system_timestamp'),('slice_begun_stop','system_timestamp')]
    model.require(len(observed) == len(mapping), 'independent complete phase count')
    initial = copy.deepcopy(observed[0]['auxiliary'])
    widths = {'aux.schema':2,'journal.bound':1,'overlay.enabled':1,'wifi.network_enabled':1,'wifi.bridge':1,'wifi.device':1,
              'wifi.worker':1,'wifi.scheduled':1,'wifi.raw_deadline':8,'wifi.timestamp':8,'trace.count':8,
              'trace.last.count':8,'trace.last.cycle':8,'trace.last.before':4,'trace.last.after':4,
              'trace.last.debt_before':4,'trace.last.debt_after':4,'scheduler.modulus':8,'scheduler.sample':1}
    model.require({name:width for name,width,number in initial} == widths, 'independent auxiliary schema')
    get = lambda name: model.value(initial, name)
    model.require(get('aux.schema') == 1 and all(get(name) == 0 for name in [
        'journal.bound','overlay.enabled','wifi.network_enabled','wifi.worker','wifi.scheduled','scheduler.modulus','scheduler.sample']),
        'independent auxiliary readiness')
    model.require(get('wifi.bridge') in [0,1] and get('wifi.device') in [0,1] and get('trace.count') < (1 << 64) - 1,
                  'independent presence/trace domain')
    model.require(get('trace.last.count') == get('trace.count') and get('wifi.timestamp') <= 1708437888,
                  'independent trace/time relation')
    if not get('wifi.bridge'):
        model.require(not any(get(name) for name in ['wifi.device','wifi.timestamp','wifi.raw_deadline']), 'absent bridge consistency')
    for index, (label, source) in enumerate(mapping):
        expected_core = copy.deepcopy(prior[source]['core'])
        expected_gpu = copy.deepcopy(prior[source]['gpu'])
        extra = copy.deepcopy(initial)
        if index >= 4:
            for name, number in [('trace.count',get('trace.count') + 1),('trace.last.count',get('trace.count') + 1),
                ('trace.last.cycle',3416875777),('trace.last.before',0x80000000),('trace.last.after',0x80000000),
                ('trace.last.debt_before',0),('trace.last.debt_after',0)]:
                model.put(extra,name,number)
        if index >= 13 and get('wifi.bridge') and get('wifi.device'):
            model.put(extra,'wifi.timestamp',1708437888)
        if index in [20,21]:
            model.put(expected_core,'round_active',0)
        if index in [23,24]:
            model.put(expected_core,'scheduler.round_epoch',1169)
            model.put(expected_core,'scheduler.planned_target',3416875826)
            model.put(expected_core,'scheduler.next_event',1708437913)
        if index == 25:
            expected_core = model.conditional_slice_state(expected_core)
        row = observed[index]
        model.require(row['label'] == label and row['fields'] == expected_core and row['identities'] == identities,
                      'independent full core/identity transition: ' + label)
        model.require(row['gpu'] == expected_gpu and row['auxiliary'] == extra,
                      'independent full GPU/auxiliary transition: ' + label)
    return len(mapping)
