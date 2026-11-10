"""실제 PL02 귀환156..161과 역사 파생 출처 읽기. 제작 모듈 호출/자원쓰기 없음."""
from pathlib import Path
import hashlib, json, sys, struct
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).parent
sys.path[:0] = [str(ROOT), str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw, parts, sig, tile, render

H = D.parent / 'shibuki_audit'
O = D / 'shibuki_ultimate_return_relations01'
O.mkdir(exist_ok=True)
PBS = (0, 5, 6, 7, 8)
REFS = range(156, 162)
sha = lambda v: hashlib.sha256(v).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
tracked = {}

def load(p):
    v = p.read_bytes(); tracked[rel(p)] = sha(v); return v

def png(p):
    load(p); return np.asarray(Image.open(p))

def full(ar, n):
    z = ar.layer(n)[0].copy(); overlay = np.zeros_like(z)
    for pb in (8, 5, 7, 6):
        v = ar.layer(n, pb)[0]; z[v > 0] = v[v > 0]; overlay[v > 0] = v[v > 0]
    return z, overlay

def over(bg, fg): return np.where(fg > 0, fg, bg).astype(np.uint8)

def shift(z, dy):
    out = np.zeros_like(z); y, x = np.nonzero(z); out[y+dy, x] = z[y, x]; return out

def diff(a, b, cells=False):
    m = a != b; y, x = np.nonzero(m)
    q = {'different_pixels': int(m.sum()), 'bbox_world': [int(x.min()-160), int(y.min()-160), int(x.max()-159), int(y.max()-159)] if len(x) else None}
    if cells and len(x) <= 100:
        q['cells'] = [{'world': [int(xx-160), int(yy-160)], 'predicted': int(a[yy, xx]), 'actual': int(b[yy, xx])} for yy, xx in zip(y, x)]
    return q

def aura(z):
    m = z > 0
    inner = binary_dilation(m, np.ones((3, 3)))
    outer = binary_dilation(m, np.ones((3, 3)), iterations=2)
    return np.where(m, z, np.where(inner, 9, np.where(outer, 14, 0))).astype(np.uint8)

source = H / 'prepared_ultimate_arrival_partial01/PL02_U.ARC'
a = Archive(load(source))
assert sha(a.data) == '3e55b972c007731a8446c8478336c6def303e0dc5ed4ab5d6a52856471327138'
prior = Archive(load(H / 'prepared_ultimate_hurt02/PL02_U.ARC'))
histpath = ROOT / 'work/overhaul_20261105/sprites/ver_buki_riko/baseline/PL02_U.ARC'
hist = Archive(load(histpath))
folder = ROOT / 'work/overhaul_20261105/sprites/shibuki_preultimate'
nb156 = png(folder / 'normalized/156.png')
original, _ = read_disc(ROOT / 'MegaMan X4.bin', ('PL02_U.ARC', 'SLUS_005.61'))
us = Archive(original['PL02_U.ARC'])

rows = []
for n in REFS:
    f = a.banks[0]['frames'][n]
    assert raw(a, 0, n) == raw(prior, 0, n)
    layers = {}
    for pb in PBS:
        ps = parts(a, pb, n); slots = {q['record_offset'] for q in ps}
        aliases = [j for j in range(237) if j != n and slots & {q['record_offset'] for q in parts(a, pb, j)}]
        assert [sig(q) for q in ps] == [sig(q) for q in parts(prior, pb, n)]
        assert np.array_equal(a.layer(n, pb)[0], prior.layer(n, pb)[0])
        layers[str(pb)] = {'opaque': int(np.count_nonzero(a.layer(n, pb)[0])), 'parts': ps, 'record_overlap_refs': aliases}
    rows.append({'ref': n, 'tile_count': f['tile_count'], 'stream_offset': f['offset'],
                 'raw_sha256': sha(raw(a, 0, n)), 'raw_owners': [q['index'] for q in a.banks[0]['frames'] if q['offset'] == f['offset']], 'layers': layers})

energy = hist.layer(159)[0]
assert np.array_equal(energy, a.layer(159)[0])
np.save(O / 'historical_energy159.npy', energy)
energy_parts = parts(hist, 0, 159)
energy_tiles = [{'tile': t, 'sha256': sha(tile(hist, 159, t).tobytes()), 'opaque': int(np.count_nonzero(tile(hist, 159, t)))} for t in sorted({q['tile'] + q['page']*256 for q in energy_parts})]
relations = []
for form in ('after', 'before'):
    get = lambda n: a.layer(n)[0] if form == 'after' else full(a, n)[0]
    body = get(156)
    p157 = aura(shift(body, -1)); p158 = over(energy, shift(body, -10))
    relations.append({'form': form, '156_opaque': int(np.count_nonzero(body)),
                      '157_current156_yminus1_Chebyshev9_14': diff(p157, get(157), True),
                      '157_current_body_interior': diff(np.where(shift(body, -1)>0, p157, 0), np.where(shift(body, -1)>0, get(157), 0), True),
                      '158_current156_yminus10_over_historical159': diff(p158, get(158), True),
                      '158_external_source_energy': diff(np.where(shift(body, -10)==0, energy, 0), np.where(shift(body, -10)==0, get(158), 0), True),
                      '157_shifted_body_alpha_missing': int(np.count_nonzero((shift(body, -1)>0)&(get(157)==0))),
                      '157_external_index_counts': {str(v):int(c) for v,c in zip(*np.unique(get(157)[(shift(body,-1)==0)&(get(157)>0)],return_counts=True))},
                      '158_visible_energy_outside_body': int(np.count_nonzero((energy>0)&(shift(body,-10)==0))),
                      '156_vs_historical_normalized': diff(nb156, body),
                      '156_vs_historical_full': diff(full(hist, 156)[0], body)})

historical_guard = full(hist, 157)[1] == 0
old_pred157 = aura(shift(nb156, -1))
old_pred157[historical_guard] = hist.layer(157)[0][historical_guard]
post158 = over(energy, shift(full(hist, 156)[0], -10))
pre158_unclipped = over(energy, shift(nb156, -10))
pre158 = pre158_unclipped.copy(); pre158[post158 == 0] = 0
history = {
    '157_normalized156_yminus1_with_uncovered_original_base': diff(old_pred157, a.layer(157)[0], True),
    '157_guard_changed_vs_pure_aura': diff(aura(shift(nb156, -1)), old_pred157, True),
    '157_before_vs_historical_full': diff(full(hist, 157)[0], full(a, 157)[0], True),
    '158_normalized156_over_energy_clipped_to_historical_post_alpha': diff(pre158, a.layer(158)[0], True),
    '158_original_alpha_clipping_changes': diff(pre158_unclipped, pre158, True),
    '158_historical_full156_yminus10_over_energy': diff(post158, full(a, 158)[0], True),
    '157_overlay5_vs_current156_overlay5_yminus1': diff(shift(a.layer(156,5)[0],-1),a.layer(157,5)[0],True),
}

# Original US relations are measured separately: they are not artwork-production assertions.
us_relations = []
for form in ('base', 'full_armor'):
    get = lambda n: us.layer(n)[0] if form == 'base' else full(us, n)[0]
    for n, dy in ((157, -1), (158, -10)):
        moved = shift(get(156), dy); target = get(n)
        us_relations.append({'form': form, 'ref': n, 'tested_translation': [0, dy],
                             'body_interior': diff(np.where(moved>0, moved, 0), np.where(moved>0, target, 0)),
                             'whole_translation_only': diff(moved, target)})

# Read actual PS-X EXE bytes for the two return table aliases; no native execution.
mdpath = ROOT / 'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json'
md = json.loads(load(mdpath)); cfg = json.loads(load(ROOT / 'config/shibuki_x_us.json'))
exe = original['SLUS_005.61']; exe_base = cfg['executable']['load_address']
sequences = []
for q in md['animations']:
    if q['id'] not in (3, 40): continue
    address = struct.unpack_from('<I', exe, cfg['animation_table_address'] + q['id']*4 - exe_base + 2048)[0]
    assert address == int(q['address'], 16)
    steps = []
    for s in q['steps']:
        p = address + s['position']*4 - exe_base + 2048; code = exe[p:p+4]
        assert code.hex() == s['bytes']
        steps.append({'frame': s['frame'], 'duration_calls_uninterrupted': s['duration_calls_uninterrupted'], 'relative_step': s['relative_step'], 'bytes': code.hex()})
    sequences.append({'animation': q['id'], 'address': q['address'], 'steps': steps, 'original_exe_bytes_exact': True})

sheets = []
for form, mask in (('before', 15), ('after', 0)):
    ims = [a.composite(n, mask)[0] for n in REFS]
    boxes = [im.getchannel('A').getbbox() for im in ims]
    box = (min(b[0] for b in boxes)-2, min(b[1] for b in boxes)-2, max(b[2] for b in boxes)+2, max(b[3] for b in boxes)+2)
    w, h = box[2]-box[0], box[3]-box[1]; board = Image.new('RGB', (6*(w*3+10), h*3+32), '#263345'); dr=ImageDraw.Draw(board)
    for k, (n, im) in enumerate(zip(REFS, ims)):
        x = k*(w*3+10); dr.text((x+3, 4), f'{form} {n}', fill='white'); crop=im.crop(box).resize((w*3,h*3),Image.Resampling.NEAREST); board.paste(crop,(x,24),crop)
    path=O/f'{form}_156_161.png';board.save(path);sheets.append({'path':rel(path),'sha256':sha(path.read_bytes()),'no_clipping':True})

for p in ('scripts/overhaul_sprites_state_layers.py', 'scripts/ultimate_costume_swap.py'):
    load(ROOT/p)
for p, h in tracked.items(): assert sha((ROOT/p).read_bytes()) == h
report = {'scope':'시부키 현재 Ultimate 귀환156..161 실제 파생/효과/공유 읽기 조사', 'source': rel(source), 'source_sha256': sha(a.data),
          'original_US_arc_sha256': sha(us.data), 'original_US_exe_sha256': sha(exe), 'current_156_161_exact_to_b43e_parent': True,
          'frames': rows, 'current_formula_comparisons': relations, 'historical_reconstruction': history,
          'historical_energy159': {'opaque':int(np.count_nonzero(energy)), 'indexed_sha256':sha(energy.tobytes()), 'current159_exact':True, 'parts':energy_parts, 'whole_consumed_tiles':energy_tiles},
          'original_US_relations': us_relations, 'original_sequences': sequences, 'readbacks': sheets, 'readbacks_actually_viewed':False,
          'inputs':tracked, 'producer_functions_called':False, 'new_art_or_archive_written':False, 'runtime_verified':False,
          'limits':['기존 수용 그림의 파생 규칙과 원US 형상 관계는 별도다.', '새 원화에 역사 가림/알파 예외를 그대로 적용해야 한다는 결론이 아니다.', '기계 미리보기나 실제 게임을 실행하지 않았다.']}
(O/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()), 'formulas': relations, 'history':history},ensure_ascii=False))
