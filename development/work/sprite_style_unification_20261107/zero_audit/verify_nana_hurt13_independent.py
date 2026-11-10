"""Read only: independently decode hurt13 and reconstruct dependent FX."""
from pathlib import Path
import collections
import hashlib
import json
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, label, distance_transform_cdt

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import decode_stream, composition_frame, bank_offsets, indexed_atlas, compose_indices

D = Path(__file__).parent
N = D.parent / 'nana_audit'
H = N / 'hurt_repaint'
P = H / 'packed_hurt_candidate_v1'
T = H / 'final_targets_v1'
O = D / 'nana_hurt13_independent01'
PBS = (0, 5, 6, 7, 8)
REFS = set(range(106, 115)) | set(range(233, 237))
RESERVED = {105, *range(175, 183)}
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: json.loads(p.read_text('utf8'))
rel = lambda p: p.relative_to(ROOT).as_posix()
oldpath = N / 'rising_repaint/packed_base_candidate_v1/PL00_U.ARC'
newpath = P / 'PL00_U.ARC'
old, new = oldpath.read_bytes(), newpath.read_bytes()
assert sha(old) == '3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'
assert sha(new) == '978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f'
frozen = read(P / 'INPUT_FROZEN.json')
assert frozen['asset_sha256'] == sha(new) and frozen['parent_asset_sha256'] == sha(old)
for q in frozen['files']:
    assert sha((ROOT / q['path']).read_bytes()) == q['sha256'], q['path']
a, b = Archive(old), Archive(new)
counts = collections.Counter()
assert len(old) == len(new) and a.p == b.p
allowed = np.zeros(len(old), dtype=bool)
ae, be = psx_arc(old), psx_arc(new)
assert [(e['type'], e['offset'], e['size']) for e in ae] == [(e['type'], e['offset'], e['size']) for e in be]
for e in ae:
    if int(e['type'], 16) in (2, 3):
        allowed[e['offset']:e['offset'] + e['size']] = True
assert not np.any((np.frombuffer(old, np.uint8) != np.frombuffer(new, np.uint8)) & ~allowed)
assert bank_offsets(a.g, allow_aliases=True) == bank_offsets(b.g, allow_aliases=True)
assert bank_offsets(a.c) == bank_offsets(b.c)
raws = {}
for gb, (ob, nb) in enumerate(zip(a.banks, b.banks)):
    assert (ob['base'], ob['end']) == (nb['base'], nb['end']) and len(ob['frames']) == len(nb['frames'])
    if gb:
        assert a.g[ob['base']:ob['end']] == b.g[nb['base']:nb['end']]
        counts['effect_graphics_banks_byte_exact'] += 1
    for f, g in zip(ob['frames'], nb['frames']):
        n = f['index']
        assert n == g['index']
        x = decode_stream(a.g, f['offset'], f['limit'], f['tile_count'] * 128)
        y = decode_stream(b.g, g['offset'], g['limit'], g['tile_count'] * 128)
        assert x.serialize() == a.g[x.start:x.end] and y.serialize() == b.g[y.start:y.end]
        counts['raw_checked'] += 1
        if gb == 0 and n in REFS:
            assert g['tile_count'] == 32
            raws[n] = (x.data, f['tile_count'], y.data)
        else:
            assert x.data == y.data and f['tile_count'] == g['tile_count']
            counts['non_target_raw_exact'] += 1

def atlas(data, count):
    return np.frombuffer(indexed_atlas(data, count)[0], np.uint8).reshape(-1, 256)

def tile(data, count, t):
    x, y = t % 16 * 16, t // 16 * 16
    return atlas(data, count)[y:y + 16, x:x + 16]

def sig(p):
    return p['flags'], p['tile'], p['x'], p['y']

def parts(ar, pb, n):
    return composition_frame(ar.c, pb, n)['parts']

def render(ar, n, ps):
    out = np.zeros((384, 384), np.uint8)
    if not ps:
        return out
    f = ar.banks[0]['frames'][n]
    raw = decode_stream(ar.g, f['offset'], f['limit'], f['tile_count'] * 128).data
    px, size, box, _ = compose_indices(raw, f['tile_count'], {'parts': ps}, allowed_cluts={0, 1, 2, 3})
    v = np.frombuffer(px, np.uint8).reshape(size[1], size[0])
    ys, xs = np.nonzero(v)
    out[ys + box[1] + 160, xs + box[0] + 160] = v[ys, xs]
    return out

m = read(T / 'manifest.json')
assert set(map(int, m['targets'])) == REFS and m['parent_sha256'] == sha(old)
target = {}
for n in range(237):
    if n in RESERVED:
        continue
    for pb in PBS:
        z = b.layer(n, pb)[0]
        counts['layers_checked'] += 1
        if n in REFS:
            want = np.array(Image.open(T / f'layer{pb}_{n:03}.png'))
            assert want.shape == (384, 384) and want.dtype == np.uint8 and want.max() < 48
            assert sha(want.tobytes()) == m['targets'][str(n)][str(pb)]
            assert np.array_equal(z, want), (n, pb)
            target[n, pb] = want
            counts['registered_layers_exact'] += 1
        else:
            assert np.array_equal(z, a.layer(n, pb)[0])
            counts['non_target_layers_exact'] += 1
gpu_native_edges = []
for pb in range(len(bank_offsets(a.c))):
    for n in range(composition_frame(a.c, pb, 0)['bank_frame_count']):
        op, nparts = parts(a, pb, n), parts(b, pb, n)
        if pb in PBS and n in REFS:
            for p in nparts:
                t = p['tile'] + p['page'] * 256
                assert 0 <= t < 32
                tx = tile(raws[n][2], 32, t)
                u = t % 16 == 0 and bool(tx[:, 0].any())
                v = p['flip_y'] and t // 16 % 16 == 0 and bool(tx[0].any())
                if u or v:
                    assert any(sig(p) == sig(q) for q in op)
                    assert np.array_equal(tx, tile(raws[n][0], raws[n][1], t))
                    gpu_native_edges.append({'ref': n, 'bank': pb, 'record': sig(p), 'U': u, 'V': v})
                counts['target_GPU_parts_checked'] += 1
        else:
            assert [sig(p) for p in op] == [sig(p) for p in nparts]
            counts['non_target_compositions_exact'] += 1

# Body keys are registered art; derived frames are rebuilt from their real parts.
for n in (106, 110, 233, 234):
    for pb in PBS:
        source = np.array(Image.open(H / 'joint_layers_probe_v1' / f'layer{pb}_{n:03}.png'))
        assert np.array_equal(target[n, pb], source)
        counts['independent_body_key_layers'] += 1
effects = []
for n, core in ((107, 106), (108, 106), (111, 110)):
    assert b.banks[0]['frames'][n]['offset'] == b.banks[0]['frames'][core]['offset']
    for pb in PBS:
        remaining = collections.Counter(sig(p) for p in parts(a, pb, core))
        extras = []
        for p in parts(a, pb, n):
            if remaining[sig(p)]:
                remaining[sig(p)] -= 1
            else:
                extras.append(p)
        assert not any(remaining.values())
        assert [sig(p) for p in parts(b, pb, n)] == [sig(p) for p in parts(b, pb, core)] + [sig(p) for p in extras]
        fx = render(a, n, extras)
        assert np.array_equal(fx, render(b, n, extras))
        assert np.array_equal(target[n, pb], np.where(fx, fx, target[core, pb]))
        ts = sorted({p['tile'] for p in extras})
        for t in ts:
            assert np.array_equal(tile(raws[n][0], raws[n][1], t), tile(raws[n][2], 32, t))
            counts['original_whole_effect_tiles_exact'] += 1
        effects.append({'ref': n, 'bank': pb, 'tiles': ts, 'records': len(extras), 'raster_exact': True})

mask = target[106, 0] > 0
flash = np.zeros_like(target[106, 0])
flash[binary_dilation(mask)] = 9
flash[mask] = 13
assert np.array_equal(flash, target[109, 0])
assert all(not target[109, pb].any() for pb in PBS[1:])
invp = ROOT / 'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json'
inv = read(invp)
def original(n):
    z = np.array(Image.open(invp.parent / f'base_{n:03}.png'))
    box = inv['base_frames'][n]['bounds']
    result = np.zeros((384, 384), np.uint8)
    ys, xs = np.nonzero(z)
    result[ys + box[1] + 160, xs + box[0] + 160] = z[ys, xs] % 16
    return result
def silhouette(n, residual, body):
    z = residual.copy()
    mask = body > 0
    if n == 112:
        z[binary_dilation(mask)] = 6
        z[mask] = 14
    elif n == 113:
        z[binary_dilation(mask)] = 1
    else:
        z[binary_dilation(mask)] = 1
        z[mask] = 3
        z[np.isin(body, (1, 2, 4, 8, 15))] = 5
        z[np.isin(body, (6, 9))] = 1
    return z
derived = []
for n in (112, 113, 114):
    residue = original(n)
    residue[binary_dilation(original(110) > 0, iterations=2)] = 0
    if n == 114:
        residue[np.isin(residue, (3, 5))] = 0
    historical = silhouette(n, residue, a.layer(110)[0])
    labels, _ = label(historical > 0)
    sizes = np.bincount(labels.ravel())
    removed = (labels != 0) & (sizes[labels] < 4)
    old_expected = historical.copy()
    old_expected[removed] = 0
    assert np.array_equal(old_expected, a.layer(n)[0] % 16)
    residue[removed] = 0
    z = silhouette(n, residue, target[110, 0])
    z = np.where(z, z + 32, 0).astype(np.uint8)
    assert np.array_equal(z, target[n, 0])
    assert all(not target[n, pb].any() for pb in PBS[1:])
    derived.append({'ref': n, 'parent_rule_reconstructed_exact': True,
                    'new_body_rule_exact': True, 'new_small_components_deleted': False,
                    'original_residual_hash': sha(residue.tobytes())})

auras = []
am = read(H / 'aura_contact_probe_v2/manifest.json')
assert m['aura_registration'] == am
union = np.logical_or.reduce([target[234, pb] > 0 for pb in PBS])
distance = distance_transform_cdt(~union, metric='taxicab')
for q in am['frames']:
    n = q['ref']
    oldbody = a.layer(234)[0]
    oldfx = np.where(oldbody, 0, a.layer(n)[0]).astype(np.uint8)
    assert sha(oldfx.tobytes()) == q['source_effect_sha256']
    labels, num = label(oldfx > 0, structure=np.ones((3, 3), bool))
    z = np.zeros_like(oldfx)
    source_seen, translations = set(), collections.defaultdict(set)
    for p in q['source_links']:
        sx, sy = p['source_world']
        x, y = p['world']
        val = p['index']
        assert oldfx[sy + 160, sx + 160] == val and val != 0
        assert (sx, sy) not in source_seen and not z[y + 160, x + 160]
        source_seen.add((sx, sy))
        z[y + 160, x + 160] = val
        translations[int(labels[sy + 160, sx + 160])].add((x - sx, y - sy))
    assert len(source_seen) == np.count_nonzero(oldfx) == q['old_count'] == q['new_count']
    assert len(translations) == num and all(len(v) == 1 for v in translations.values())
    assert all(max(abs(x), abs(y)) <= 3 for ts in translations.values() for x, y in ts)
    assert sha(z.tobytes()) == q['registered_effect_sha256']
    assert not np.any((z > 0) & union)
    assert np.array_equal(target[n, 0], np.where(z, z, target[234, 0]))
    assert all(np.array_equal(target[n, pb], target[234, pb]) for pb in PBS[1:])
    auras.append({'ref': n, 'pixel_count': len(source_seen), '8connected_components': num,
                  'each_component_rigid_translation': {str(k): list(next(iter(v))) for k, v in translations.items()},
                  'all_source_pixels_unique_and_color_exact': True, 'body_or_partial_layer_overlap': 0,
                  'maximum_manhattan_distance': int(distance[z > 0].max())})

def color(z, start=0):
    table = np.array([[(int(w) >> s & 31) * 255 // 31 for s in (0, 5, 10)] +
                      [0 if i % 16 == 0 else 255] for i, w in enumerate(b.words[start:])], np.uint8)
    return table[z]
for n in sorted(REFS):
    for mask in range(16):
        for arm in (1, 2):
            want = color(target[n, 0])
            for bit, pb in ((8, 8), (1, 5), (4, 7), (2, 6)):
                if mask & bit:
                    v = color(target[n, pb], 32 if pb == 7 and arm == 2 else 16)
                    occupied = v[:, :, 3] > 0
                    want[occupied] = v[occupied]
            assert np.array_equal(want, np.array(b.composite(n, mask, arm)[0]))
            counts['independent_partial_RGBA'] += 1

O.mkdir(exist_ok=True)
sheets = []
for idx, ns in enumerate(((106, 110), (233, 234), (107, 108, 109), (111, 112, 113), (114, 235, 236))):
    crop = (127, 126, 197, 194)
    scale, cw, ch = 4, 292, 300
    pic = Image.new('RGB', (cw * 4, ch * len(ns)), '#263345')
    dr = ImageDraw.Draw(pic)
    for row, n in enumerate(ns):
        panels = [('old base', a.composite(n)[0]), ('new base', b.composite(n)[0]),
                  ('old Fourth', a.composite(n, 15)[0]), ('new Fourth', b.composite(n, 15)[0])]
        for col, (name, frame) in enumerate(panels):
            x, y = col * cw, row * ch
            dr.text((x + 4, y + 4), f'{n} {name}', fill='white')
            v = frame.crop(crop).resize((280, 272), Image.Resampling.NEAREST)
            pic.paste(v, (x + 6, y + 23), v)
    p = O / f'readback_{idx:02}.png'
    pic.save(p)
    sheets.append({'path': rel(p), 'sha256': sha(p.read_bytes())})
assert counts['raw_checked'] == 508 and counts['non_target_raw_exact'] == 495
assert counts['layers_checked'] == 1140 and counts['registered_layers_exact'] == 65
assert counts['non_target_layers_exact'] == 1075 and counts['independent_partial_RGBA'] == 416
assert oldpath.read_bytes() == old and newpath.read_bytes() == new
for q in frozen['files']:
    assert sha((ROOT / q['path']).read_bytes()) == q['sha256'], q['path']
report = {
    'passed': True, 'scope': '나나 기본/포스 피격13 최종 후보 독립 읽기. 제작·정합·패킹 함수 미호출.',
    'parent': rel(oldpath), 'parent_sha256': sha(old), 'candidate': rel(newpath), 'candidate_sha256': sha(new),
    'target_manifest': rel(T / 'manifest.json'), 'target_manifest_sha256': sha((T / 'manifest.json').read_bytes()),
    'input_frozen_sha256': sha((P / 'INPUT_FROZEN.json').read_bytes()), 'input_files_checked': len(frozen['files']),
    'counts': dict(counts), 'palette_audio_static_all_other_entries_exact': True,
    'bank_boundaries_exact': True, 'original_whole_effect_tiles_and_records': effects,
    'preserved_original_GPU_edge_exceptions': gpu_native_edges, 'new_GPU_edge_invasions': 0,
    'derived_flash109_exact': True, 'derived_CLUT2_frames': derived, 'aura_reconstruction': auras,
    'all_non_target_partial_RGBA_follows_from_exact1075_layers_and_palette': True,
    'new_readback_sheets': sheets, 'readback_actually_viewed': False,
    'art_generation_quantization_reconstructed': False, 'producer_functions_called': False,
    'native_MIPS_executed_here': False, 'runtime_verified': False, 'source_files_unchanged': True,
    'limits': ['원화 생성·양자화 전과정 재현이 아니라 고정 등록65층과 실물 ARC를 대조했다.',
               '109/112..114는 기존 원효과와 새 몸체의 파생 규칙,235/236은 원오라 조각의 색·형상·강체 이동을 독립 재구성했다.',
               '실제 피격 팔레트 전환·60Hz 물리·게임 재현이나 사용자 최종수용은 별도이다.'],
}
(O / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'passed': True, 'counts': dict(counts), 'aura': auras,
                  'report_sha256': sha((O / 'report.json').read_bytes())}))
