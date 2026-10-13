"""Generate scalar/hash-only AU expectations; never open ROM, save or checkpoint bytes."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def content():
    paths = [ROOT/'docs/BrainAge_TaskAV_Result.json', ROOT/'docs/BrainAge_TaskAU_Result.json']
    av, au = [json.loads(path.read_text(encoding='utf-8-sig')) for path in paths]
    for path, expected, commit in zip(paths, [av, au],
            ['524acc6bead2768183e45ae4913b00ea811b274b', 'f17f95ae2b2a15f7fced6f04d82d2593350d37a4']):
        historical = subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{commit}:docs/{path.name}'])
        assert json.loads(historical.decode('utf-8-sig')) == expected, 'Authority report mismatch'
    assert av['au_stop'] == au['au_stop']
    expected = {'fields': {}, 'hashes': {}}

    def field(key, width, value):
        expected['fields'][key] = [width, value]

    for index, value in enumerate(av['au_stop']['r']):
        field(f'r{index}', 4, value)
    field('cpsr', 4, 31)
    for key, source in [('cycle9', 'cycle9'), ('cycle7', 'cycle7'),
                        ('ordinal9', 'insn9'), ('ordinal7', 'insn7')]:
        field(key, 8, av['au_stop_counters'][source])
    field('logical_saves', 8, 0)
    field('flash_commits', 8, 0)
    field('dtcm_stack_word', 4, 0x02067568)
    pcs = [int(text, 16) for text in av['AW']['pc_sequence']] + [0x020019B8]
    words = {int(row['pc'], 16): int(row['opcode'], 16) for row in av['code_facts']}
    for pc in pcs:
        field(f'code.{pc:08x}', 4, words[pc])
    for address in [0x020019AC, 0x020019E4]:
        field(f'literal.{address:08x}', 4, int(av['literals'][f'0x{address:08X}'], 16))
    for row in av['mapped_fields']:
        assert row['before'] == row['after']
        field(f'protected.{int(row["address"], 16):08x}', row['width'], row['after'])
    expected['hashes'].update(av['entry_images'])
    expected['hashes']['rom'] = av['rom_sha1']
    expected['hashes']['framework_commit'] = av['framework_baseline']
    manifest = {
        'schema': 'brainage-aw2-au-manifest-1',
        'authority': {'AW': '71f28f7ecc87388691c4c68589811d4322d05863',
                      'AV': '524acc6bead2768183e45ae4913b00ea811b274b',
                      'AU': av['authoritative_AU_commit']},
        'source_reports_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        'expected': expected,
        'unrecorded_au_entry_classes': [
            'slice-cap history, round target and fast-limit provenance',
            'CP15 and code/data timing latch values at AU stop',
            'divider operands, quotient/remainder, busy and inherited deadline',
            'periodic/peripheral service phase, DMA/timer/IRQ readiness and return stack'],
        'executable_AX_certificate': False,
    }
    header = '#pragma once\n#include "canonical.h"\nnamespace task_aw2 {\ninline Snapshot au_manifest() {\n    Snapshot expected;\n'
    for key, (width, value) in sorted(expected['fields'].items()):
        header += f'    expected.put("{key}",{width},{value}ULL);\n'
    for key, value in sorted(expected['hashes'].items()):
        header += f'    expected.hashes["{key}"]="{value}";\n'
    header += '    return expected;\n}\n}\n'
    return {'manifest.json': json.dumps(manifest, indent=2, sort_keys=True)+'\n', 'au_manifest.h': header}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    generated = content()
    if args.apply:
        patch = '*** Begin Patch\n'
        for name, text in generated.items():
            path = HERE/name
            assert not path.exists(), 'Manifest is immutable; compare instead of overwriting.'
            patch += f'*** Add File: {path.as_posix()}\n' + ''.join('+'+line+'\n' for line in text.splitlines())
        patch += '*** End Patch\n'
        binary = Path.home()/'AppData/Local/OpenAI/Codex/bin/9691020b546a15b2/codex.exe'
        subprocess.run([str(binary), '--codex-run-as-apply-patch', patch], check=True)
    else:
        for name, text in generated.items():
            assert (HERE/name).read_text(encoding='utf-8') == text, name
        print('Immutable AU scalar/hash manifest matches authoritative report metadata.')


if __name__ == '__main__':
    main()
