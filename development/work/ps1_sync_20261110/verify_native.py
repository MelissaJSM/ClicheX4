"""Run the unchanged PS1 HQ loader and native decoder with the new eye data."""
import importlib.util
import struct
import sys
from pathlib import Path
from sync import ROOT, D, source, read_disc, entry, psx_arc, sha, save, decode_stream
from src.psx_ui_atlas import tile_pixels, write_tile
from src.steam_player import unpack_indices
import unicorn as uc
from unicorn import mips_const as m

H = ROOT / 'work/hq_armor_20261109'
sys.path.insert(0, str(H))
spec = importlib.util.spec_from_file_location('hq_native_verifier', H / 'verify_cpu.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
fixture = D / 'native_fixture'
mode = 'ver_buki_riko'
names = ['SLUS_005.61', 'ST0D_0X.ARC', 'ST0D_0Z.ARC', 'COL0D_0X.ARC', 'COL0D_0Z.ARC']
_, parent = source(mode)
original, _ = read_disc(parent, names)
for folder in ['originals', 'prepared']:
    dst = fixture / mode / folder
    dst.mkdir(parents=True, exist_ok=True)
    for name, raw in original.items():
        if folder == 'prepared' and name == 'ST0D_0X.ARC':
            raw = (D / 'prepared' / name).read_bytes()
        (dst / name).write_bytes(raw)
mod.H = fixture
arc = (D / 'prepared/ST0D_0X.ARC').read_bytes()
assert entry(arc, 12) == entry(original['ST0D_0X.ARC'], 12)
container = entry(arc, 13)[96:]
exe = original['SLUS_005.61']
cache = {}
chunks = []
for i in range(struct.unpack_from('<I', container, 4)[0]):
    kind, start, off, size = struct.unpack_from('<4I', container, 16+i*16)
    packed = container[off:]
    machine = uc.Uc(uc.UC_ARCH_MIPS, uc.UC_MODE_MIPS32 | uc.UC_MODE_LITTLE_ENDIAN)
    machine.mem_map(0, 0x200000)
    machine.mem_write(0x10000, exe[2048:])
    machine.mem_write(0x180000, packed)
    machine.mem_write(0x190000, bytes([0xa5])*(size+32))
    machine.reg_write(m.UC_MIPS_REG_A0, 0x80180000)
    machine.reg_write(m.UC_MIPS_REG_A1, 0x80190010)
    machine.reg_write(m.UC_MIPS_REG_RA, mod.STOP)
    machine.emu_start(0x80016ff4, mod.STOP, count=2000000)
    expected = decode_stream(packed, 0, len(packed), size).data
    assert machine.reg_read(m.UC_MIPS_REG_PC) == mod.STOP
    assert bytes(machine.mem_read(0x190010, size)) == expected
    assert bytes(machine.mem_read(0x190000,16))+bytes(machine.mem_read(0x190010+size,16)) == bytes([0xa5])*32
    cache[off] = expected
    chunks.append((kind, start, expected))

states = next(raw for kind, start, raw in chunks if kind == 0)
dictionary = b''.join(raw for kind, start, raw in chunks if kind == 1)
static = bytearray(768*128)
static[:len(entry(arc, 0x10102))] = entry(arc, 0x10102)
for kind, start, raw in chunks:
    if kind == 2:
        static[start*128:start*128+len(raw)] = raw
cases = []
for special, armor in [(0,n) for n in range(16)] + [(1,0),(1,15),(255,15)]:
    result = mod.run(mode, special=special, armor=armor, decoder_cache=cache)
    state = 16+(armor != 0) if special else armor
    record = states[state*1412:(state+1)*1412]
    tiles = bytearray(176*128)
    for i, k in enumerate(struct.unpack('<176H', record[:352])):
        if k != 65535:
            write_tile(tiles, i, unpack_indices(dictionary[k*128:(k+1)*128]))
    expected = static + tiles
    for t in range(944):
        x = 384+t//176*64+t%16*4
        y = (t%176)//16*16
        raw = b''.join(result['vram'][(y+r)*2048+x*2:(y+r)*2048+x*2+8] for r in range(16))
        assert unpack_indices(raw) == tile_pixels(expected, t), (state,t)
    p = result['parts']
    off = struct.unpack_from('<I', p, 8)[0]
    assert p[off:off+1060] == record[352:]
    assert result['scheduler_preserved']
    cases.append({'special':special, 'armor':armor, 'state':state, 'texture_tiles':944})
protected = 0
for char in (0,1):
    for special in (0,1,255):
        for partner in ((1,255) if char==0 else (0,1,255)):
            old = mod.run(mode, True, char, special, partner=partner)
            new = mod.run(mode, False, char, special, partner=partner)
            assert not new['uploads'] and old['calls']==new['calls'] and old['palette']==new['palette']
            assert new['scheduler_preserved']
            protected += 1
live = mod.run(mode, special=1, armor=0, decoder_cache=cache, base=0x1b93c4, arena_tail=0x1a00, stack_top=0x801fef88)
assert live['scheduler_preserved']
save(D/'native_verification.json', {
    'passed':True, 'unicorn':uc.__version__, 'native_decoder_chunks':len(cache),
    'states':cases, 'protected_actor_cases':protected, 'all_944_tiles_match_each_state':True,
    'loader_and_executable_unchanged':True, 'task_tables_and_stack_guards_preserved':True,
    'prior_crash_layout_preserved':True, 'actual_gameplay_verified':False,
    'prepared_hq_sha256':sha(arc),
})
print('Native decoder',len(cache),'chunks; HQ',len(cases),'states;',protected,'protected actor cases: PASS',flush=True)
