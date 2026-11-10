"""X4 피격 대체 후보 조사. 게임·포인터·활성 상태를 수정하지 않는다."""
import gzip
import hashlib
import json
import math
import struct
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import numpy as np
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn import mips_const as m
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.overhaul_audio_verify_cpu import banks
from scripts.overhaul_nana_progress_refresh import loaded_vab_header
from src.psx_spu_audio import decode_spu

OUT = Path(__file__).resolve().parent
STATES = {
    'x': ('work/overhaul_20261105/audio/nana_user_progress_candidate04_final_v1/SLUS_005.61.000', '57977106f9bf2a8fae08834c94225fdcdf477d895e82256510e7a745f5259440'),
    'zero': ('work/overhaul_20261105/runtime/riko_chaser_fresh_state/SLUS_005.61.000', 'd392bf6b3d9421512b867985b3f0b44bd0958dc0d3f2a4eda7e1d33f4f2274d7'),
}
EXPECTED = {'ver_buki_riko': '15b6eec0ff23decff4f42133e20f0d0b33efed40c4ecf3f245905ef2a5357aea', 'ver_rin_nana': '8c5c7ba9bb2fd6d04080db453c2890c6446350fe19b896013661dc97b21b5bc1'}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def read_disc(path, names):
    with path.open('rb') as f:
        d = DiscReader(f, path.stat().st_size)
        rec = {r['name'].split(';')[0]: r for r in d.inspect()['files']}
        return {n: d.read(rec[n]['lba'], rec[n]['size']) for n in names}

def native_route(exe, weapon, result):
    u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0, 0x200000)
    load = struct.unpack_from('<I', exe, 24)[0] & 0x1fffffff
    u.mem_write(load, exe[2048:])
    obj = 0x1c0000
    u.mem_write(obj + 1, bytes([weapon]))
    u.reg_write(m.UC_MIPS_REG_A0, 0x80000000 | obj)
    u.reg_write(m.UC_MIPS_REG_A1, result & 0xffffffff)
    u.reg_write(m.UC_MIPS_REG_SP, 0x801ff000)
    found = []
    def hook(cpu, address, size, userdata):
        if address == 0x8001540c:
            found.append({'slot': cpu.reg_read(m.UC_MIPS_REG_A0), 'command': cpu.reg_read(m.UC_MIPS_REG_A1), 'call_return_address': hex(cpu.reg_read(m.UC_MIPS_REG_RA))})
            cpu.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x8002df7c, 0, count=20000)
    assert len(found) == 1
    return found[0]

def sdk(ram, loaded, slot, command):
    u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0, 0x200000)
    u.mem_map(0x1f801000, 0x1000)
    u.mem_write(0, ram)
    # A comparison-only route on the original hurt channel; no state file is written.
    source = loaded[slot][0][8 + command * 4:12 + command * 4]
    route = source[:3] + bytes([(source[3] & 0xe0) | 20])
    command_pointer = struct.unpack_from('<I', ram, 0x141f50 + 3 * 4)[0] & 0x1fffffff
    u.mem_write(command_pointer, route)
    u.reg_write(m.UC_MIPS_REG_A0, 3)
    u.reg_write(m.UC_MIPS_REG_A1, 0)
    u.reg_write(m.UC_MIPS_REG_A2, 0)
    u.reg_write(m.UC_MIPS_REG_SP, 0x801ff000)
    u.reg_write(m.UC_MIPS_REG_RA, 0x80008000)
    def hook(cpu, address, size, userdata):
        if address == 0x80008000:
            cpu.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x8001540c, 0, count=200000)
    assert u.reg_read(m.UC_MIPS_REG_PC) == 0x80008000 and u.reg_read(m.UC_MIPS_REG_V0) == 0
    regs = struct.unpack('<8H', u.mem_read(0x166d90 + 20 * 16, 16))
    assert regs[0] > 0 and regs[1] > 0 and regs[2] > 0
    return {'route_for_hurt_channel20': route.hex(), 'volume_left': regs[0], 'volume_right': regs[1], 'pitch': regs[2], 'start': regs[3], 'adsr1': regs[4], 'adsr2': regs[5], 'native_sdk_unmocked': True, 'real_game_playback': False}

def write_wav(path, pcm):
    with wave.open(str(path), 'wb') as f:
        f.setparams((1, 2, 44100, len(pcm), 'NONE', 'not compressed'))
        f.writeframes(np.asarray(pcm, dtype='<i2').tobytes())

def stats(x):
    y = np.asarray(x, dtype=np.float64)
    e = y * y
    total = float(e.sum())
    cumulative = np.cumsum(e) / max(1, total)
    fft = abs(np.fft.rfft(y * np.hanning(len(y)))) ** 2
    frequencies = np.fft.rfftfreq(len(y), 1 / 44100)
    spectral_total = max(1, float(fft.sum()))
    return {'seconds': len(y) / 44100, 'energy_90pct_seconds': int(np.searchsorted(cumulative, .90)) / 44100, 'rms_dbfs': float(20 * np.log10(max(1e-10, np.sqrt(np.mean(e)) / 32768))), 'peak_lsb': int(abs(y).max()), 'spectral_centroid_hz': float(np.sum(frequencies * fft) / spectral_total), 'energy_above_4000hz_ratio': float(fft[frequencies >= 4000].sum() / spectral_total), 'spectral_flatness': float(np.exp(np.mean(np.log(fft + 1e-12))) / max(1e-12, np.mean(fft))), 'human_listening_verified': False}

def main():
    names = ['PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC']
    inputs = {}
    current = {}
    for project, expected in EXPECTED.items():
        p = json.loads((ROOT / 'projects' / project / 'current_build.json').read_text(encoding='utf8'))
        path = ROOT / Path(p['cue']).with_suffix('.bin')
        assert p['sha256'] == expected and digest(path) == expected
        inputs[project] = {'bin': path.relative_to(ROOT).as_posix(), 'sha256': expected}
        current[project] = read_disc(path, names)
    original = ROOT / 'MegaMan X4.bin'
    assert digest(original) == '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
    exe = read_disc(original, ['SLUS_005.61'])['SLUS_005.61']
    routes = {'rejected_deflection': native_route(exe, 0, -1), 'x_buster_hit': native_route(exe, 0, 0), 'zero_hit': native_route(exe, 24, 0), 'zero_finishing_hit': native_route(exe, 24, 1)}
    assert [(r['slot'], r['command']) for r in routes.values()] == [(0, 6), (1, 12), (1, 9), (1, 10)]
    loaded = {k: banks(current['ver_rin_nana'][name]) for k, name in [('x', names[0]), ('zero', names[1])]}
    state_ram = {}
    for k, (path, expected) in STATES.items():
        data = (ROOT / path).read_bytes()
        assert sha(data) == expected
        state_ram[k] = gzip.decompress(data)[442:442 + 0x200000]
        for slot in (0, 1, 3):
            h, b, q = loaded[k][slot]
            start = struct.unpack_from('<I', state_ram[k], 0x141f30 + slot * 4)[0]
            pointer = struct.unpack_from('<I', state_ram[k], 0x141f50 + slot * 4)[0] & 0x1fffffff
            assert state_ram[k][pointer - 8:pointer - 8 + len(h)] == loaded_vab_header(h, b, start)
    cases = [('00_rejected_deflection', 'x', 0, 6, '원작 무효 타격/튕김음: 사용자 반려 비교 기준'), ('01_x_buster_hit', 'x', 1, 12, '원작 X 일반 탄환 적중음'), ('02_zero_hit', 'zero', 1, 9, '원작 제로 일반 명중음'), ('03_zero_finishing_hit', 'zero', 1, 10, '원작 제로 마무리 명중음: 긴 후보')]
    candidates = []
    reel = []
    for label, kind, slot, cmd, explanation in cases:
        h, b, q = loaded[kind][slot]
        c = h[8 + 4 * cmd:12 + 4 * cmd]
        program, tone = c[1] & 127, c[2] >> 4
        at = q['vab_offset'] + 32 + 2048 + (program * 16 + tone) * 32
        t = h[at:at + 32]
        w = q['waves'][struct.unpack_from('<H', t, 22)[0] - 1]
        encoded = b[w['body_offset']:w['body_offset'] + w['bytes']]
        values = sdk(state_ram[kind], loaded[kind], slot, cmd)
        decoded = decode_spu(encoded)
        # PCM preview uses measured native pitch. It is not a capture of SPU Gaussian interpolation, ADSR or reverb.
        rate = 44100 * values['pitch'] / 4096
        y = np.asarray(decoded.pcm, dtype=np.float64)
        pos = np.arange(math.ceil(len(y) * 4096 / values['pitch'])) * values['pitch'] / 4096
        pcm = np.rint(np.interp(pos, np.arange(len(y)), y)).astype(np.int16)
        write_wav(OUT / (label + '.wav'), pcm)
        (OUT / (label + '.adpcm')).write_bytes(encoded)
        (OUT / (label + '.tone')).write_bytes(t)
        reel.extend([pcm, np.zeros(44100, dtype=np.int16)])
        candidates.append({'id': label, 'label_ko': explanation, 'source': kind, 'slot': slot, 'command': cmd, 'command_hex': c.hex(), 'program': program, 'tone': tone, 'wave': w, 'tone_hex': t.hex(), 'native': values, 'effective_sample_rate': rate, 'decoded_end_flag': decoded.end_flag, 'pcm_statistics': stats(pcm), 'preview': (OUT / (label + '.wav')).relative_to(ROOT).as_posix(), 'adpcm_sha256': sha(encoded), 'listening_completed': False})
    write_wav(OUT / 'comparison_in_order.wav', np.concatenate(reel))
    capacity = []
    for project, assets in current.items():
        for name, arc in assets.items():
            h, b, q = banks(arc)[3]
            boss = q['waves'][-2:]
            prefix = boss[0]['body_offset']
            waves = q['waves'][:-2]
            assert all(not any(decode_spu(b[w['body_offset']:w['body_offset'] + w['bytes']]).pcm) for w in waves)
            capacity.append({'project': project, 'file': name, 'arc_sha256': sha(arc), 'voice_header_sha256': sha(h), 'voice_body_sha256': sha(b), 'body_bytes': len(b), 'original_silent_wave_sizes': [w['bytes'] for w in waves], 'silent_prefix_bytes': prefix, 'wave1_plus_wave2_bytes': waves[0]['bytes'] + waves[1]['bytes'], 'two_sfx_capacity_with_64byte_silent_reservations': prefix - (len(waves) - 2) * 64, 'boss_waves_preserve_exact': boss, 'boss_tones_preserve_exact': [h[q['vab_offset'] + 32 + 2048 + n * 32:q['vab_offset'] + 32 + 2048 + (n + 1) * 32].hex() for n in (14, 15)], 'all_original_voice_pcm_still_silent': True})
    report = {'scope': 'X4 조사 참고 후보. 최신 요청에 따라 실제 새 C01은 X5/X6 SE를 별도 선택한다.', 'inputs': inputs, 'native_hit_routing': routes, 'candidates': candidates, 'capacity': capacity, 'preview_limitations': ['Measured native pitch, but before SPU Gaussian interpolation/ADSR/reverb/voice gain.', 'No human listening, no real-time emulator input, no game or state or pointer output.'], 'all_source_states_preserved': all(sha((ROOT / p).read_bytes()) == s for p, s in STATES.values())}
    (OUT / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'candidates': [{k: c[k] for k in ('id', 'native', 'pcm_statistics')} for c in candidates], 'unified_two_sfx_capacity_bytes': min(r['two_sfx_capacity_with_64byte_silent_reservations'] for r in capacity), 'output': str(OUT)}, ensure_ascii=True))

if __name__ == '__main__':
    main()
