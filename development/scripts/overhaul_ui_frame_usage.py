"""미국판 등장/노바 프레임 사용 조건을 실제 EXE에서 읽기 전용으로 확인한다."""
import hashlib
import json
import struct
import sys
from pathlib import Path

import capstone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader

OUT = ROOT / 'work/overhaul_20261105/ui/c04_visual_review/frame_usage.json'
BUILDS = {
    'original': ('MegaMan X4.bin', '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'),
    'ver_buki_riko': ('out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin', '8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a'),
    'ver_rin_nana': ('out/ver_rin_nana/nana_ultimate_nova_20261104T185708218838Z/rin_nana.bin', '5dd089c181cd141955f8e98e3a6b028f24253f2ca4179ed34e194f6a276047f0'),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def off(address):
    return address - 0x80010000 + 2048

def main():
    cfg = json.loads((ROOT / 'config/shibuki_x_us.json').read_text('utf-8'))
    exes = {}
    for project, (relative, expected) in BUILDS.items():
        path = ROOT / relative
        with path.open('rb') as stream:
            h = hashlib.file_digest(stream, 'sha256').hexdigest()
            if h != expected:
                raise ValueError('Unsupported input BIN')
            stream.seek(0)
            exes[project] = DiscReader(stream, path.stat().st_size).read(cfg['executable']['lba'], cfg['executable']['size'])
    exe = exes['original']
    assert sha(exe) == cfg['executable']['sha256']
    cs = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
    regions = {
        'beam_in': (0x80031410, 0x80031540),
        'nova_entry': (0x800375B4, 0x8003770C),
        'nova_animation': (0x80038ECC, 0x80039130),
    }
    code = {}
    for name, (start, end) in regions.items():
        data = exe[off(start):off(end)]
        assert all(e[off(start):off(end)] == data for e in exes.values())
        code[name] = {'start':hex(start), 'end':hex(end), 'sha256':sha(data),
            'same_in_both_baselines':True,
            'instructions':[f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in cs.disasm(data, start)]}
    animations = {}
    for n in (2, 106):
        address = struct.unpack_from('<I', exe, off(cfg['animation_table_address']) + 4*n)[0]
        position, seen, rows = 0, set(), []
        while position not in seen:
            seen.add(position)
            data = exe[off(address)+position*4:off(address)+position*4+4]
            assert all(e[off(address)+position*4:off(address)+position*4+4] == data for e in exes.values())
            ticks, event, relative, frame = struct.unpack('<bbbB',data)
            rows.append({'position':position,'ticks':ticks,'event':event,'relative':relative,'frame':frame})
            position += relative
        animations[str(n)] = {'address':hex(address),'steps':rows,'same_in_both_baselines':True}
    assert [(r['frame'],r['event']) for r in animations['2']['steps'] if r['event']] == [(140,1)]
    assert set(r['frame'] for r in animations['106']['steps']) == set(range(213,221))
    expected = {0x800314D8:0x82020045, 0x800314F8:0xA20200A7,
                0x800375D4:0x920200A7, 0x800375DC:0x30420002,
                0x80037650:0x2405006A}
    for address, word in expected.items():
        assert struct.unpack_from('<I',exe,off(address))[0] == word
    report = {
        'sources':{k:{'path':v[0],'bin_sha256':v[1],'exe_sha256':sha(exes[k])} for k,v in BUILDS.items()},
        'capstone_version':capstone.__version__, 'code':code, 'animations':animations,
        'findings':[
            'X animation2 is normal arrival. Frame140 event1 restores saved armor_parts and arm_type; frames133..139 precede that restoration.',
            'PL02 basic-layer arrival body must therefore use the capsule-before costume; full-armor overlay previews are not a faithful simulation of the pre-event steps.',
            'X animation106 uses frames213..220. Actual US nova entry checks armor_parts bit2 and energy48, not the Ultimate flag.',
            'Fourth/body-part forms can use213..220. They must NOT be excluded as Ultimate-only. Armorless basic/pre-capsule forms fail the bit2 test.',
            'The Ultimate engine byte at0x801721F7 controls energy consumption in nova entry; its absence does not block initial nova entry.',
        ],
        'limitations':['Read-only static US machine-code/animation inspection; no runtime input or state mutation.',
            'Arrival body/overlay rendering must be checked at each animation event, not inferred from a composite sheet with all four armor layers always enabled.'],
        'runtime_verified':False,
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'output':str(OUT),'arrival_event_frame':140,'nova_frames':list(range(213,221))}))

if __name__ == '__main__':
    main()
