"""Nana Ultimate 등장10 독립 reader; 제작 모듈 미호출."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).parent
sys.path[:0] = [str(ROOT), str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets, composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw, parts, sig, tile, render, color, polygons

N = D.parent / 'nana_audit'
U = N / 'ultimate_ceremony_repaint'
P = U / 'packed_arrival_candidate_v1'
T = U / 'arrival_targets_probe_v2'
O = D / 'nana_ultimate_arrival10_independent01'
PBS = (0, 5, 6, 7, 8)
REFS = {130, 131, 133, 134, 135, 136, 137, 138, 139, 141}
BODIES = (133, 135, 136, 137, 138)
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
    return np.asarray(Image.open(p))

def overlay(bg, fg):
    return np.where(fg > 0, fg, bg).astype(np.uint8)

def full(ar, n):
    z = ar.layer(n)[0].copy()
    for pb in (8, 5, 7, 6):
        z = overlay(z, ar.layer(n, pb)[0])
    return z

def shift(z, dy):
    v = np.zeros_like(z)
    y, x = np.nonzero(z)
    v[y+dy, x] = z[y, x]
    return v

def rect(bounds):
    x0, y0, x1, y1 = bounds
    z = np.zeros((384, 384), bool)
    z[y0+160:y1+160, x0+160:x1+160] = True
    return z

oldp = N / 'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC'
newp = P / 'PL02_U.ARC'
old, new = readb(oldp), readb(newp)
assert sha(old) == 'c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
assert sha(new) == 'c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
a, b = Archive(old), Archive(new)
lockpath = P / 'INPUT_FROZEN.json'
lock = readj(lockpath)
assert lock['parent_sha256'] == sha(old) and lock['candidate_sha256'] == sha(new)
for q in lock['files']:
    v = readb(ROOT / q['path'])
    assert len(v) == q['size'] and sha(v) == q['sha256'], q['path']
meta = readj(T / 'manifest.json')
assert meta['parent_arc_sha256'] == sha(old) and set(meta['refs']) == REFS
rules = {q['ref']: q for q in meta['rules']}

# Native registered bodies and common pistol/hand; no image generator or quantizer called.
casep = U / 'canonical_cases_probe_v2'
cases = readj(casep / 'manifest.json')
assert cases['donor_arc_sha256'] == sha(old) and cases['donor_ref'] == 85
casecoords = cases['canonical_source_texels']
assert len(casecoords) == 20
for x, y, v in casecoords:
    assert a.layer(85)[0][y+160, x+160] == v
case_masks = {}
for q in cases['frames']:
    n, form = q['ref'], q['form']
    expected = np.zeros((384, 384), np.uint8)
    matrix, delta = np.array(q['matrix']), np.array(q['translation'])
    assert abs(round(np.linalg.det(matrix))) == 1 and np.array_equal(matrix @ matrix.T, np.eye(2))
    for x, y, v in casecoords:
        tx, ty = matrix @ np.array([x, y]) + delta
        expected[ty+160, tx+160] = v
    assert np.count_nonzero(expected) == 20
    assert np.array_equal(expected, png(casep / f'{form}_{n:03}_case.png'))
    case_masks[form, n] = expected
commonp = U / 'common_hands_probe_v1'
common = readj(commonp / 'manifest.json')
assert sha((commonp / 'manifest.json').read_bytes()) == meta['body_source_manifest_sha256']
body, bodyproof = {}, []
for q in common['frames']:
    n = q['ref']
    bp, ap = ROOT / q['before_path'], ROOT / q['after_path']
    bef, aft = png(bp), png(ap).copy()
    assert sha(bp.read_bytes()) == q['before_source_sha256'] and sha(ap.read_bytes()) == q['after_source_sha256']
    mask = polygons([q['common_hand_polygon']]) | (case_masks['before', n] > 0)
    common_hand = np.where(bef == 15, 13, bef).astype(np.uint8)
    aft[mask] = common_hand[mask]
    assert np.array_equal(bef, png(commonp / f'before_{n:03}.png'))
    assert np.array_equal(aft, png(commonp / f'after_{n:03}.png'))
    assert sha(bef.tobytes()) == q['before_sha256'] and sha(aft.tobytes()) == q['after_sha256']
    body['before', n], body['after', n] = bef, aft
    bodyproof.append({'ref': n, 'canonical20_module_rigid_exact': True, 'common_hand_reconstructed': True})
lp = U / 'settle_legs_registered_v1'
lm = readj(lp / 'manifest.json')
assert sha((lp / 'manifest.json').read_bytes()) == rules[138]['source_manifest_sha256']
legs, side = rect(lm['legs_mask_world']), rect(lm['side_mask_world'])
mask = legs | side
fixed = {f: png(lp / f'{f}_fixed.png') for f in ('before', 'after')}
for q in lm['frames']:
    f = q['form']
    assert sha(fixed[f].tobytes()) == q['native_fixed_sha256']
    z = body[f, 138].copy()
    z[mask] = fixed[f][mask]
    if f == 'after':
        shared = np.where(fixed['before'] == 15, 13, fixed['before']).astype(np.uint8)
        z[legs] = shared[legs]
    assert np.array_equal(z, png(lp / f'{f}_138.png')) and sha(z.tobytes()) == q['target_sha256']
    assert np.array_equal(z[~mask], body[f, 138][~mask])
    assert np.array_equal(z[180:], body[f, 138][180:])
    body[f, 138] = z

# Exact historical FX and shell/window rules are reconstructed independently.
histp = ROOT / meta['historical_arc']
hist = Archive(readb(histp))
assert sha(hist.data) == meta['historical_arc_sha256']
effects = []
for n in (136, 137):
    ps = [q for q in parts(hist, 0, n) if q['tile'] == 7]
    assert [sig(q) for q in ps] == [sig(q) for q in rules[n]['source_parts']]
    fx = render(hist, n, 0, ps)
    assert np.count_nonzero(fx) == 46 and sha(fx.tobytes()) == rules[n]['effect_sha256']
    for f in ('before', 'after'):
        body[f, n] = overlay(body[f, n], fx)
    effects.append({'ref': n, 'historical_tile7_pixels': 46, 'source_records': [sig(q) for q in ps]})
orb = hist.layer(129)[0]
assert np.array_equal(overlay(orb, a.layer(133)[0]), a.layer(134)[0])
assert sha(orb.tobytes()) == rules[134]['effect_sha256']
for f in ('before', 'after'):
    body[f, 134] = overlay(orb, body[f, 133])
    body[f, 139] = shift(body[f, 138], -1)
ps = parts(hist, 0, 131)[:16]
fx131 = render(hist, 131, 0, ps)
assert np.array_equal(fx131, a.layer(132)[0]) and sha(fx131.tobytes()) == rules[131]['effect_sha256']
assert np.array_equal(np.where(a.layer(133)[0] > 0, 13, fx131), a.layer(131)[0])
for f in ('before', 'after'):
    body[f, 131] = np.where(body['after', 133] > 0, 13, fx131).astype(np.uint8)
disc, _ = read_disc(ROOT / 'MegaMan X4.bin', ('PL02_U.ARC',))
us = Archive(disc['PL02_U.ARC'])
assert sha(us.data) == rules[130]['source_us_arc_sha256']
mapping = np.array([0, 5, 1, 10, 12, 9, 7, 5, 13, 9, 6, 1, 8, 7, 6, 5], np.uint8)
assert mapping.tolist() == rules[130]['palette_index_map']
bg, shell = mapping[us.layer(129)[0] % 16], mapping[us.layer(130)[0] % 16]
oldbody = np.zeros((384, 384), np.uint8)
oldbody[80:240, 80:240] = png(ROOT / 'work/ver_rin_nana/nana_art/arrival_v1/production02/frame_133.png')
old130 = overlay(bg, np.where(oldbody > 0, 13, 0).astype(np.uint8))
new130 = overlay(bg, np.where(body['after', 133] > 0, 13, 0).astype(np.uint8))
counts_tiles = collections.Counter(q['tile'] for q in parts(us, 0, 130))
windows, shellmask = [], np.zeros((384, 384), bool)
for q in parts(us, 0, 130):
    if counts_tiles[q['tile']] > 1:
        box = [q['x'], q['y'], q['x']+16, q['y']+16]
        m = rect(box)
        shellmask |= m
        windows.append(box)
        old130[m], new130[m] = shell[m], shell[m]
assert windows == rules[130]['shell_windows'] and np.array_equal(old130, a.layer(130)[0])
assert sha(new130[shellmask].tobytes()) == rules[130]['shell_window_sha256']
for f in ('before', 'after'):
    body[f, 130] = new130.copy()
dustp = D / 'nana_arrival141_dust01'
dust_report = readj(dustp / 'report.json')
assert sha((dustp / 'report.json').read_bytes()) == rules[141]['independent_report_sha256']
readb(dustp / 'dust141_indices.npy')
dust = np.load(dustp / 'dust141_indices.npy')
assert np.count_nonzero(dust) == 12 and sha(dust.tobytes()) == rules[141]['dust_sha256']
body['before', 141] = overlay(dust, full(a, 0))
body['after', 141] = overlay(dust, a.layer(0)[0])
assert np.array_equal(body['before', 141], full(a, 141))

target = {}
for n in sorted(REFS):
    bef, aft = body['before', n], body['after', n]
    assert not np.any((aft > 0) & (bef == 0))
    target[n, 0] = aft
    target[n, 5] = np.where((bef != aft) | (bef == 15), bef, 0).astype(np.uint8)
    for pb in (6, 7, 8):
        target[n, pb] = np.zeros_like(aft)
    for pb in PBS:
        assert sha(target[n, pb].tobytes()) == meta['targets'][str(n)][str(pb)]
        assert np.array_equal(target[n, pb], png(T / f'layer{pb}_{n:03}.png'))

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
for pb in range(len(bank_offsets(a.c))):
    for n in range(composition_frame(a.c, pb, 0)['bank_frame_count']):
        op, bp = parts(a, pb, n), parts(b, pb, n)
        if pb in PBS and n in REFS:
            assert len(bp) <= 16
            for q in bp:
                t = q['tile']+q['page']*256
                assert 0 <= t < 32
                v = tile(b, n, t)
                assert not (t % 16 == 0 and v[:, 0].any())
                assert not (q['flip_y'] and t // 16 == 0 and v[0].any())
                counts['GPU_parts_checked'] += 1
        else:
            assert [sig(q) for q in op] == [sig(q) for q in bp]
            counts['non_target_compositions_exact'] += 1
assert a.banks[0]['frames'][131]['offset'] == a.banks[0]['frames'][132]['offset']
assert b.banks[0]['frames'][131]['offset'] != b.banks[0]['frames'][132]['offset']
assert raw(a, 0, 132) == raw(b, 0, 132)
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
O.mkdir(exist_ok=True)
sheets = []
for i, ns in enumerate(((133, 135), (136, 137), (138, 139), (130, 131), (134, 141))):
    cw, ch = 392, 476
    board = Image.new('RGB', (cw*4, ch*2), '#263345')
    draw = ImageDraw.Draw(board)
    for row, n in enumerate(ns):
        for col, (ar, mask, label) in enumerate(((a, 15, 'old before'), (b, 15, 'new before'), (a, 0, 'old after'), (b, 0, 'new after'))):
            x, y = col*cw, row*ch
            draw.text((x+4, y+4), f'{n} {label}', fill='white')
            im = ar.composite(n, mask)[0].crop((112, 96, 208, 208)).resize((384, 448), Image.Resampling.NEAREST)
            board.paste(im, (x+4, y+22), im)
    p = O / f'readback_{i:02}.png'
    board.save(p)
    sheets.append({'path': rel(p), 'sha256': sha(p.read_bytes())})
assert counts['raw_checked'] == 512 and counts['non_target_raw_exact'] == 502
assert counts['target_layers_exact'] == 50 and counts['non_target_layers_exact'] == 1090
assert counts['partial_RGBA_exact'] == 320
for name, h in tracked.items():
    assert sha((ROOT / name).read_bytes()) == h, name
report = {
    'passed': True, 'scope': 'Nana Ultimate 등장10 등록/권총·공통손/138국소→역사효과→50층→ARC 독립 reader. 제작모듈 미호출.',
    'candidate': rel(newp), 'candidate_sha256': sha(new), 'parent_sha256': sha(old),
    'target_manifest_sha256': sha((T / 'manifest.json').read_bytes()), 'input_lock_sha256': sha(lockpath.read_bytes()),
    'locked_inputs': len(lock['files']), 'counts': dict(counts), 'body_source_proof': bodyproof,
    'settle138_fixed_native_local_reconstruction_exact': True,
    'settle138_outside_local_shoes_hands_weapon_exact': True,
    'effects136137': effects, 'orb134_parent_rule_and_new133_reconstructed': True,
    'energy131_parent_rule_and_new133_alpha13_reconstructed': True,
    'shell130_historical_parent_reconstructed': True, 'shell130_full_windows_exact': windows,
    'dust141_exact12_from_independent_history': True,
    'translation139': {'dx': 0, 'dy': -1, 'both_costumes': True, 'new_authored_policy_not_original_US_alias': True},
    'support132': {'separate_stream': True, 'all_decoded_raw_tilecount_compositions_layers_exact': True},
    'all_bank_boundaries_archive_length_directory_palette_audio_other_entries_exact': True,
    'non_target_partial_RGBA_follows_exact1090_layers_and_palette': True,
    'new_GPU_edge_invasions': 0, 'readback_sheets': sheets, 'readback_actually_viewed': False,
    'inputs': tracked, 'producer_functions_called': False, 'source_generation_requantized': False,
    'native_MIPS_executed_here': False, 'runtime_verified': False,
}
report['limitations'] = ['고정 등록 뒤 의미 합성과 원효과를 독립 재구성했다. 생성원화 재양자화는 별도다.',
                         '전체7296조합을 반복하지 않고 대상320RGBA와 비대상1090층/팔레트 완전보존을 대조했다.',
                         '원시간표 재생·실제게임·최종사용자수용은 별도다.']
(O / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf8')
print(json.dumps({'passed': True, 'counts': dict(counts), 'report_sha256': sha((O / 'report.json').read_bytes())}))
