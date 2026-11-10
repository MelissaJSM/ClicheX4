"""Backport accepted Steam indexed art to authenticated PS1 copies only."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.prepare_riko_ui import entry
from scripts.inspect_steam_portraits import frames
from scripts.build_steam_selection import render_frame
from src.psx_player import decode_stream, composition_frame, bank_offsets, graphics_bank, indexed_atlas
from src.psx_compress import encode_stream
from src.psx_ui_atlas import write_tile, aliased_composition
from src.psx_ui_render import render_static_rgba
from src.psx_disc import file_hash, write_archive_copies
from src.psx_sector import validate_checks
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from src.steam_player import unpack_indices
from src.steam_portraits import tile, pack
from PIL import Image, ImageDraw

D = Path(__file__).parent
EYES = ROOT / 'work/shibuki_eyes_20261110'
W = ROOT / 'work/steam_port_20261109'
STEAM = Path(json.loads((W / 'backup_manifest.json').read_text('utf8'))['steam_root'])
EXPECTED = {
    'ver_buki_riko': '0d76b1e983275482e4aa5d56ebdaa4a7d6f01a571e8cea218337df9eb84ed46e',
    'ver_rin_nana': '03bb660be698dd7dd1b1b3fbf6612bcd1ed111cff47b5eda7c186ded3f343f3a',
}
INSTALLED = {r['relative_path']: r['installed_sha256'] for r in json.loads((W / 'install_state.json').read_text('utf8'))['files']}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, indent=2).encode('utf8') + b'\n'
    path.write_bytes(raw)


def source(mode):
    ptr = json.loads((ROOT / 'projects' / mode / 'current_build.json').read_text('utf8'))
    p = (ROOT / ptr['cue']).with_suffix('.bin')
    assert ptr['sha256'] == file_hash(p) == EXPECTED[mode]
    return ptr, p


def native(name, old=False):
    if old:
        return SteamArc((EYES / 'before' / name).read_bytes())
    rel = 'nativeDX10/X4/romPC/' + name
    raw = (STEAM / rel).read_bytes()
    assert sha(raw) == INSTALLED[rel], rel
    return SteamArc(raw)


def find(arc, magic, suffix='', folder=''):
    matches = [e for e in arc.entries if e.payload[:4] == magic and e.name.endswith(suffix) and folder in e.name]
    assert len(matches) == 1, (magic, suffix, folder, len(matches))
    return matches[0].payload


def packed(pixels):
    assert len(pixels) % 2 == 0 and max(pixels, default=0) <= 15
    return bytes(a | b << 4 for a, b in zip(pixels[::2], pixels[1::2]))


def replace_resource(arc, kind, data):
    e = next(e for e in psx_arc(arc) if int(e['type'], 16) == kind)
    assert len(data) == e['size']
    b = bytearray(arc)
    b[e['offset']:e['offset'] + e['size']] = data
    assert entry(b, kind) == data
    return bytes(b)


def reverse_pack(ps_pixels, ps_frames, old_tex, new_tex, pc_frames):
    """Inverse of the verified tile deduplication; reject shared-tile conflicts."""
    assert old_tex[:20] == new_tex[:20] and len(old_tex) == len(new_tex)
    converted, records = pack(old_tex, ps_frames, unpack_indices(ps_pixels))
    assert converted[8:] == old_tex[8:] and records == pc_frames, 'PS1 source/Steam before correspondence'
    modifications = {}
    for a, b in zip(ps_frames, pc_frames):
        for pa, pb in zip(struct.iter_unpack('<BBbb', a), struct.iter_unpack('<BBbb', b)):
            assert (pa[0] & ~3, pa[2:]) == (pb[0] & ~3, pb[2:])
            old_index = (pa[0] & 3) * 256 + pa[1]
            new_index = (pb[0] & 3) * 256 + pb[1]
            before, after = tile(old_tex[20:], new_index), tile(new_tex[20:], new_index)
            previous = modifications.setdefault(old_index, after)
            assert previous == after, ('Conflicting shared PS1 tile', old_index)
            assert tile(unpack_indices(ps_pixels), old_index) == before
    output = bytearray(ps_pixels)
    for index, pixels in modifications.items():
        write_tile(output, index, pixels)
    # Repack may deduplicate further after the edit: compare all referred pixels.
    for a, b in zip(ps_frames, pc_frames):
        for pa, pb in zip(struct.iter_unpack('<BBbb', a), struct.iter_unpack('<BBbb', b)):
            assert tile(unpack_indices(output), (pa[0] & 3) * 256 + pa[1]) == tile(new_tex[20:], (pb[0] & 3) * 256 + pb[1])
    return bytes(output)


def render_check(label, graphics, compositions, pc_tex, pc_records, palette, review):
    count = 0
    for n, (comp, rec) in enumerate(zip(compositions, pc_records)):
        expected = render_frame(pc_tex, rec, palette, 0)
        ps_image, bounds = render_static_rgba(graphics, comp, {i: struct.unpack_from('<16H', palette, i*32) for i in range(len(palette)//32)})
        assert ps_image.size == expected.size and ps_image.tobytes() == expected.tobytes(), (label, n)
        qs = list(struct.iter_unpack('<BBbb', rec))
        assert bounds == (min(q[2] for q in qs), min(q[3] for q in qs), max(q[2]+16 for q in qs), max(q[3]+16 for q in qs))
        ps_image.save(review / f'{label}_{n:02}.png')
        count += 1
    return count


def player_audit():
    result = []
    for mode, suffix in [('ver_rin_nana', ''), ('ver_buki_riko', '_eng')]:
        ptr, path = source(mode)
        raw, _ = read_disc(path, ['PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC'])
        for number in range(3):
            name = f'PL{number:02}_U.ARC'
            arc = native(f'pl{number:02}{suffix}.arc')
            g, p = entry(raw[name], 2), entry(raw[name], 3)
            pc_pat = pat_frames(find(arc, b'PAT\0', f'PL{number:02}'))
            ps_pat = frames(p)
            assert ps_pat == pc_pat, (mode, name, 'PAT')
            count = 0
            for bank in range(len(bank_offsets(g, allow_aliases=True))):
                suffix_name = f'pl{number:02}_{bank:03}'
                tex = find(arc, b'TEX\0', suffix_name)
                cof = find(arc, b'COF\0', suffix_name)
                cp = 17 + cof[16]
                offsets = struct.unpack_from('<256I', cof, cp+4)
                ff = graphics_bank(g, bank, allow_bank_aliases=True)['frames']
                for f in ff:
                    upload = decode_stream(g, f['offset'], f['limit'], f['tile_count']*128).data
                    pix, _, height = indexed_atlas(upload, f['tile_count'])
                    y = offsets[f['index']]
                    # Native charged Frost has an additional tile-base upload.
                    # It was restored to native COF in Steam; artwork remains PS1-identical.
                    if number in (0, 2) and bank == 3 and f['index'] >= 10:
                        y = 32
                    actual = tex[20+y*256:20+(y+height)*256]
                    assert actual == pix, (mode, name, bank, f['index'], height, y)
                    count += 1
            result.append({'mode': mode, 'player': number, 'atlas_references': count,
                           'pat_frames': sum(map(len, pc_pat)), 'all_player_art_and_parts_equal': True})
    save(D / 'player_audit.json', {'passed': True, 'checks': result, 'actual_gameplay_test': False})
    print('Player audit', result, flush=True)


def prepare():
    ptr, path = source('ver_buki_riko')
    with path.open('rb') as stream:
        reader = DiscReader(stream, path.stat().st_size)
        names = [r['name'].split(';')[0] for r in reader.inspect()['files'] if not r['directory'] and r['name'].split(';')[0].endswith('.ARC')]
    original, disc_records = read_disc(path, names)
    current = dict(original)
    review = D / 'review'
    review.mkdir(exist_ok=True)
    changed = {}
    checks = []

    def set_resource(name, kind, data):
        before = entry(current[name], kind)
        if data == before:
            return
        current[name] = replace_resource(current[name], kind, data)
        changed.setdefault(name, set()).add(kind)

    # Selection: exact indexed atlas correspondence, no layout conversion.
    name = 'ST0E_U1.ARC'
    old, new = native('st0e_01_eng.arc', True), native('st0e_01_eng.arc')
    oldtex, newtex = find(old, b'TEX\0', '_001'), find(new, b'TEX\0', '_001')
    start = struct.unpack_from('<I', entry(original[name], 12), 4)[0]
    end = struct.unpack_from('<I', entry(original[name], 12), 8)[0]
    g = bytearray(entry(original[name], 0x10102))
    count = (end-start)*2
    assert unpack_indices(g[start:end]) == oldtex[20:20+count]
    assert oldtex[20+count:] == newtex[20+count:]
    g[start:end] = packed(newtex[20:20+count])
    set_resource(name, 0x10102, bytes(g))
    pat = entry(original[name], 10)
    recs = pat_frames(find(new, b'PAT\0'))[1]
    palette = find(new, b'COL\0')[12+48*32:]
    # Use the palette row recorded during the approved native audit.
    rows = json.loads((EYES / 'records.json').read_text('utf8'))
    rr = next(r for r in rows if r['kind'] == 'select')
    palette = new.by_key[tuple(rr['palette_key'])].payload[12+rr['row']*32:]
    n = render_check('select', bytes(g[start:]), [composition_frame(pat, 1, i) for i in range(len(recs))], newtex, recs, palette, review)
    checks.append({'kind': 'select', 'frames': n})

    # Dialogue: normal/Force 8 plus 4 referenced Ultimate mouth frames.
    name = 'ST00_00.ARC'
    pat = entry(original[name], 10)
    start = struct.unpack_from('<I', entry(original[name], 12), 44)[0]
    end = struct.unpack_from('<I', entry(original[name], 12), 52)[0]
    oldg = entry(original[name], 0x10102)[start:end]
    private = struct.unpack_from('<I', pat, 44)[0] + 1376
    upat = struct.pack('<I', 4) + pat[private:]
    indices = [0, 1, 4, 5]
    ps_frames = frames(pat)[11] + [frames(upat)[0][i] for i in indices]
    old, new = native('st00_00_eng.arc', True), native('st00_00_eng.arc')
    rr = next(r for r in rows if r['kind'] == 'dialogue' and r['target'] == 'st00_00_eng.arc')
    texkey = tuple(rr['texture_key'])
    oldtex, newtex = old.by_key[texkey].payload, new.by_key[texkey].payload
    pc_frames = pat_frames(find(new, b'PAT\0'))[11]
    newg = reverse_pack(oldg, ps_frames, oldtex, newtex, pc_frames)
    dialogue_copies = []
    non_standard_arcs = []
    for target, raw in original.items():
        try:
            entries = psx_arc(raw)
        except ValueError:
            non_standard_arcs.append(target)
            continue
        for e in entries:
            kind = int(e['type'], 16)
            if kind >> 16 != 1:
                continue
            value = entry(current[target], kind)
            location = value.find(oldg)
            if location < 0:
                continue
            assert value.find(oldg, location+1) == -1
            set_resource(target, kind, value[:location] + newg + value[location+len(oldg):])
            dialogue_copies.append({'arc': target, 'kind': kind, 'offset': location})
    print('Dialogue identical copies', dialogue_copies, 'non-standard', non_standard_arcs, flush=True)
    assert any(r['arc'] == name for r in dialogue_copies)
    comps = [aliased_composition(pat, 11, i) for i in range(8)] + [composition_frame(upat, 0, i) for i in indices]
    palette = new.by_key[tuple(rr['palette_key'])].payload[12+rr['row']*32:]
    n = render_check('dialogue', newg, comps, newtex, pc_frames, palette, review)
    checks.append({'kind': 'dialogue', 'frames': n, 'copies': dialogue_copies, 'non_standard_arcs_not_searched': non_standard_arcs})

    # Other PS1 stages keep the same art after different amounts of NPC data.
    # Exact whole-atlas matching alone only finds ST00; use the verified prior
    # atlas inventory and prove each tile/part mapping against Steam before.
    prior = ROOT / 'work/armor_dialogue_20261108/ver_buki_riko'
    inv = json.loads((prior / 'audit.json').read_text('utf8'))['inventory']
    layout = json.loads((prior / 'prepared_v2/verification.json').read_text('utf8'))
    copies = []
    for item in layout['graphics']:
        target = item['file']
        if target == 'ST00_00.ARC':
            continue
        meta = next(q for q in inv['graphics'] if q['file'] == target)
        compinfo = next(q for q in layout['compositions'] if q['delta_tiles'] == item['delta_tiles'])
        pp = entry(original[compinfo['file']], 10)
        bank_id = compinfo['bank_indices'][0]
        local_up = struct.pack('<I', 4) + pp[struct.unpack_from('<I', pp, bank_id*4)[0]+1376:]
        fr = frames(pp)[bank_id] + [frames(local_up)[0][i] for i in indices]
        lo, hi = item['new_texture_base'], meta['offset']+meta['size']
        oldall = entry(original[target], meta['type'])
        local_new = reverse_pack(oldall[lo:hi], fr, oldtex, newtex, pc_frames)
        set_resource(target, meta['type'], oldall[:lo]+local_new+oldall[hi:])
        comps = [aliased_composition(pp, bank_id, i) for i in range(8)] + [composition_frame(local_up, 0, i) for i in indices]
        n = render_check('dialogue_'+target[:-4], local_new, comps, newtex, pc_frames, palette, review)
        copies.append({'arc': target, 'kind': meta['type'], 'offset': lo, 'frames': n, 'delta_tiles': item['delta_tiles']})
    assert len(copies) == 8
    checks.append({'kind': 'dialogue_stage_copies', 'frames': sum(q['frames'] for q in copies), 'copies': copies})

    # Pause: native shared cache has a separate PS1 atlas for base and Ultimate.
    old, new = native('pl00_eng.arc', True), native('pl00_eng.arc')
    oldtex, newtex = find(old, b'TEX\0', folder='\\wsel\\'), find(new, b'TEX\0', folder='\\wsel\\')
    for name, page, choices in [('PL00_U.ARC', 1, range(4)), ('PL02_U.ARC', 2, range(4, 6))]:
        oldg = entry(original[name], 0x10007)
        lo, hi = 20+page*65536, 20+(page+1)*65536
        assert unpack_indices(oldg) == oldtex[lo:hi]
        newg = packed(newtex[lo:hi])
        set_resource(name, 0x10007, newg)
        palettes = entry(original[name], 17)
        bank = palettes[1024:1536]
        count = 0
        for i in choices:
            rec = pat_frames(find(new, b'PAT\0', folder='\\wsel\\'))[0][38+i]
            n, off = struct.unpack_from('<HH', bank, i*4)
            assert bank[off*4:(off+n)*4] == rec
            local = bytearray(rec)
            for j in range(0, len(local), 4):
                index = 96 + (local[j] & 3)*256 + local[j+1]
                local[j] = (local[j] & ~3) | (index//256)
                local[j+1] = index % 256
            pp = struct.pack('<IHH', 4, n, 1) + bytes(local)
            rr = next(r for r in rows if r['kind'] == 'pause' and r['target'] == 'pl00_eng.arc' and r['frame'] == 38+i)
            pal = new.by_key[tuple(rr['palette_key'])].payload[12+rr['row']*32:]
            # Steam display also adds the same 96-tile virtual base.
            pc_local = bytes(local)
            count += render_check(f'pause_{i}', newg, [composition_frame(pp, 0, 0)], newtex[:20]+newtex[lo:hi], [pc_local], pal, review)
        checks.append({'kind': 'pause', 'source': name, 'frames': count})

    # Static title and weapon-get background illustration pages.
    for name, pcname in [('ST0E_U0.ARC', 'st0e_00_eng.arc'), ('ST0F_UX.ARC', 'st0f_0x_eng.arc'), ('ST0F_UZ.ARC', 'st0f_0z_eng.arc')]:
        old, new = native(pcname, True), native(pcname)
        oldtex, newtex = find(old, b'TEX\0', folder='\\dds\\'), find(new, b'TEX\0', folder='\\dds\\')
        oldg = entry(original[name], 0x10000)
        px = bytearray(unpack_indices(oldg))
        for y in range(len(px)//256):
            page, row = divmod(y, 256)
            pos = 20 + (page//8*256+row)*2048 + page%8*256
            assert px[y*256:(y+1)*256] == oldtex[pos:pos+256]
            px[y*256:(y+1)*256] = newtex[pos:pos+256]
        newg = packed(px)
        set_resource(name, 0x10000, newg)
        checks.append({'kind': 'background', 'source': name, 'indexed_bytes_changed': sum(a != b for a,b in zip(oldg,newg))})

    # HQ: preserve all state tables, parts, common backgrounds, and loader code.
    name = 'ST0D_0X.ARC'
    resource = entry(original[name], 13)
    blob = resource[96:]
    assert struct.unpack_from('<I', blob)[0] == 0x52415148
    chunks = []
    for i in range(struct.unpack_from('<I', blob, 4)[0]):
        kind, start, offset, size = struct.unpack_from('<4I', blob, 16+i*16)
        dec = decode_stream(blob, offset, len(blob), size)
        chunks.append((kind, start, dec.data, blob[offset:dec.end]))
    states = next(v for kind, start, v, _ in chunks if kind == 0)
    dictionary = b''.join(v for kind, start, v, _ in chunks if kind == 1)
    changes = {}
    for state in range(18):
        st = states[state*1412:(state+1)*1412]
        lut = struct.unpack('<176H', st[:352])
        atlas = bytearray(176*128)
        for index, k in enumerate(lut):
            if k != 65535:
                write_tile(atlas, index, unpack_indices(dictionary[k*128:(k+1)*128]))
        pp = struct.pack('<I', 4) + st[352:]
        fr = frames(pp)[0]
        pcname = 'cliche_br_st0d_0x.arc' if state == 0 else f'cliche_br_hqx_{state:02}.arc'
        old, new = native(pcname, True), native(pcname)
        oldtex, newtex = find(old, b'TEX\0', '_002'), find(new, b'TEX\0', '_002')
        pc_frames = pat_frames(find(new, b'PAT\0'))[2]
        newatlas = reverse_pack(bytes(atlas), fr, oldtex, newtex, pc_frames)
        for index, k in enumerate(lut):
            if k == 65535:
                continue
            px = tile(unpack_indices(newatlas), index)
            value = packed(px)
            prev = changes.setdefault(k, value)
            assert prev == value, ('HQ dictionary conflict', state, index, k)
        rr = next(r for r in rows if r['kind'] == 'hq' and r['target'] == pcname)
        palette = new.by_key[tuple(rr['palette_key'])].payload[12+35*32:]
        n = render_check(f'hq_{state:02}', newatlas, [composition_frame(pp, 0, f) for f in range(12)], newtex, pc_frames, palette, review)
        checks.append({'kind': 'hq', 'state': state, 'frames': n})
    newdict = bytearray(dictionary)
    for k, value in changes.items():
        newdict[k*128:(k+1)*128] = value
    directory = bytearray(16*len(chunks))
    payload = bytearray()
    chunk_checks = []
    for i, (kind, start, raw, encoded) in enumerate(chunks):
        updated = bytes(newdict[start*128:start*128+len(raw)]) if kind == 1 else raw
        if raw != updated:
            encoded = encode_stream(updated)
        assert decode_stream(encoded, 0, len(encoded), len(updated)).data == updated
        offset = 16 + len(directory) + len(payload)
        struct.pack_into('<4I', directory, i*16, kind, start, offset, len(raw))
        payload.extend(encoded)
        payload.extend(bytes((-len(payload)) % 4))
        chunk_checks.append({'kind': kind, 'start': start, 'changed': raw != updated, 'raw_size': len(raw), 'compressed_size': len(encoded)})
    newblob = blob[:16] + bytes(directory) + bytes(payload)
    assert len(newblob) <= len(blob), ('HQ capacity', len(newblob), len(blob))
    set_resource(name, 13, resource[:96] + newblob + bytes(len(blob)-len(newblob)))
    checks.append({'kind': 'hq_container', 'used': len(newblob), 'capacity': len(blob), 'chunks': chunk_checks})

    prepared = D / 'prepared'
    prepared.mkdir(exist_ok=True)
    for name, kinds in changed.items():
        before, after = original[name], current[name]
        layout_of = lambda value: [(e['type'], e['offset'], e['size']) for e in psx_arc(value)]
        assert len(before) == len(after) and layout_of(before) == layout_of(after)
        for e in psx_arc(before):
            kind = int(e['type'], 16)
            if kind not in kinds:
                assert entry(before, kind) == entry(after, kind), (name, kind)
        (prepared / name).write_bytes(after)
    report = {'passed': True, 'parent_sha256': ptr['sha256'], 'changed_arcs': {k: sorted(v) for k, v in changed.items()},
              'checks': checks, 'frames_compared': sum(r.get('frames', 0) for r in checks),
              'layout_palettes_timing_preserved': True, 'runtime_verified': False,
              'prepared_sha256': {n: sha(current[n]) for n in changed}}
    save(D / 'preparation.json', report)
    save(D / 'parent_pointer.json', ptr)
    print('Prepared', len(changed), 'archives;', report['frames_compared'], 'independent frames', flush=True)


if __name__ == '__main__':
    {'audit': player_audit, 'prepare': prepare}[sys.argv[1]]()
