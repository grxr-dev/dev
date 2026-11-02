"""Compile ONE hypothesized C leaf and compare its exact ELF symbol to local ROM.

Diagnostic only: no linker, guest execution, original-toolchain/source match,
ROM rebuild or Gate0 certification. Generated files always stay in ignored local/.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import struct
import subprocess
import time
from elf_function import function, compare

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def sha(data):return hashlib.sha256(data).hexdigest()


def run(source=None, output=None, config=None):
    cfg=json.loads((config or HERE/'diagnostic_config.json').read_text(encoding='utf-8'))
    source=(source or HERE/'leaf_pilot.c').resolve()
    out=(output or ROOT/'local/matching_phase0/leaf-diagnostic').resolve()
    if not out.is_relative_to((ROOT/'local').resolve()):raise ValueError('outputs must stay in ignored local/')
    out.mkdir(parents=True,exist_ok=True)
    rom=ROOT.parent/cfg['rom_name'];raw=rom.read_bytes()
    if hashlib.sha1(raw).hexdigest()!=cfg['rom_sha1'] or sha(raw)!=cfg['rom_sha256']:raise ValueError('exact ROM identity gate failed')
    offset,entry,base,size=struct.unpack_from('<4I',raw,0x20)
    address=int(cfg['address'],16);start=address-base;length=cfg['size']
    if base!=0x02000000 or not 0<=start<=size-length or offset+size>len(raw):raise ValueError('ARM9 ROM bounds/load address')
    expected=raw[offset+start:offset+start+length]
    if sha(expected)!=cfg['reference_sha256']:raise ValueError('reference leaf hash mismatch')
    module=ROOT/cfg['extracted_arm9'];module_bytes=module.read_bytes()
    if module_bytes[start:start+length]!=expected:raise ValueError('existing extracted ARM9 differs from verified ROM')
    metadata=ROOT/cfg['metadata']
    symbols=(metadata/'arm9/symbols.txt').read_text(encoding='utf-8')
    symbol_line=[line for line in symbols.splitlines() if line.startswith(cfg['symbol']+' ')]
    if len(symbol_line)!=1 or f"function(arm,size=0x{length:x})" not in symbol_line[0]:raise ValueError('dsd leaf boundary/state evidence changed')
    original_relocations=[]
    for line in (metadata/'arm9/relocs.txt').read_text(encoding='utf-8').splitlines():
        where=re.search(r'from:0x([0-9a-f]+)',line)
        if where and address<=int(where[1],16)<address+length:original_relocations.append(line)
    calls={name:int(target,16) for name,target in cfg.get('arm_call_targets',{}).items()}
    if original_relocations != cfg.get('expected_original_relocations',[]):raise ValueError('original code relocations differ from explicit comparison policy')
    for line in original_relocations:
        m=re.fullmatch(r'from:0x([0-9a-f]+) kind:arm_call to:0x([0-9a-f]+) module:main',line)
        if not m or int(m[2],16) not in calls.values():raise ValueError('unapproved original call relocation')
        pc=int(m[1],16);word=struct.unpack_from('<I',module_bytes,pc-base)[0]
        imm=word&0xffffff;imm=imm-(1<<24) if imm&(1<<23) else imm
        if word>>24 != 0xeb or pc+8+(imm<<2) != int(m[2],16):raise ValueError('original BL opcode/target disagrees with metadata')
    inputs={str(p):sha(p.read_bytes()) for p in [rom,module,*sorted(metadata.rglob('*'))] if p.is_file()}
    compiler=ROOT/cfg['compiler']
    if sha(compiler.read_bytes())!=cfg['compiler_sha256']:raise ValueError('compiler binary differs from qualified official executable')
    env=dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(ROOT/'local/matching_phase0/toolchains/zig-cache'),ZIG_LOCAL_CACHE_DIR=str(out/'cache'),TMP=str(out),TEMP=str(out))
    def execute(argv,timeout=120):
        before=time.monotonic();p=subprocess.run([str(x) for x in argv],cwd=out,env=env,capture_output=True,encoding='utf-8',errors='replace',timeout=timeout,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        return {'argv':[str(x) for x in argv],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-before}
    version=execute([compiler,'version'],15)
    if version['exit_code'] or version['stdout'].strip()!=cfg['zig_version']:raise ValueError('compiler version mismatch')
    banner=execute([compiler,'cc','--version'],15)
    obj=out/'leaf.o';obj.unlink(missing_ok=True)
    compilation=execute([compiler,'cc',*cfg['flags'],'-c',source,'-o',obj])
    (out/'compiler.stdout.txt').write_text(compilation['stdout'],encoding='utf-8')
    (out/'compiler.stderr.txt').write_text(compilation['stderr'],encoding='utf-8')
    report={'classification':'DIAGNOSTIC_COMPILE_FAILED','gate0':'OPEN','original_toolchain_matched_c':0,
            'address':cfg['address'],'symbol':cfg['symbol'],'source':str(source),'source_sha256':sha(source.read_bytes()),
            'compiler':{'path':str(compiler),'sha256':cfg['compiler_sha256'],'zig_version':version['stdout'].strip(),'banner':banner['stdout'],'archive_sha256':cfg['archive_sha256']},
            'compile':compilation,'reference_sha256':sha(expected),'reference_size':length,'linked':False,
            'reference_hex':expected.hex(),'original_code_relocations':original_relocations,'reference_rom_offset':offset+start,'arm9_load_address':hex(base),'metadata_boundary':symbol_line[0]}
    if compilation['exit_code']==0:
        actual,info=function(obj.read_bytes(),cfg['symbol'],arm_calls=calls,runtime_address=address)
        if info['code_relocations'] != len(original_relocations):raise ValueError('call relocation count differs from selected original function')
        comparison=compare(expected,actual)
        import capstone
        decoder=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM|capstone.CS_MODE_LITTLE_ENDIAN)
        decoded=[{'address':hex(i.address),'size':i.size,'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(actual,address)]
        if sum(i['size'] for i in decoded)!=len(actual):raise ValueError('incomplete ARM disassembly')
        disassembly='\n'.join(f"{i['address']}: {i['mnemonic']} {i['operands']}" for i in decoded)+'\n'
        (out/'leaf.disassembly.txt').write_text(disassembly,encoding='utf-8');(out/'leaf.code.bin').write_bytes(actual)
        original_decoded=[{'address':hex(i.address),'size':i.size,'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(expected,address)]
        if sum(i['size'] for i in original_decoded)!=length:raise ValueError('incomplete original ARM disassembly')
        report['original_disassembly']=original_decoded
        report.update(classification='PASS_DIAGNOSTIC_INSTRUCTION_MATCH' if comparison['equal'] else 'FAIL_DIAGNOSTIC_BYTE_MISMATCH',
                      object_sha256=sha(obj.read_bytes()),elf=info,compiled_hex=actual.hex(),compiled_sha256=sha(actual),comparison=comparison,
                      disassembly=decoded,disassembler={'name':'Capstone','version':capstone.__version__},
                      original_runtime_address_linked=False,explicit_call_relocations_resolved=bool(calls),diagnostic_matched_functions=int(comparison['equal']))
    report['inputs_unchanged']=all(sha(Path(path).read_bytes())==digest for path,digest in inputs.items())
    if not report['inputs_unchanged']:raise ValueError('ROM/extracted payload/metadata changed')
    report['input_sha256']=inputs
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['classification']+'; original-toolchain matched C=0; Gate0 OPEN')
    if report.get('compiled_hex'):print('compiled='+report['compiled_hex']+'; differing bytes='+str(len(report['comparison']['differences'])))
    return 0 if report['classification']=='PASS_DIAGNOSTIC_INSTRUCTION_MATCH' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--source',type=Path);p.add_argument('--output',type=Path);args=p.parse_args()
    raise SystemExit(run(args.source,args.output,args.config))
