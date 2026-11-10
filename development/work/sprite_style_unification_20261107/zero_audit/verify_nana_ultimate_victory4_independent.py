"""Nana Ultimate 승리4: 제작 함수를 부르지 않는 출처/자원 독립 reader."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label, binary_dilation

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).parent
sys.path[:0] = [str(ROOT), str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets, composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw, parts, sig, tile, color, polygons

N = D.parent / 'nana_audit'
U = N / 'ultimate_victory_repaint'
P = U / 'packed_victory_candidate_v1'
T = U / 'final_targets_v1'
O = D / 'nana_ultimate_victory4_independent01'
PBS = (0, 5, 6, 7, 8)
REFS = {204, 205, 206, 207}
RESERVED = {105, *range(175, 183)}
sha = lambda x: hashlib.sha256(x).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
tracked = {}

def readb(p):
    v = p.read_bytes()
    tracked[rel(p)] = sha(v)
    return v

def readj(p):
    return json.loads(readb(p))

def png(p):
    readb(p)
    return np.array(Image.open(p))

def box(bounds):
    x0, y0, x1, y1 = bounds
    z = np.zeros((384, 384), bool)
    z[y0+160:y1+160, x0+160:x1+160] = True
    return z

oldp = N / 'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC'
newp = P / 'PL02_U.ARC'
old, new = readb(oldp), readb(newp)
assert sha(old) == 'c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
assert sha(new) == 'b7dcf46dba35084265e8b32529d7a4d072108ed201a60ba4f17fcc71494aa1c5'
a, b = Archive(old), Archive(new)
lockpath = P / 'INPUT_FROZEN.json'
lock = readj(lockpath)
assert lock['parent_sha256'] == sha(old) and lock['candidate_sha256'] == sha(new)
for q in lock['files']:
    v = readb(ROOT / q['path'])
    assert len(v) == q['size'] and sha(v) == q['sha256'], q['path']
meta = readj(T / 'manifest.json')
assert meta['parent_arc_sha256'] == sha(old) and set(meta['refs']) == REFS

# 고정 등록 원화에서 머리/사지 공통부와 의상 의미영역을 별도로 재합성한다.
cp = U / 'costume_pair_probe_v2'
cm = readj(cp / 'manifest.json')
body, source_proof = {}, []
for q in cm['frames']:
    n = q['ref']
    bp, ap = ROOT / q['before_source'], ROOT / q['after_source']
    bef, donor = png(bp), png(ap)
    assert sha(bp.read_bytes()) == q['before_source_sha256']
    assert sha(ap.read_bytes()) == q['after_source_sha256']
    common = np.where(bef == 15, 13, bef).astype(np.uint8)
    m = polygons([q['costume_polygon']])
    for x, y, v in q['after_hair_excluded_from_costume']:
        assert donor[y+160, x+160] == v == 5 and bef[y+160, x+160] == 0
        m[y+160, x+160] = False
    aft = common.copy()
    aft[m] = donor[m]
    assert np.array_equal(aft[~m], common[~m])
    assert not np.any((aft > 0) & (bef == 0))
    for form, z in (('before', bef), ('after', aft)):
        assert sha(z.tobytes()) == q[form+'_sha256']
        assert np.array_equal(z, png(cp / f'{form}_{n:03}.png'))
        assert label(z > 0, np.ones((3, 3)))[1] == 1
        body[form, n] = z
    source_proof.append({'ref': n, 'new_registered_pair_reconstructed': True,
                         'costume_pixels': int(m.sum()), 'hair_exclusions': q['after_hair_excluded_from_costume']})

# 85의 실제 정본20색인을 정수 직교변환으로 검증하고 새 손 피부 가림을 보존한다.
wp = U / 'canonical_weapon_probe_v1'
wm = readj(wp / 'manifest.json')
assert wm['canonical_donor_arc_sha256'] == sha(old) and wm['canonical_donor_ref'] == 85
coords = wm['canonical_texels']
assert len(coords) == 20
for x, y, v in coords:
    assert a.layer(85)[0][y+160, x+160] == v
remove_bounds = {206: (-14, -19, -9, -10), 207: (-15, -38, -9, -28)}
hand_bounds = {206: (-14, -12, -10, -8), 207: (-16, -31, -10, -27)}
weapons = []
for q in wm['frames']:
    n, form = q['ref'], q['form']
    z = body[form, n].copy()
    assert np.array_equal(z, png(ROOT / q['body_source']))
    case = np.zeros_like(z)
    rm, skin = np.zeros_like(z, bool), np.zeros_like(z, bool)
    if q['new_weapon']:
        matrix, delta = np.array(q['matrix']), np.array(q['translation'])
        assert np.array_equal(matrix @ matrix.T, np.eye(2)) and abs(round(np.linalg.det(matrix))) == 1
        for x, y, v in coords:
            tx, ty = matrix @ np.array([x, y]) + delta
            case[ty+160, tx+160] = v
        assert np.count_nonzero(case) == 20
        rm = box(remove_bounds[n]) & np.isin(z, range(1, 10))
        skin = box(hand_bounds[n]) & np.isin(z, (10, 11, 12, 13))
        removed = [[int(x-160), int(y-160), int(z[y, x])] for y, x in np.argwhere(rm)]
        assert removed == q['source_weapon_removed']
        saved = z.copy()
        z[rm] = 0
        visible = (case > 0) & ~skin
        z[visible] = case[visible]
        z[skin] = saved[skin]
        assert np.array_equal(z[~(rm | (case > 0))], saved[~(rm | (case > 0))])
        assert int(visible.sum()) == q['visible_texels'] and int(skin.sum()) == q['skin_pixels_preserved']
        adjacent = int(((case > 0) & binary_dilation(skin, np.ones((3, 3)))).sum())
        assert adjacent == q['gun_adjacent_to_hand_pixels8']
        weapons.append({'ref': n, 'form': form, 'canonical_texels': 20, 'visible': int(visible.sum()),
                        'skin_preserved': int(skin.sum()), 'adjacent_to_skin': adjacent,
                        'matrix': matrix.tolist(), 'translation': delta.tolist()})
    else:
        assert n in (204, 205)
    assert np.array_equal(case, png(wp / f'{form}_{n:03}_case.png'))
    assert np.array_equal(rm, png(wp / f'{form}_{n:03}_removed_mask.png') > 0)
    assert np.array_equal(skin, png(wp / f'{form}_{n:03}_skin_mask.png') > 0)
    assert np.array_equal(z, png(wp / f'{form}_{n:03}_indices.png'))
    assert sha(z.tobytes()) == q['target_sha256'] and label(z > 0, np.ones((3, 3)))[1] == 1
    body[form, n] = z

target = {}
for n in sorted(REFS):
    bef, aft = body['before', n], body['after', n]
    assert not np.any((aft > 0) & (bef == 0))
    target[n, 0] = aft
    target[n, 5] = np.where((bef != aft) | (bef == 15), bef, 0).astype(np.uint8)
    for pb in (6, 7, 8):
        target[n, pb] = np.zeros_like(aft)
    for pb in PBS:
        assert np.array_equal(target[n, pb], png(T / f'layer{pb}_{n:03}.png'))
        assert sha(target[n, pb].tobytes()) == meta['targets'][str(n)][str(pb)]

counts = collections.Counter()
assert len(old) == len(new) and a.p == b.p
ae, be = psx_arc(old), psx_arc(new)
assert [(q['type'], q['offset'], q['size']) for q in ae] == [(q['type'], q['offset'], q['size']) for q in be]
allow = np.zeros(len(old), bool)
for q in ae:
    if int(q['type'], 16) in (2, 3):
        allow[q['offset']:q['offset']+q['size']] = True
assert not np.any((np.frombuffer(old, np.uint8) != np.frombuffer(new, np.uint8)) & ~allow)
assert bank_offsets(a.g, allow_aliases=True) == bank_offsets(b.g, allow_aliases=True)
assert bank_offsets(a.c) == bank_offsets(b.c)
for gb, (ab, bb) in enumerate(zip(a.banks, b.banks)):
    assert (ab['base'], ab['end'], len(ab['frames'])) == (bb['base'], bb['end'], len(bb['frames']))
    if gb:
        assert a.g[ab['base']:ab['end']] == b.g[bb['base']:bb['end']]
        counts['other_graphics_banks_byte_exact'] += 1
    for f, g in zip(ab['frames'], bb['frames']):
        n = f['index']
        assert n == g['index']
        counts['raw_checked'] += 1
        if gb == 0 and n in REFS:
            assert g['tile_count'] == 32
        else:
            assert raw(a, gb, n) == raw(b, gb, n) and f['tile_count'] == g['tile_count']
            counts['non_target_raw_exact'] += 1
for n in range(237):
    if n in RESERVED:
        continue
    for pb in PBS:
        want = target[n, pb] if n in REFS else a.layer(n, pb)[0]
        assert np.array_equal(b.layer(n, pb)[0], want), (n, pb)
        counts['target_layers_exact' if n in REFS else 'non_target_layers_exact'] += 1

shared = []
for pb in range(len(bank_offsets(a.c))):
    allparts = {n: parts(a, pb, n) for n in range(composition_frame(a.c, pb, 0)['bank_frame_count'])}
    selected_addresses = {q['record_offset'] for n in REFS if n in allparts and pb in PBS for q in allparts[n]}
    for n, op in allparts.items():
        bp = parts(b, pb, n)
        if pb in PBS and n in REFS:
            assert len(bp) <= 16
            for q in bp:
                t = q['tile'] + q['page'] * 256
                assert 0 <= t < 32 and q['unknown_flags'] == 0
                v = tile(b, n, t)
                assert not (t % 16 == 0 and v[:, 0].any())
                assert not (q['flip_y'] and t // 16 == 0 and v[0].any())
                counts['GPU_parts_checked'] += 1
        else:
            assert [sig(q) for q in op] == [sig(q) for q in bp]
            counts['non_target_compositions_exact'] += 1
            overlaps = sorted(selected_addresses & {q['record_offset'] for q in op})
            if overlaps:
                shared.append({'bank': pb, 'ref': n, 'shared_parent_record_offsets': overlaps,
                               'entire_composition_semantics_exact': True})
assert any(q['bank'] == 5 and q['ref'] == 89 for q in shared)
assert raw(a, 0, 89) == raw(b, 0, 89)
for n in sorted(REFS):
    for mask in range(16):
        for arm in (1, 2):
            expected = color(b, target[n, 0])
            for bit, pb in ((8, 8), (1, 5), (4, 7), (2, 6)):
                if mask & bit:
                    v = color(b, target[n, pb], 32 if pb == 7 and arm == 2 else 16)
                    m = v[:, :, 3] > 0
                    expected[m] = v[m]
            assert np.array_equal(expected, np.asarray(b.composite(n, mask, arm)[0]))
            counts['partial_RGBA_exact'] += 1
    assert np.array_equal(color(b, body['before', n], 16), np.asarray(b.composite(n, 15)[0]))
    assert np.array_equal(color(b, body['after', n]), np.asarray(b.composite(n, 0)[0]))

O.mkdir(exist_ok=True)
sheets = []
for i, ns in enumerate(((204, 205), (206, 207))):
    cw, ch = 392, 476
    board = Image.new('RGB', (cw*4, ch*2), '#263345')
    draw = ImageDraw.Draw(board)
    for row, n in enumerate(ns):
        for col, (ar, mask, caption) in enumerate(((a, 15, 'old before'), (b, 15, 'new before'), (a, 0, 'old after'), (b, 0, 'new after'))):
            x, y = col*cw, row*ch
            draw.text((x+4, y+4), f'{n} {caption}', fill='white')
            im = ar.composite(n, mask)[0].crop((112, 96, 208, 208)).resize((384, 448), Image.Resampling.NEAREST)
            board.paste(im, (x+4, y+22), im)
    p = O / f'readback_{i:02}.png'
    board.save(p)
    sheets.append({'path': rel(p), 'sha256': sha(p.read_bytes())})
assert counts['raw_checked'] == 512 and counts['non_target_raw_exact'] == 508
assert counts['target_layers_exact'] == 20 and counts['non_target_layers_exact'] == 1120
assert counts['partial_RGBA_exact'] == 128
for name, h in tracked.items():
    assert sha((ROOT / name).read_bytes()) == h, name
report = {'passed': True, 'scope': 'Nana Ultimate 승리4 고정등록8→의상 의미영역/정본권총→20층→실제ARC 독립 reader',
          'candidate': rel(newp), 'candidate_sha256': sha(new), 'parent_sha256': sha(old),
          'target_manifest_sha256': sha((T / 'manifest.json').read_bytes()), 'input_lock_sha256': sha(lockpath.read_bytes()),
          'locked_inputs': len(lock['files']), 'counts': dict(counts), 'body_sources': source_proof,
          'empty_hands204205_preserved': True, 'canonical_weapon_four_cases': weapons,
          'parent_shared_record_owners_preserved': shared, 'support89_raw_layers_entire_composition_exact': True,
          'all_bank_boundaries_archive_directory_length_palette_audio_other_entries_exact': True,
          'non_target_partial_RGBA_follows_exact1120_layers_palette': True,
          'new_GPU_edge_invasions': 0, 'readback_sheets': sheets, 'readback_actually_viewed': False,
          'inputs': tracked, 'producer_functions_called': False, 'source_generation_requantized': False,
          'native_MIPS_executed_here': False, 'runtime_verified': False,
          'limitations': ['원화 전체 재양자화 대신 고정등록 이후 의미 합성과 권총/손 가림을 독립 재구성했다.',
                          '전체7296RGBA를 반복하지 않고 대상128과 비대상1120층/팔레트 불변을 대조했다.',
                          '원시간표 재생·실제게임·최종사용자수용은 별도다.']}
(O / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf8')
print(json.dumps({'passed': True, 'counts': dict(counts), 'report_sha256': sha((O / 'report.json').read_bytes())}))
