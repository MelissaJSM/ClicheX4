"""확인된 X6 비보컬 피격/사망을 X4의 폐기 음성 공간에 넣는 자원 제안만 생성한다."""
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.inventory_riko_voice import parse_bank
from scripts.overhaul_audio_verify_cpu import banks
from scripts.overhaul_nana_progress_refresh import loaded_vab_header
from src.psx_spu_audio import decode_spu, validate_oneshot_template
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn import mips_const as m

WORK = Path(__file__).resolve().parent
OUT = WORK / 'prepared'
NAMES = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC')
BASES = {
    'ver_buki_riko': ('shibuki_riko', '15b6eec0ff23decff4f42133e20f0d0b33efed40c4ecf3f245905ef2a5357aea'),
    'ver_rin_nana': ('rin_nana', '8c5c7ba9bb2fd6d04080db453c2890c6446350fe19b896013661dc97b21b5bc1'),
}
STATES = {
    'x': ('work/overhaul_20261105/audio/nana_user_progress_candidate04_final_v1/SLUS_005.61.000', '57977106f9bf2a8fae08834c94225fdcdf477d895e82256510e7a745f5259440'),
    'zero': ('work/overhaul_20261105/runtime/riko_chaser_fresh_state/SLUS_005.61.000', 'd392bf6b3d9421512b867985b3f0b44bd0958dc0d3f2a4eda7e1d33f4f2274d7'),
}
X6_SHA = 'e0b5e6b6349bb0f0f487234f52cda43f26754a3d67764b7c306ba75c01e76e1f'
HURT_SHA = '3849f73da2ec664732118255463da30fcd8438fc29ef37db4b0b18c1b8c51029'
DEATH_SHA = 'bca9ec5b6b47b1247ec483f6b95cb8de3d94c58e03132255c63df5f434e4cfbc'

def require(test, reason):
    if not test:
        raise ValueError(reason)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def read_disc(path):
    with path.open('rb') as f:
        d = DiscReader(f, path.stat().st_size)
        records = {r['name'].split(';')[0]: r for r in d.inspect()['files'] if r['name'].split(';')[0] in NAMES}
        require(set(records) == set(NAMES), 'Missing player ARC')
        return {n: d.read(r['lba'], r['size']) for n, r in records.items()}, records

def sound_entries(arc):
    entries = psx_arc(arc)
    for i, e in enumerate(entries[:-1]):
        h = arc[e['offset']:e['offset'] + e['size']]
        be = entries[i + 1]
        body = arc[be['offset']:be['offset'] + be['size']]
        try:
            q = parse_bank(h, body, False)
        except (ValueError, struct.error, IndexError):
            continue
        if q['slot'] == 3:
            return e, be, h, body, q
    raise ValueError('Missing player voice bank')

def mute(size):
    require(size >= 64 and size % 16 == 0, 'Unsafe silent sample reservation')
    x = bytearray(size)
    x[17], x[-31], x[-15] = 4, 1, 7
    result = bytes(x)
    validate_oneshot_template(result)
    require(not any(decode_spu(result).pcm), 'Nonzero mute')
    return result

def pack(arc, expected, samples):
    require(sha(arc) == expected, 'Unsupported ARC SHA')
    he, be, header, body, q = sound_entries(arc)
    require((q['program_count'], q['tone_count'], q['command_count']) == (1, 16, 13), 'Unsupported bank format')
    require(q['wave_count'] in (13, 14), 'Unexpected C06 wave count')
    require(header[8:16] == bytes.fromhex('8000601480006014') and header[56:60] == bytes.fromhex('80000014'), 'Already patched or unexpected source C01')
    waves = q['waves']
    sizes = [w['bytes'] for w in waves]
    require(sizes[:2] == [3040, 3040] and q['initial_padding_bytes'] == 0, 'Unexpected initial allocation')
    for w in waves[:-2]:
        raw = body[w['body_offset']:w['body_offset'] + w['bytes']]
        validate_oneshot_template(raw)
        require(not any(decode_spu(raw).pcm), 'Player voice is not silent')
    for kind, expected_sha in [('hurt', HURT_SHA), ('death', DEATH_SHA)]:
        require(sha(samples[kind]['raw']) == expected_sha, 'Wrong X6 sound')
        validate_oneshot_template(samples[kind]['raw'])
    old_sizes = sizes.copy()
    sizes[:2] = [len(samples['hurt']['raw']), len(samples['death']['raw'])]
    needed = sum(sizes) - sum(old_sizes)
    require(needed >= 0 and needed % 16 == 0, 'Unexpected packing delta')
    # Reclaim only the largest silent slots needed. Other original silent lengths stay intact.
    for i in sorted(range(2, len(waves) - 2), key=lambda i: sizes[i], reverse=True):
        take = min(needed, sizes[i] - 64)
        sizes[i] -= take
        needed -= take
        if not needed:
            break
    require(needed == 0 and sum(sizes) == len(body), 'Insufficient fixed SPU allocation')
    chunks = []
    for i, (w, size) in enumerate(zip(waves, sizes)):
        original = body[w['body_offset']:w['body_offset'] + w['bytes']]
        if i < 2:
            raw = samples['hurt' if i == 0 else 'death']['raw']
        elif size == w['bytes']:
            raw = original
        else:
            raw = mute(size)
        require(len(raw) == size, 'Wrong output wave size')
        chunks.append(raw)
    new_body = b''.join(chunks)
    h = bytearray(header)
    tb = q['vab_offset'] + 32 + 128 * 16
    for i, kind in enumerate(('hurt', 'death')):
        tone = bytearray(samples[kind]['tone'])
        require(struct.unpack_from('<HH', tone, 16) == (0x80ff, 0x1fc0), 'Unconfirmed X6 ADSR')
        # Program index/wave ID change; every timbre, pitch, volume and envelope byte stays identical.
        struct.pack_into('<HH', tone, 20, 0, i + 1)
        h[tb + i * 32:tb + (i + 1) * 32] = tone
    for command, tone in ((0, 0), (1, 0), (12, 1)):
        h[8 + command * 4:12 + command * 4] = bytes([0x83, 0, tone << 4, 20])
    for i, size in enumerate(sizes):
        struct.pack_into('<H', h, tb + 16 * 32 + (i + 1) * 2, size // 8)
    nq = parse_bank(bytes(h), new_body, False)
    require(h[tb + 2 * 32:tb + 16 * 32] == header[tb + 2 * 32:tb + 16 * 32], 'Unrelated tone changed')
    for key in ('slot', 'vab_offset', 'body_bytes', 'program_count', 'tone_count', 'wave_count', 'command_count'):
        require(nq[key] == q[key], 'Header metadata changed')
    require(nq['waves'][-2:] == waves[-2:], 'Peacock wave addresses/content changed')
    prefix = waves[-2]['body_offset']
    require(new_body[prefix:] == body[prefix:], 'Peacock raw payload changed')
    for c in range(2, 12):
        require(h[8 + c * 4:12 + c * 4] == header[8 + c * 4:12 + c * 4], 'Unrelated player command changed')
        cmd = h[8 + c * 4:12 + c * 4]
        if cmd[0] & 63 != 3:
            require(c == 10, 'Unexpected nonvoice command')
            continue
        t = cmd[2] >> 4
        wave_id = struct.unpack_from('<H', h, tb + t * 32 + 22)[0]
        require(not any(decode_spu(chunks[wave_id - 1]).pcm), 'Protagonist voice restored')
    result = bytearray(arc)
    result[he['offset']:he['offset'] + he['size']] = h
    result[be['offset']:be['offset'] + be['size']] = new_body
    result = bytes(result)
    layout = lambda a: [{k: v for k, v in e.items() if k != 'sha256'} for e in psx_arc(a)]
    require(len(result) == len(arc) and layout(result) == layout(arc), 'ARC layout changed')
    allowed = set(range(he['offset'], he['offset'] + he['size'])) | set(range(be['offset'], be['offset'] + be['size']))
    require(all(a == b or i in allowed for i, (a, b) in enumerate(zip(arc, result))), 'Unrelated asset changed')
    check = {'old_wave_sizes': old_sizes, 'new_wave_sizes': sizes, 'reclaimed_silent_bytes': sum(old_sizes[i] - sizes[i] for i in range(2, len(waves) - 2)), 'new_header_sha256': sha(h), 'new_body_sha256': sha(new_body), 'changed_bytes': sum(a != b for a, b in zip(arc, result)), 'player_commands_2_to_11_identical': True, 'tones_2_to_15_identical': True, 'Peacock_addresses_tones_raw_identical': True, 'other_sound_banks_and_assets_identical': True, 'all_unmodified_player_voice_commands_silent': True, 'original_X6_ADPCM_byte_exact': True, 'fixed_SPURAM_total': len(body), 'source_voice_timer_code_unmodified': True}
    return result, check

def native_sdk(ram, old, new):
    old_banks, new_banks = banks(old), banks(new)
    h, b, q = old_banks[3]
    start = struct.unpack_from('<I', ram, 0x141f30 + 12)[0]
    ptr = (struct.unpack_from('<I', ram, 0x141f50 + 12)[0] & 0x1fffffff) - 8
    require(ram[ptr:ptr + len(h)] == loaded_vab_header(h, b, start), 'Unknown input SDK cache')
    nh, nb, nq = new_banks[3]
    updated = bytearray(ram)
    updated[ptr:ptr + len(nh)] = loaded_vab_header(nh, nb, start)
    rows = []
    for command, kind, pitch in ((0, 'hurt', 1024), (1, 'hurt', 1024), (12, 'death', 1290)):
        u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
        u.mem_map(0, 0x200000)
        u.mem_map(0x1f801000, 0x1000)
        u.mem_write(0, bytes(updated))
        u.reg_write(m.UC_MIPS_REG_A0, 3)
        u.reg_write(m.UC_MIPS_REG_A1, command)
        u.reg_write(m.UC_MIPS_REG_A2, 0)
        u.reg_write(m.UC_MIPS_REG_SP, 0x801ff000)
        u.reg_write(m.UC_MIPS_REG_RA, 0x80008000)
        def hook(cpu, address, size, userdata):
            if address == 0x80008000:
                cpu.emu_stop()
        u.hook_add(UC_HOOK_CODE, hook)
        u.emu_start(0x8001540c, 0, count=200000)
        require(u.reg_read(m.UC_MIPS_REG_PC) == 0x80008000 and u.reg_read(m.UC_MIPS_REG_V0) == 0, 'Native SDK call failed')
        left, right, actual_pitch, wave_start, adsr1, adsr2, envelope, repeat = struct.unpack('<8H', u.mem_read(0x166d90 + 20 * 16, 16))
        w = nq['waves'][0 if kind == 'hurt' else 1]
        require(actual_pitch == pitch and (adsr1, adsr2) == (0x80ff, 0x1fc0), 'Native X4 pitch/ADSR differs from X6')
        require(wave_start == (start + w['body_offset']) // 8 and left > 0 and left == right, 'Wrong SDK start/gain')
        rows.append({'command': command, 'kind': kind, 'pitch': actual_pitch, 'ADSR1': adsr1, 'ADSR2': adsr2, 'start_register': wave_start, 'volume_left': left, 'volume_right': right, 'raw_sha256': w['sha256'], 'X6_native_pitch_matches': True, 'native_SDK_unmocked': True, 'scope': 'isolated CPU, transformed loaded VAB cache, no live state writes or real mixer capture'})
    return rows

def main():
    require(not OUT.exists(), 'Refuse overwriting a prepared proposal')
    require(digest(ROOT / 'MegaManX6.bin') == X6_SHA, 'Unsupported supplied X6 BIN')
    candidates = json.loads((WORK / 'x6/sound_candidates.json').read_text(encoding='utf8'))
    samples = {}
    for kind in ('hurt', 'death'):
        row = next(r for r in candidates if r['kind'] == kind and r['dat_index'] == 86)
        samples[kind] = {'raw': (WORK / 'x6' / row['raw']).read_bytes(), 'tone': bytes.fromhex(row['tone_hex']), 'source': row}
    state_ram = {}
    for key, (path, expected) in STATES.items():
        raw = (ROOT / path).read_bytes()
        require(sha(raw) == expected, 'Protected evidence state differs')
        state_ram[key] = gzip.decompress(raw)[442:442 + 0x200000]
    prepared = {}
    for project, (stem, expected) in BASES.items():
        source = ROOT / 'out' / project / 'selection_unified_20261105_v4' / (stem + '.bin')
        require(digest(source) == expected, 'Current baseline BIN differs')
        assets, records = read_disc(source)
        files, products = {}, {}
        for name, old in assets.items():
            new, proof = pack(old, sha(old), samples)
            require(pack(old, sha(old), samples)[0] == new, 'Non-reproducible preparation')
            refused = 0
            for bad, expected_sha in ((old, '0' * 64), (old[:-1], sha(old)), (new, sha(new))):
                try:
                    pack(bad, expected_sha, samples)
                except ValueError:
                    refused += 1
            require(refused == 3, 'Bad input accepted')
            proof['negative_inputs_rejected'] = refused
            proof['native_sdk'] = native_sdk(state_ram['zero' if name == 'PL01_U.ARC' else 'x'], old, new)
            path = OUT / project / name
            files[name] = {'path': path.relative_to(ROOT).as_posix(), 'before': sha(old), 'after': sha(new), 'size': len(new), 'record': records[name], 'validation': proof}
            products[name] = new
        prepared[project] = {'proposal': {'project': project, 'baseline': source.relative_to(ROOT).as_posix(), 'baseline_sha256': expected, 'files': files, 'source': {'bin': 'MegaManX6.bin', 'sha256': X6_SHA, 'sound_candidates': 'work/audio_c01_revision_20261105/x6/sound_candidates.json', 'hurt_sha256': HURT_SHA, 'death_sha256': DEATH_SHA}, 'real_runtime_verified': False, 'human_listening_verified': False}, 'products': products}
    # All cross-mode CPU/input/structure checks pass before any proposal ARC is published.
    for project, item in prepared.items():
        folder = OUT / project
        folder.mkdir(parents=True, exist_ok=False)
        for name, raw in item['products'].items():
            (folder / name).write_bytes(raw)
        (folder / 'proposal.json').write_text(json.dumps(item['proposal'], ensure_ascii=False, indent=2), encoding='utf8')
        require(all(sha((folder / n).read_bytes()) == item['proposal']['files'][n]['after'] for n in NAMES), 'Saved proposal mismatch')
    require(all(sha((ROOT / p).read_bytes()) == s for p, s in STATES.values()), 'Protected states changed')
    print(json.dumps({'output': str(OUT), 'projects': list(prepared), 'resources': 6, 'native_SDK_unmocked_cases': 18, 'all_passed': True, 'BIN_or_pointer_or_active_F1_written': False}))

if __name__ == '__main__':
    main()
