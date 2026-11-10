"""최신 두 BIN의 프레임 범위·애니메이션·대기 기준을 읽기 전용으로 고정한다.

전체 아트 시각 판정/게임 실행 검사가 아니다. 결과는 전용 coverage 폴더에만 쓴다.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from src.psx_player import bank_offsets, graphics_bank, decode_stream, composition_frame, compose_indices

OUT = ROOT / 'work/sprite_consistency_20261105/coverage'
EXPECTED = {
    'ver_buki_riko': ('shibuki_riko', 'bedba81a4c1263388835e10f57a8e30f6b7e9d9ac6f3f3d3dbf77821f4fb7c08'),
    'ver_rin_nana': ('rin_nana', 'b15be8bf18921f06c8e6713c0bdc51a22374764c7d59ec7fca29df97f2e742c1'),
}
US_SHA = '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
X_PLACEHOLDERS = {105, *range(175, 183)}
X_GROUPS = {
    'idle': [0, *range(115, 120)], 'run_and_shot': list(range(1, 33)),
    'air_and_shot': list(range(33, 55)), 'wall_and_shot': list(range(55, 67)),
    'dash_and_shot': list(range(67, 85)), 'standing_shot_charge': [85, 86, 87, 88, 89, 90, 91, 92],
    'special_weapon_poses': list(range(93, 105)), 'hurt': list(range(106, 115)) + list(range(233, 237)),
    'low_hp': list(range(120, 126)), 'arrival': list(range(126, 143)),
    'ladder': list(range(143, 157)), 'transfer_out': list(range(157, 162)) + list(range(208, 213)),
    'ride_chaser': list(range(162, 175)), 'ride_armor': list(range(184, 204)),
    'victory': list(range(204, 208)), 'nova_and_hover': list(range(213, 231)),
    'other_valid_refs_require_context': [183, 231, 232],
}


def sha(b): return hashlib.sha256(b).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf8')


def read_assets(path, names):
    with path.open('rb') as f:
        d = DiscReader(f, path.stat().st_size)
        rr = {r['name'].split(';')[0]: r for r in d.inspect()['files']}
        return {n: d.read(rr[n]['lba'], rr[n]['size']) for n in names}, {n: rr[n] for n in names}


def unique_entry(arc, typ):
    ee = [e for e in psx_arc(arc) if int(e['type'], 16) == typ]
    assert len(ee) == 1
    e = ee[0]
    return arc[e['offset']:e['offset'] + e['size']]


def exe_slice(exe, address, size):
    base = struct.unpack_from('<I', exe, 0x18)[0]
    pos = 2048 + address - base
    if pos < 2048 or pos + size > len(exe):
        raise ValueError('Executable bounds')
    return exe[pos:pos + size]


def source_callers():
    result = {}
    folder = ROOT / 'work/research/decomp/src/main'
    # Labels are source-call evidence only: dynamic IDs and conditional control
    # flow require actual runtime, not a regex proof of reachability.
    for path in folder.glob('player*.c'):
        fn = None
        lines = path.read_text('utf8').splitlines()
        for i, line in enumerate(lines, 1):
            match = re.match(r'^(?:void|s32|u32|s16|s8)\s+(\w+)\([^;]*\)\s*$', line)
            if match:
                fn = match.group(1)
            for call in re.finditer(r'player_set_animation(?:_frame)?\([^,]+,\s*(0x[\da-fA-F]+|\d+)\s*[,)]', line):
                aid = int(call.group(1), 0)
                result.setdefault(aid, []).append({'file': path.relative_to(ROOT).as_posix(), 'line': i,
                                                  'function': fn, 'source': line.strip()})
    return result


def animations(exe, original, family, callers):
    base = 0x80119DF0 if family == 'x' else 0x8011AFF0
    selector = [0] * 144 if family == 'x' else list(exe_slice(exe, 0x8011AF60, 144))
    if family == 'zero':
        assert bytes(selector) == exe_slice(original, 0x8011AF60, 144)
    table = exe_slice(exe, base, 144 * 4)
    assert table == exe_slice(original, base, 144 * 4)
    rows, reverse = [], {}
    for aid, address in enumerate(struct.unpack('<144I', table)):
        pos = 0
        visited = set()
        steps = []
        while pos not in visited:
            if not 0 <= pos < 512:
                raise ValueError('Unexpected animation traversal')
            visited.add(pos)
            raw = exe_slice(exe, address + pos * 4, 4)
            assert raw == exe_slice(original, address + pos * 4, 4)
            duration, event, stride, frame = struct.unpack('<bbbB', raw)
            # Native decrements the signed byte, wraps modulo256, then compares0.
            # Duration0 is256 calls if the gameplay state does not intervene.
            ticks = duration & 255 or 256
            steps.append({'position': pos, 'address': hex(address + pos * 4), 'bytes': raw.hex(),
                          'duration_signed': duration, 'duration_calls_uninterrupted': ticks,
                          'event_signed': event, 'event_bits': event & 255, 'relative_step': stride,
                          'frame': frame})
            gb = 0 if selector[aid] == 0 else 1
            reverse.setdefault(f'{gb}:{frame}', []).append({'animation': aid, 'position': pos})
            pos += stride
        rows.append({'id': aid, 'address': hex(address), 'graphics_bank': 0 if selector[aid] == 0 else 1,
                     'composition_bank': 0 if selector[aid] == 0 else 5, 'steps': steps,
                     'loop_to_position': pos, 'sequence_call_ticks': sum(q['duration_calls_uninterrupted'] for q in steps),
                     'has_event_or_terminal': any(q['event_bits'] or not q['relative_step'] for q in steps),
                     'unfiltered_source_callers': callers.get(aid, []), 'runtime_verified_in_this_audit': False})
    return {'table_address': hex(base), 'count': len(rows), 'unique_sequence_addresses': len({q['address'] for q in rows}),
            'all_table_and_reachable_step_bytes_identical_to_original': True, 'animations': rows,
            'frame_to_animation': reverse, 'limitations': [
                'Relative-step traversal is an uninterrupted preview model, not full gameplay control flow.',
                'Gameplay may consume event bits, choose another animation or start at a nonzero sequence position.',
                'Ticks count animate_object calls. Mapping to60Hz is only a preview assumption.',
                'An animation-table entry existing does not prove reachability in gameplay.',
                'Source callers combine X and Zero branches; shared numeric IDs do not mean the same action.']}


def extra_sequences(exe, original):
    result = {}
    for address, count, label in [(0x8011BF40, 54, 'shared_effect_capsule'), (0x8011C018, 22, 'zero_effects')]:
        data = exe_slice(exe, address, count * 4)
        assert data == exe_slice(original, address, count * 4)
        rows = []
        for aid, ptr in enumerate(struct.unpack('<' + 'I' * count, data)):
            pos, seen, steps = 0, set(), []
            while pos not in seen:
                assert -512 < pos < 512 and len(seen) < 512
                seen.add(pos)
                raw = exe_slice(exe, ptr + pos * 4, 4)
                assert raw == exe_slice(original, ptr + pos * 4, 4)
                dur, ev, stride, frame = struct.unpack('<bbbB', raw)
                steps.append(dict(position=pos, duration_signed=dur, duration_calls_uninterrupted=(dur & 255) or 256,
                                  event_bits=ev & 255, relative_step=stride, frame=frame))
                pos += stride
            rows.append(dict(id=aid, address=hex(ptr), steps=steps, loop_to_position=pos))
        result[label] = dict(table=hex(address), count=count, animations=rows,
                             resource_binding='Object constructor selects graphics/composition bank; frame alone is ambiguous.',
                             original_bytes_preserved=True)
    return result


def reference_inventory(project, idles):
    first = project == 'ver_buki_riko'
    refs = {
        'zero_normal': (
            'work/ver_buki_riko/art_pilot/scale_consistency/walk_design_basis/idle_147.png' if first else 'work/ver_rin_nana/idle_style/v2/preview_147.png',
            'docs/RIKO_SCALE_STANDARD.md' if first else 'docs/RIN_STYLE_UNIFICATION.md'),
        'x_base': (
            'work/ver_buki_riko/shibuki_art/idle_chubby_v2/candidate09/shibuki_idle000_indexed.png' if first else 'out/ver_rin_nana/nana_pilot_v9/nana_000_indexed.png',
            'docs/SHIBUKI_SPRITES.md' if first else 'docs/NANA_ART_DIRECTION.md'),
        'x_fourth_full': (
            'work/ver_buki_riko/shibuki_art/fourth_armor_v1/layers03/frame_000_mask15.png' if first else 'work/ver_rin_nana/nana_fourth_armor/idle_v6/frame_000_mask15.png',
            'docs/SHIBUKI_FOURTH_ARMOR.md' if first else 'docs/NANA_FOURTH_ARMOR.md'),
        'ultimate_before_jacket': (
            'work/ver_buki_riko/shibuki_art/ultimate_v1/pilot01/ultimate_000.png' if first else 'work/ver_rin_nana/nana_ultimate_armor/start_v2/ultimate_000.png',
            'docs/SHIBUKI_ULTIMATE_ARMOR.md' if first else 'docs/NANA_ULTIMATE_ARMOR.md'),
        'ultimate_after_swim': (
            'work/overhaul_20261105/sprites/c03_final_v1/' + project + '/proposal.json',
            'docs/OVERHAUL_SPRITES.md'),
    }
    rows = {}
    for role, (path, evidence) in refs.items():
        p = ROOT / path
        r = dict(path=path, exists=p.exists(), source_document=evidence,
                 current_idle=idles[role]['path'], current_roles_follow_latest_swap=True)
        if p.exists():
            r['sha256'] = file_sha(p)
            if p.suffix.lower() == '.png':
                a = Image.open(p).convert('RGBA'); b = Image.open(ROOT / idles[role]['path']).convert('RGBA')
                aa = np.asarray(a.crop(a.getbbox())).copy(); bb = np.asarray(b.crop(b.getbbox())).copy()
                # Compare 5-bit colors; old PNG display expansion may use other8-bit rounding.
                aa[:, :, :3] >>= 3; bb[:, :, :3] >>= 3
                aa[aa[:, :, 3] == 0] = 0; bb[bb[:, :, 3] == 0] = 0
                r['reference_png_size'] = list(a.size)
                r['tight_rgba555_same_shape'] = aa.shape == bb.shape
                r['tight_rgba555_equal'] = bool(aa.shape == bb.shape and np.array_equal(aa, bb))
                r['comparison_scope'] = 'Tight silhouette/color match only; world origin must come from actual compositions.'
                if not first and role == 'x_fourth_full':
                    current = np.asarray(b.crop((80, 80, 240, 240))).copy()
                    old = np.asarray(a).copy()
                    old[:, :, :3] >>= 3; current[:, :, :3] >>= 3
                    old[old[:, :, 3] == 0] = 0; current[current[:, :, 3] == 0] = 0
                    diff = np.any(old != current, axis=2)
                    yy, xx = np.where(diff)
                    r['later_accepted_delta'] = {
                        'changed_pixels': len(xx), 'world_positions': [[int(x-80), int(y-80)] for x,y in zip(xx,yy)],
                        'evidence': 'docs/NANA_FOURTH_MOVEMENT.md:21',
                        'meaning': 'Later user-accepted removal of blinking yellow veil speck; preserve current idle, do not roll back.'}
                    assert len(xx) == 1 and [int(xx[0]-80), int(yy[0]-80)] == [6,-18]
        rows[role] = r
    return rows


def focused_regressions(assets, original):
    arrival = []
    for name in ('PL00_U.ARC', 'PL02_U.ARC'):
        for layers in ([0], [0,8,5,7,6]):
            first = idle_image(assets[name], 0, layers)
            last = idle_image(assets[name], 142, layers)
            different = np.any(np.asarray(first) != np.asarray(last), axis=2)
            yy, xx = np.where(different)
            arrival.append({'archive': name, 'layers': layers,
                            'ready142_equals_idle0_rgba': first.tobytes() == last.tobytes(),
                            'changed_pixels': len(xx),
                            'changed_bbox_world': [int(xx.min()-160), int(yy.min()-160), int(xx.max()+1-160), int(yy.max()+1-160)] if len(xx) else None,
                            'interpretation': 'Difference is a review candidate, not by itself a quality defect.'})
    partial = []
    g0, c0 = [unique_entry(original['PL01_U.ARC'], t) for t in (2,3)]
    g, c = [unique_entry(assets['PL01_U.ARC'], t) for t in (2,3)]
    source = graphics_bank(g0,1,allow_bank_aliases=True)['frames']
    current = graphics_bank(g,1,allow_bank_aliases=True)['frames']
    for n in range(42,50):
        f0, f = source[n], current[n]
        a = decode_stream(g0,f0['offset'],f0['limit'],f0['tile_count']*128).data
        b = decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        def records(cc):
            return [(q['flags'],q['tile'],q['x'],q['y']) for q in composition_frame(cc,5,n)['parts']]
        assert a == b and records(c0) == records(c) and f['tile_count'] == 1
        partial.append({'frame': n, 'raw_sha256':sha(b), 'tile_count':1,
                        'max_composition_tile':max(q['tile'] for q in composition_frame(c,5,n)['parts']),
                        'raw_and_composition_identical_to_original':True})
    return {'x_ready_to_idle':arrival,'zero_partial_uploads':partial,
            'scope':'Pixel equality on known idle transition and raw/composition preservation only; no broad artwork judgement.'}


def archive_inventory(arc, family, anim):
    g, c, p = [unique_entry(arc, t) for t in (2, 3, 9)]
    banks, streams = [], {}
    for bi in range(len(bank_offsets(g, allow_aliases=True))):
        bank = graphics_bank(g, bi, allow_bank_aliases=True)
        fs = []
        for f in bank['frames']:
            raw = decode_stream(g, f['offset'], f['limit'], f['tile_count'] * 128)
            streams.setdefault(str(f['offset']), []).append([bi, f['index']])
            row = {**f, 'raw_sha256': sha(raw.data), 'compressed_size': raw.end - raw.start,
                   'animation_references': anim['frame_to_animation'].get(f'{bi}:{f["index"]}', [])}
            cb = bi * 5 if family == 'zero' and bi < 2 else 0 if family == 'x' and bi == 0 else None
            if cb is not None:
                comp = composition_frame(c, cb, f['index'])
                row['composition_bank'] = cb
                row['parts_count'] = len(comp['parts'])
                row['cluts'] = sorted({r['clut'] for r in comp['parts']})
                row['texture_pages'] = sorted({r['page'] for r in comp['parts']})
                row['max_composition_tile'] = max((r['tile'] + r['page'] * 256 for r in comp['parts']), default=-1)
                try:
                    pix, size, bounds, _ = compose_indices(raw.data, f['tile_count'], comp, allowed_cluts={0, 1, 2, 3})
                    row['standalone_structure'] = 'empty_parts' if not comp['parts'] else 'composable'
                except ValueError as error:
                    row['standalone_structure'] = 'not_composable'
                    row['reason'] = str(error)
            fs.append(row)
        banks.append({'bank': bi, 'base': bank['base'], 'end': bank['end'], 'count': len(fs),
                      'max_tile_count': max(r['tile_count'] for r in fs), 'frames': fs})
    comps = [{'bank': i, 'offset': off, 'frame_count': composition_frame(c, i, 0)['bank_frame_count']}
             for i, off in enumerate(bank_offsets(c))]
    return {'sha256': sha(arc), 'graphics_sha256': sha(g), 'composition_sha256': sha(c), 'palette_sha256': sha(p),
            'graphics_banks': banks, 'composition_banks': comps, 'stream_sharing': streams,
            'graphics_reference_count': sum(b['count'] for b in banks), 'unique_compressed_streams': len(streams),
            'all_streams_decoded': True, 'full_visual_audit_performed': False}


def idle_image(arc, frame, layers, black=False):
    g, c, p = [unique_entry(arc, t) for t in (2, 3, 9)]
    f = graphics_bank(g, 0, allow_bank_aliases=True)['frames'][frame]
    packed = decode_stream(g, f['offset'], f['limit'], f['tile_count'] * 128).data
    result = Image.new('RGBA', (384, 384))
    for cb in layers:
        comp = composition_frame(c, cb, frame)
        if cb:
            comp = {**comp, 'parts': [{**q, 'clut': 0} for q in comp['parts']]}
        pixels, size, bounds, _ = compose_indices(packed, f['tile_count'], comp, allowed_cluts={0, 1, 2, 3})
        if not comp['parts']:
            continue
        words = list(struct.unpack_from('<64H', p)) if not cb else list(struct.unpack_from('<16H', p, 64 if cb == 7 else 32))
        if black:
            words[:16] = struct.unpack_from('<16H', p, 13 * 32)
        colors = np.array([[(w >> s & 31) * 255 // 31 for s in (0, 5, 10)] + [0 if i % 16 == 0 else 255]
                           for i, w in enumerate(words)], np.uint8)
        small = Image.fromarray(colors[np.frombuffer(pixels, np.uint8).reshape(size[1], size[0])])
        result.alpha_composite(small, (160 + bounds[0], 160 + bounds[1]))
    return result


def timer_cpu(exe):
    spec = importlib.util.spec_from_file_location('coverage_cpu', ROOT / 'work/ultimate_costume_swap_20261105/audit/native_contracts.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    from unicorn import mips_const as m
    rows = []
    for duration in (1, 2, 127, 0, -1):
        u = helper.cpu(exe)
        obj, seq = 0x8000, 0x9000
        current = struct.pack('<bbbB', duration, 0, 1, 7)
        following = struct.pack('<bbbB', 5, 0, 0, 9)
        u.mem_write(seq, current + following)
        u.mem_write(obj + 0x34, struct.pack('<I', 0x80000000 + seq))
        u.mem_write(obj + 0x44, current)
        wanted = duration & 255 or 256
        for tick in range(1, wanted + 1):
            u.reg_write(m.UC_MIPS_REG_A0, 0x80000000 + obj)
            u.reg_write(m.UC_MIPS_REG_RA, helper.RETURN)
            helper.finish(u, 0x80015DC8)
            actual = struct.unpack('<I', u.mem_read(obj + 0x34, 4))[0]
            assert actual == 0x80000000 + seq + (4 if tick == wanted else 0)
        assert bytes(u.mem_read(obj + 0x44, 4)) == following
        rows.append({'duration_signed': duration, 'actual_native_advance_after_calls': wanted})
    return {'native_function': '0x80015DC8', 'cases': rows, 'passed': True,
            'scope': 'Actual current EXE MIPS in isolated Unicorn RAM; no emulator/game-state changes.'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original_path = ROOT / 'MegaMan X4.bin'
    assert file_sha(original_path) == US_SHA
    names = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC', 'SLUS_005.61')
    original, _ = read_assets(original_path, names)
    callers = source_callers()
    reports = {}
    for project, (stem, expected) in EXPECTED.items():
        path = ROOT / 'out' / project / 'ultimate_costumes_swapped_20261105_v1' / (stem + '.bin')
        assert file_sha(path) == expected
        assets, records = read_assets(path, names)
        target = OUT / project
        target.mkdir(exist_ok=True)
        anims = {family: animations(assets['SLUS_005.61'], original['SLUS_005.61'], family, callers) for family in ('x', 'zero')}
        for family, data in anims.items():
            write(target / (family + '_animations.json'), data)
        write(target / 'effect_animations.json', extra_sequences(assets['SLUS_005.61'], original['SLUS_005.61']))
        arcs = {}
        for name in names[:3]:
            family = 'zero' if name.startswith('PL01') else 'x'
            data = archive_inventory(assets[name], family, anims[family])
            write(target / (name + '.inventory.json'), data)
            arcs[name] = {k: v for k, v in data.items() if k not in ('graphics_banks', 'composition_banks', 'stream_sharing')}
            arcs[name]['record'] = records[name]
            arcs[name]['banks'] = [{k: v for k, v in b.items() if k != 'frames'} for b in data['graphics_banks']]
            arcs[name]['noncomposable_main_references'] = [[b['bank'], f['index'], f.get('reason')]
                for b in data['graphics_banks'] for f in b['frames'] if f.get('standalone_structure') == 'not_composable']
        idles = {}
        for key, name, ref, layers, black in [
            ('zero_normal', 'PL01_U.ARC', 147, [0], False), ('zero_black', 'PL01_U.ARC', 147, [0], True),
            ('x_base', 'PL00_U.ARC', 0, [0], False), ('x_fourth_full', 'PL00_U.ARC', 0, [0, 8, 5, 7, 6], False),
            ('ultimate_before_jacket', 'PL02_U.ARC', 0, [0, 8, 5, 7, 6], False),
            ('ultimate_after_swim', 'PL02_U.ARC', 0, [0], False)]:
            im = idle_image(assets[name], ref, layers, black)
            filename = key + '_idle.png'
            im.save(target / filename)
            bbox = im.getbbox()
            idles[key] = {'archive': name, 'graphics_bank': 0, 'frame': ref, 'layers_in_order': layers,
                          'black_palette_row13': black, 'path': (target / filename).relative_to(ROOT).as_posix(),
                          'rgba_sha256': sha(im.tobytes()), 'png_sha256': file_sha(target / filename),
                          'bbox_world': [bbox[0]-160,bbox[1]-160,bbox[2]-160,bbox[3]-160],
                          'size': [bbox[2]-bbox[0],bbox[3]-bbox[1]], 'world_origin_in_png': [160,160],
                          'interpretation': 'Current actual BIN idle snapshot, not a new artwork or all-animation quality approval.'}
        reports[project] = {'bin': path.relative_to(ROOT).as_posix(), 'sha256': expected,
                            'executable_sha256': sha(assets['SLUS_005.61']), 'archives': arcs,
                            'idle_snapshots': idles, 'historical_idle_references': reference_inventory(project, idles),
                            'focused_regression_checks': focused_regressions(assets, original),
                            'idle_sequences': {k: v['animations'][5] for k, v in anims.items()}}
    assert reports['ver_buki_riko']['executable_sha256'] == reports['ver_rin_nana']['executable_sha256']
    timer = timer_cpu(assets['SLUS_005.61'])
    write(OUT / 'native_animation_timer.json', timer)
    report = {'scope': 'Coverage, stream decoding, native animation metadata and accepted idle-reference investigation only.',
              'original_sha256': US_SHA, 'projects': reports, 'x_frame_groups': X_GROUPS,
              'x_placeholder_refs': sorted(X_PLACEHOLDERS), 'zero_partial_upload_refs': list(range(42, 50)),
              'zero_static_body': {'archive_entry_type': '0x10206', 'composition_bank': 6, 'frames': [23, 24]},
              'native_timer_proof': 'native_animation_timer.json', 'full_visual_audit_performed': False,
              'gameplay_test_performed': False, 'source_or_active_files_modified': False}
    write(OUT / 'manifest.json', report)
    print(json.dumps({'output': OUT.relative_to(ROOT).as_posix(), 'idle': {p:{k:v['size'] for k,v in r['idle_snapshots'].items()} for p,r in reports.items()},
                      'all_stream_decode_counts': {p:{n:a['graphics_reference_count'] for n,a in r['archives'].items()} for p,r in reports.items()},
                      'native_timer_passed':timer['passed']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
