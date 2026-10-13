"""Install diagnostic-only capture hooks. Never launch a runner, enable capture or dispatch AX."""
import hashlib
import difflib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'local/ndsrecomp/runner/src'


def once(text, anchor, replacement):
    if replacement in text:
        return text
    assert text.count(anchor)==1, anchor
    return text.replace(anchor,replacement)


def main():
    assert subprocess.check_output(['git','-C',str(SOURCE.parents[1]),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
    names=['runtime_arm.cpp','scheduler.cpp','bus.cpp','io.cpp','cp15.cpp','tier3.cpp',
           'task_au_setup.inc','brainage_task_au.h','brainage_flash_trace.h','brainage_task_c_trace.h']
    originals={name:(SOURCE/name).read_text(encoding='utf-8-sig') for name in names}
    updated=dict(originals)
    for name in names:
        if '#include "aw3/bridge.h"' not in updated[name]:
            updated[name]='#include "aw3/bridge.h"\n'+updated[name]
    text=updated['runtime_arm.cpp']
    obsolete='    if (task_aw3::armed) { const auto target=g_nds_active==NDS_ARM9 ? task_aw2::twice(system_deadline) : system_deadline; task_aw3::cap_note(1,g_nds_active,g_runtime_cycles,g_cycle_cap,g_cycle_cap ? std::min(g_cycle_cap,target) : target,system_deadline); }\n'
    text=text.replace(obsolete,'')
    for anchor,replacement in [
        ('extern "C" void nds_set_cycle_cap(unsigned long long cap) {',
         'extern "C" void nds_set_cycle_cap(unsigned long long cap) {\n    task_aw3::cap_note(2,g_nds_active,g_runtime_cycles,g_cycle_cap,cap);'),
        ('    if (g_cycle_cap == 0 || cpu_deadline < g_cycle_cap) {',
         '    task_aw3::reschedule(g_nds_active,g_runtime_cycles,g_cycle_cap,system_deadline);\n    if (g_cycle_cap == 0 || cpu_deadline < g_cycle_cap) {'),
        ('extern "C" void nds_slice_begin(unsigned long long cap) {',
         'extern "C" void nds_slice_begin(unsigned long long cap) {\n    task_aw3::cap_note(0,g_nds_active,g_runtime_cycles,g_cycle_cap,cap);'),
        ('extern "C" void nds_halt(const char* reason) {',
         'extern "C" void nds_halt(const char* reason) {\n    if (task_aw3::armed) task_aw3::fail(reason ? reason : "ordinary halt denied");'),
        ('    g_insn_count[0] = in.insn_count[0];','    task_aw3::invalidate();\n    g_insn_count[0] = in.insn_count[0];')]:
        text=once(text,anchor,replacement)
    updated['runtime_arm.cpp']=text
    text=updated['scheduler.cpp']
    text=once(text,'uint64_t           g_sys_timestamp = 0;',
              'uint64_t g_aw3_round_epoch=0,g_aw3_planned_target=0,g_aw3_next_event=0;\nuint64_t           g_sys_timestamp = 0;')
    text=once(text,'    const uint64_t arm9_target = planned << kArm9ClockShift;',
              '    const uint64_t arm9_target = planned << kArm9ClockShift;\n    if (task_aw3::armed) { ++g_aw3_round_epoch; g_aw3_planned_target=arm9_target; g_aw3_next_event=ev; }')
    updated['scheduler.cpp']=text
    updated['io.cpp']=once(updated['io.cpp'],'    g_card_rom.assign(rom, rom + rom_size);',
        '    task_aw3::loaded_rom(rom,rom_size);\n    g_card_rom.assign(rom, rom + rom_size);')
    for name,signature in [
        ('bus.cpp','bool bus_savestate_import(const NdsBusMemorySnapshot& in, std::string* error) {'),
        ('cp15.cpp','bool cp15_savestate_import(const NdsCp15SaveState& in, std::string* error) {'),
        ('io.cpp','bool io_savestate_import(const NdsIoCoreSaveState& in, std::string* error) {'),
        ('io.cpp','bool io_peripheral_savestate_import(const NdsIoPeripheralSaveState& in,\n                                    std::string* error) {'),
        ('scheduler.cpp','bool scheduler_savestate_import(const NdsSchedulerSaveState& in,\n                                std::string* error) {')]:
        updated[name]=once(updated[name],signature,signature+'\n    task_aw3::invalidate();')
    updated['task_au_setup.inc']=once(updated['task_au_setup.inc'],
        '        file("decision-after-mainram.bin",ram);',
        '        if (task_aw3::armed) task_aw3::handoff();\n        file("decision-after-mainram.bin",ram);')
    updated['brainage_task_au.h']=once(updated['brainage_task_au.h'],'inline void finish(int code){',
        'inline void finish(int code){\n    if (task_aw3::armed) task_aw3::fail("AU finish/halt forbidden during capture");')
    updated['tier3.cpp']=once(updated['tier3.cpp'],
        '        if (brainage_task_au::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }',
        '        try {\n            if (brainage_task_au::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }\n        } catch (...) { if (task_aw3::armed) task_aw3::fail("AU guard threw before ownership handoff"); throw; }\n        if (task_aw3::armed && ic.R[15]==0x02001980) task_aw3::fail("pre-MMIO handoff returned; AX forbidden");')
    updated['brainage_task_c_trace.h']=once(updated['brainage_task_c_trace.h'],
        'inline void task_c_snapshot(uint32_t pc, bool thumb, const uint32_t* registers) {',
        'inline void task_c_snapshot(uint32_t pc, bool thumb, const uint32_t* registers) {\n    if (task_aw3::armed && g_nds_active==NDS_ARM9 && pc==0x0202fcc0u) ++task_aw3::logical_saves;')
    updated['brainage_flash_trace.h']=once(updated['brainage_flash_trace.h'],
        '    if (task_b_armed && offset == 0x18f && last) task_b_done = true;',
        '    if (task_aw3::armed) ++task_aw3::flash_commits;\n    if (task_b_armed && offset == 0x18f && last) task_b_done = true;')
    for name,part in [('runtime_arm.cpp','runtime'),('scheduler.cpp','scheduler'),('bus.cpp','bus'),('io.cpp','io'),('cp15.cpp','cp15')]:
        suffix=f'\n#include "aw3/{part}.inc"\n'
        if suffix not in updated[name]: updated[name]+=suffix
    bundle={}
    for name in ['bridge.h','runtime.inc','scheduler.inc','bus.inc','io.inc','cp15.inc']:
        bundle[name]=(HERE/name).read_text().replace('../task_aw2/','aw2/')
    for name in ['canonical.h','au_manifest.h','model.h','controller.h','fixture.h']:
        bundle['aw2/'+name]=(ROOT/'tools/task_aw2'/name).read_text().replace('../brainage_custom/bc_resource_hash.h','../../bc_resource_hash.h').replace('../task_aw/bridge.h','../../task_aw_bridge.h')
    binary=Path.home()/'AppData/Local/OpenAI/Codex/bin/9691020b546a15b2/codex.exe'
    for path,text in [(SOURCE/name,text) for name,text in updated.items()]+[(SOURCE/'aw3'/name,text) for name,text in bundle.items()]:
        old=path.read_text(encoding='utf-8-sig') if path.exists() else None
        if old==text: continue
        patch='*** Begin Patch\n'
        if old is None: patch+=f'*** Add File: {path.as_posix()}\n'+''.join('+'+line+'\n' for line in text.splitlines())
        else:
            diff=list(difflib.unified_diff(old.splitlines(),text.splitlines(),n=3))[2:]
            patch+=f'*** Update File: {path.as_posix()}\n'+''.join(('@@' if line.startswith('@@') else line)+'\n' for line in diff)
        patch+='*** End Patch\n'
        subprocess.run([str(binary),'--codex-run-as-apply-patch',patch],check=True)
    out=ROOT/'local/task-aw3'
    out.mkdir(exist_ok=True)
    record=out/('installation-latest.json' if (out/'installation.json').exists() else 'installation.json')
    record.write_text(json.dumps({'before':{name:hashlib.sha256(value.encode()).hexdigest() for name,value in originals.items()},
        'after':{name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in names},'armed':False,'guest_executed':False},indent=2)+'\n')


if __name__=='__main__': main()
