"""One bounded byte-reader pilot; no live guest execution or generic ARM API.

Uses the existing compiler/ELF comparator. The small trace checker implements
only the decoded operations present in this pilot, rejects everything else,
and bounds every read inside the supplied immutable object BEFORE indexing.
Raw original bytes/disassembly and detailed evidence stay in ignored local/.
"""
import itertools
import json
import re
import struct
import capstone
from diagnostic import ROOT, HERE, run, sha

CFG = HERE / 'nul_count_config.json'
OUT = ROOT / 'local/matching_phase0/nul-count-pilot'
MASK = 0xffffffff


def decode(code, address):
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    rows = [(i.address, i.mnemonic, i.op_str) for i in cs.disasm(code, address)]
    if len(rows)*4 != len(code):
        raise ValueError('incomplete ARM decode')
    return rows


def trace(rows, data, base=0x1000):
    """Bounded semantic check, not an independently qualified ARM emulator.

    Precheck is intentionally NOT a modeled guest read. Unterminated/invalid
    objects never enter the trace. Each modeled load separately checks bounds.
    """
    if not isinstance(data, bytes) or not data or 0 not in data:
        raise ValueError('a nonempty allocated object containing NUL is required')
    if base <= 0 or base + len(data) > MASK or len(data) > MASK:
        raise ValueError('nonnull/nonwrapping object required')
    program = {pc: (op, args) for pc, op, args in rows}
    if len(program) != len(rows):
        raise ValueError('duplicate PC')
    regs = {f'r{i}': 0xabc00000+i for i in range(13)}
    regs.update(r0=base, sp=0x8000, lr=0x9000)
    saved = {k: v for k, v in regs.items() if k not in ('r0','r1','r2','r3')}
    pc = rows[0][0]
    flags = (1, 0, 0, 1)  # N,Z,C,V; deliberately not the eventual CMP result.
    reads, path = [], []

    def value(s):
        return int(s[1:], 0) & MASK if s.startswith('#') else regs[s]

    for _ in range(8*len(data)+20):
        if pc not in program:
            raise ValueError('escaped function without BX LR')
        op, args = program[pc]
        path.append(pc)
        next_pc = pc+4
        if op in ('ldrb', 'ldrsb'):
            m = re.fullmatch(r'(r[0-9]+), \[(r[0-9]+)(?:, (r[0-9]+))?\](?:, #1)?', args)
            if not m:
                raise ValueError('unsupported byte addressing')
            dest, ptr, index = m.groups()
            address = (regs[ptr] + (regs[index] if index else 0)) & MASK
            offset = address-base
            if not 0 <= offset < len(data):
                raise ValueError('out-of-object modeled read')
            byte = data[offset]
            reads.append({'pc': pc, 'offset': offset, 'width': 1, 'byte': byte})
            regs[dest] = (byte-256 if op == 'ldrsb' and byte >= 128 else byte) & MASK
            if args.endswith('], #1'):
                regs[ptr] = (regs[ptr]+1) & MASK
        elif op in ('mov', 'moveq'):
            dest, source = args.split(', ')
            if op == 'mov' or flags[1]:
                regs[dest] = value(source)
        elif op == 'add':
            dest, left, right = args.split(', ')
            regs[dest] = (value(left)+value(right)) & MASK
        elif op == 'cmp':
            left, right = args.split(', ')
            a, b = value(left), value(right)
            result = (a-b) & MASK
            flags = (result >> 31, int(result == 0), int(a >= b),
                     int(bool(((a ^ b) & (a ^ result)) & 0x80000000)))
        elif op in ('beq', 'bne'):
            if bool(flags[1]) == (op == 'beq'):
                next_pc = value(args)
        elif op in ('bx', 'bxeq') and args == 'lr':
            if op == 'bx' or flags[1]:
                if any(regs[k] != v for k, v in saved.items()):
                    raise ValueError('preserved register changed')
                return {'return': regs['r0'], 'registers': regs, 'nzcv': flags,
                        'reads': reads, 'path': path, 'return_pc': regs['lr']}
        else:
            raise ValueError('unsupported operation: '+op+' '+args)
        pc = next_pc
    raise ValueError('bounded trace instruction budget exceeded')


def verify_case(original, compiled, data, alignment=0):
    expected = data.index(0)
    left = trace(original, data, 0x1000+alignment)
    right = trace(compiled, data, 0x1000+alignment)
    for result in (left, right):
        assert result['return'] == expected
        assert [r['offset'] for r in result['reads']] == list(range(expected+1))
        assert all(r['width'] == 1 for r in result['reads'])
        assert result['nzcv'] == (0,1,1,0)
    return left, right


def cases():
    # Exhaust all words of length <=5 over zero/positive/high-bit classes.
    for length in range(1,6):
        for word in itertools.product((0,1,0x7f,0x80,0xff), repeat=length):
            if 0 in word:
                yield bytes(word), length % 4
    # All 255 concrete nonzero bytes; NUL is last allocated byte.
    for byte in range(1,256):
        for alignment in range(4):
            yield bytes((byte,0)), alignment
    for length in (0,1,2,3,7,31,255,1024):
        for alignment in range(4):
            data = bytes(1+(i*73)%255 for i in range(length))+b'\0'
            yield data, alignment
            yield data+b'\xff\x80tail', alignment


def evidence():
    cfg = json.loads(CFG.read_text(encoding='utf-8'))
    module = ROOT/cfg['extracted_arm9']
    raw = module.read_bytes()
    rom = (ROOT.parent/cfg['rom_name']).read_bytes()
    offset, _, base, _ = struct.unpack_from('<4I', rom, 0x20)
    assert rom[offset:offset+len(raw)] == raw
    assert sha(raw) == '6b072402634801228216df32197af888a03e7f1e344c988a75cfa293ce102a65'
    metadata = ROOT/cfg['metadata']
    # Pin all ten existing metadata files, independently rechecked against the
    # prior initialization evidence when this configuration was authored.
    baseline = cfg['metadata_sha256']
    assert len(baseline) == 10
    assert all(sha((ROOT/path).read_bytes()) == digest for path,digest in baseline.items())
    callers = []
    for file in sorted(metadata.rglob('relocs.txt')):
        for line in file.read_text(encoding='utf-8').splitlines():
            if re.search(r'to:0x0?2067f74\b', line):
                callers.append({'module': file.parent.name, 'entry': line})
    assert callers == [{'module':'arm9','entry':'from:0x020665d4 kind:arm_call to:0x02067f74 module:main'}]
    # Keep complete caller decode local; no original ROM bytes in public git.
    caller = decode(raw[0x665cc:0x66614], 0x020665cc)
    return {'callers':callers, 'caller_decode':caller, 'metadata_sha256':baseline}


def main():
    before = evidence()
    result = run(HERE/'nul_count.c', OUT, CFG)  # exactly one compilation/run
    report = json.loads((OUT/'result.json').read_text(encoding='utf-8'))
    if report['compile']['exit_code'] != 0:
        raise ValueError('compiler failed')
    original = decode(bytes.fromhex(report['reference_hex']), 0x02067f74)
    compiled = decode(bytes.fromhex(report['compiled_hex']), 0x02067f74)
    count = 0
    for data, alignment in cases():
        verify_case(original, compiled, data, alignment)
        count += 1
    assert evidence() == before
    details = {'finite_cases':count, 'scope':'return, ordered byte reads, stop, preserved registers, final NZCV',
               'limitations':'small decoded-operation model, not independent emulator or DS execution',
               'empty':verify_case(original,compiled,b'\0'),
               'high_bit_embedded_zero':verify_case(original,compiled,b'\xff\x80\0tail'),
               'evidence':before, 'diagnostic_exit':result}
    (OUT/'behavior.json').write_text(json.dumps(details,indent=2)+'\n',encoding='utf-8')
    print(f'BEHAVIOR PASS: {count} bounded cases; exact ordered reads; no writes; Gate0 OPEN')
    return 0  # A genuine byte mismatch is a completed diagnostic, not hidden.


if __name__ == '__main__':
    raise SystemExit(main())
