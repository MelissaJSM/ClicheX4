"""Read original US hurt dispatch bytes and discover direct native callers."""
from pathlib import Path
import bisect
import hashlib
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

D = Path(__file__).parent
O = D / 'nana_hurt_triggers01'
O.mkdir(exist_ok=True)
assets, _ = read_disc(ROOT / 'MegaMan X4.bin', ('SLUS_005.61',))
exe = assets['SLUS_005.61']
base = struct.unpack_from('<I', exe, 24)[0]
at = lambda address, length: exe[address - base + 2048:address - base + 2048 + length]
symbols_path = ROOT / 'work/research/decomp/config/symbols.us.txt'
symbols = {}
for name, value in re.findall(r'^(\w+) = (0x[0-9a-fA-F]+);', symbols_path.read_text('utf8'), re.M):
    symbols.setdefault(int(value, 16), []).append(name)
addresses = sorted(symbols)
def owner(addr):
    start = addresses[bisect.bisect_right(addresses, addr) - 1]
    return {'symbol_start': hex(start), 'symbol_names': symbols[start], 'offset': addr - start}
cs = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
def decode(start, end):
    return [{'address': hex(i.address), 'bytes': i.bytes.hex(), 'mnemonic': i.mnemonic, 'operands': i.op_str}
            for i in cs.disasm(at(start, end - start), start)]
ranges = [
    ('contact_damage', 0x8002d9bc, 0x8002dd04),
    ('hurt_initializer', 0x80033d54, 0x80033ec0),
    ('hurt_dispatch_and_recovery', 0x80032b04, 0x80032de0),
    ('periodic_grab_damage', 0x80036470, 0x80036568),
    ('train_soldier_init', 0x80068548, 0x800688b8),
    ('train_soldier_main', 0x800688b8, 0x800689d0),
    ('main_object_allocator', 0x8002ab74, 0x8002ac50),
]
blocks = [{'name': name, 'start': hex(start), 'end': hex(end),
           'sha256': hashlib.sha256(at(start, end - start)).hexdigest(),
           'instructions': decode(start, end)} for name, start, end in ranges]
calls = {}
for target in (0x80036470, 0x8002d9bc):
    word = 0x0c000000 | ((target >> 2) & 0x3ffffff)
    found = []
    for addr in range(max(base, 0x80010000), 0x800f0000, 4):
        if struct.unpack('<I', at(addr, 4))[0] == word:
            found.append({'pc': hex(addr), **owner(addr), 'nearby': decode(addr - 24, addr + 12)})
    calls[hex(target)] = found
stores = []
for addr in range(max(base, 0x80010000), 0x800f0000, 4):
    word = struct.unpack('<I', at(addr, 4))[0]
    if word >> 26 == 0x28 and word & 0xffff == 0x62:
        stores.append({'pc': hex(addr), **owner(addr), 'nearby': decode(addr - 20, addr + 8)})
report = {'scope': '원US EXE 읽기·디스어셈블. 실행/게임조작 아님.',
          'exe_sha256': hashlib.sha256(exe).hexdigest(), 'load_address': hex(base),
          'hurt_animation_dispatch': list(at(0x800f8ad0, 5)),
          'hurt_invincibility': list(at(0x800f8b28, 5)),
          'blocks': blocks, 'direct_calls': calls, 'byte_stores_offset62': stores,
          'native_execution': False, 'game_modified': False}
stageptr = struct.unpack('<I', at(0x800f43c8 + 10 * 8, 4))[0]
stage = []
for i in range(62):
    row = struct.unpack('<BBBBhh', at(stageptr + i * 8, 8))
    flags, ident, subtype, typ, x, y = row
    if typ == 255:
        break
    item = {'index': i, 'address': hex(stageptr + i * 8), 'bytes': at(stageptr + i * 8, 8).hex(),
            'flags': flags, 'id': ident, 'subtype': subtype, 'object_type': typ, 'x': x, 'y': y}
    if typ == 0:
        entry = struct.unpack('<I', at(0x800f24a4 + ident * 4, 4))[0]
        item.update({'native_update': hex(entry), 'function': symbols.get(entry),
                     'initializer_head': decode(entry, entry + 220)})
    stage.append(item)
report['stage10_area0_records'] = stage
current_path = ROOT / 'out/ver_rin_nana/sprite_style_unification_20261107_v17/rin_nana.bin'
current_assets, _ = read_disc(current_path, ('SLUS_005.61',))
current = current_assets['SLUS_005.61']
assert struct.unpack_from('<I', current, 24)[0] == base
matched = []
for name, start, end in ranges:
    assert at(start, end-start) == current[start-base+2048:end-base+2048]
    matched.append(name)
for start, size in ((0x800f8ad0, 5), (0x800f8b28, 5),
                    (0x800f43c8 + 10*8, 8), (stageptr, len(stage)*8), (0x800f24a4, 77*4)):
    assert at(start, size) == current[start-base+2048:start-base+2048+size]
recordsource = ROOT / 'work/research/decomp/src/main/stage_object_records_10.c'
record_text = recordsource.read_text('utf8').split('stage_object_records_10_0[62] = {')[1].split('};')[0]
source_records = [tuple(int(x.strip(), 0) for x in row.split(','))
                  for row in re.findall(r'\{([^{}]+)\}', record_text)]
assert len(source_records) == 62
for i, row in enumerate(source_records):
    assert struct.pack('<BBBBhh', *row) == at(stageptr+i*8, 8)
report['RN17_unchanged_from_original_US'] = {
    'bin': current_path.relative_to(ROOT).as_posix(),
    'exe_sha256': hashlib.sha256(current).hexdigest(),
    'function_ranges_byte_exact': matched,
    'hurt_dispatch_and_timers_exact': True,
    'stage10_directory_records_and_main_dispatch_table_exact': True,
    'stage10_source_records_exact_to_original_EXE': 62,
}
(O / 'native_read.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'dispatch': report['hurt_animation_dispatch'],
                  'periodic_damage_callers': [{z: v for z, v in x.items() if z != 'nearby'} for x in calls['0x80036470']],
                  'contact_caller_count': len(calls['0x8002d9bc']), 'type_stores_count': len(stores),
                  'first_stage10_enemies': [{k: v for k, v in x.items() if k != 'initializer_head'} for x in stage if x['object_type'] == 0][:8]}, ensure_ascii=False, indent=2))
