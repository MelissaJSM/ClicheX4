"""Read current Nana ladder graphics, compositions and prior original-code proof."""
from pathlib import Path
import collections
import hashlib
import json
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame, decode_stream, indexed_atlas, bank_offsets

D = Path(__file__).parent
OUT = D / 'nana_ultimate_ladder_relations01'
OUT.mkdir(exist_ok=True)
SOURCE = D.parent / 'nana_audit/ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC'
EXPECTED = '493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29'
PBS = (0, 5, 6, 7, 8)
REFS = list(range(143, 156)) + [183]
sha = lambda b: hashlib.sha256(b).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
data = SOURCE.read_bytes()
assert sha(data) == EXPECTED
a = Archive(data)

def bbox(mask):
    ys, xs = np.nonzero(mask)
    return [int(xs.min()-160), int(ys.min()-160), int(xs.max()+1-160), int(ys.max()+1-160)] if len(xs) else None

def mirror(v, k):
    out = np.zeros_like(v)
    m = v[:, :, 3] > 0 if v.ndim == 3 else v > 0
    ys, xs = np.nonzero(m)
    tx = 320 - xs + k
    assert np.all((tx >= 0) & (tx < 384))
    out[ys, tx] = v[ys, xs]
    return out

def delta(v, w):
    m = np.any(v != w, axis=2) if v.ndim == 3 else v != w
    av, aw = (v[:, :, 3] > 0, w[:, :, 3] > 0) if v.ndim == 3 else (v > 0, w > 0)
    return {'changed_pixels': int(m.sum()), 'changed_alpha_pixels': int(np.count_nonzero(av != aw)), 'bbox_world': bbox(m)}

def cp(n, pb):
    return composition_frame(a.c, pb, n)

def signature(n, pb):
    return [(p['flags'], p['tile'], p['x'], p['y']) for p in cp(n, pb)['parts']]

def frame_keys(n):
    f = a.banks[0]['frames'][n]
    return f['offset'], f['tile_count']

all_raw_owners = collections.defaultdict(list)
for gb, bank in enumerate(a.banks):
    for f in bank['frames']:
        all_raw_owners[(f['offset'], f['tile_count'])].append([gb, f['index']])

groups = []
for key in sorted(set(frame_keys(n) for n in REFS)):
    owners = all_raw_owners[key]
    f = next(a.banks[gb]['frames'][n] for gb, n in owners)
    raw = decode_stream(a.g, f['offset'], f['limit'], f['tile_count'] * 128)
    atlas = np.frombuffer(indexed_atlas(raw.data, f['tile_count'])[0], np.uint8).reshape(-1, 256)
    consumed = {}
    for gb, n in owners:
        if gb != 0:
            continue
        used = set()
        layers = {}
        for pb in PBS:
            ps = cp(n, pb)['parts']
            tiles = sorted({p['page'] * 256 + p['tile'] for p in ps})
            used.update(tiles)
            layers[str(pb)] = tiles
        consumed[str(n)] = {'layers': layers, 'union': sorted(used)}
    union = sorted(set(t for v in consumed.values() for t in v['union']))
    groups.append({'entry2_offset': key[0], 'tile_count': key[1], 'owners': owners,
                   'decoded_sha256': sha(raw.data), 'compressed_end': raw.end,
                   'consumed_tiles': consumed, 'whole_group_tile_union': union,
                   'unused_by_player5_layers': sorted(set(range(key[1])) - set(union)),
                   'tile_sha256': {str(t): sha(atlas[t//16*16:t//16*16+16, t%16*16:t%16*16+16].tobytes()) for t in union}})

frames = []
for n in REFS:
    f = a.banks[0]['frames'][n]
    layers = {}
    for pb in PBS:
        v = a.layer(n, pb)[0]
        ps = cp(n, pb)['parts']
        records = [p['record_offset'] for p in ps]
        owners = [m for m in range(cp(n, pb)['bank_frame_count'])
                  if [p['record_offset'] for p in cp(m, pb)['parts']] == records] if records else []
        layers[str(pb)] = {'parts': ps, 'exact_record_range_owners': owners,
                           'indexed_sha256': sha(v.tobytes()), 'opaque': int(np.count_nonzero(v)), 'bbox_world': bbox(v > 0)}
    frames.append({'ref': n, 'stream': f, 'layers': layers})

pairs = []
for s, t, expected_k in [(144, 145, -1), (146, 147, 0), (149, 148, 0), (151, 152, 0)]:
    layers = {}
    for pb in PBS:
        x, y = a.layer(s, pb)[0], a.layer(t, pb)[0]
        tests = [{'k': k, **delta(mirror(x, k), y)} for k in range(-3, 4)]
        layers[str(pb)] = {'exact_k': [x['k'] for x in tests if not x['changed_pixels']],
                           'expected_k_comparison': next(v for v in tests if v['k'] == expected_k),
                           'best': min(tests, key=lambda v: v['changed_pixels'])}
    forms = {}
    for mask, arm, label in [(0, 1, 'after'), (15, 1, 'before_arm1'), (15, 2, 'before_arm2')]:
        x = np.asarray(a.composite(s, mask, arm)[0]); y = np.asarray(a.composite(t, mask, arm)[0])
        forms[label] = delta(mirror(x, expected_k), y)
    pairs.append({'source': s, 'target': t, 'world_x_rule': f'-source_x{expected_k:+d}',
                  'same_raw_stream': frame_keys(s) == frame_keys(t), 'layers': layers, 'forms': forms})

shotcomparisons = []
for s, t in [(149, 150), (149, 155), (150, 155), (154, 155)]:
    forms = {}
    for mask, arm, label in [(0, 1, 'after'), (15, 1, 'before_arm1'), (15, 2, 'before_arm2')]:
        x = np.asarray(a.composite(s, mask, arm)[0]); y = np.asarray(a.composite(t, mask, arm)[0])
        forms[label] = delta(x, y)
    shotcomparisons.append({'source': s, 'target': t,
                            'same_raw_stream': frame_keys(s) == frame_keys(t),
                            'layers': {str(pb): delta(a.layer(s, pb)[0], a.layer(t, pb)[0]) for pb in PBS},
                            'forms': forms})

historic = ROOT / 'work/ver_rin_nana/nana_art/ladder_v1/production01'
meta = json.loads((historic / 'art.json').read_text('utf8'))
gunproof = []
for n in (150, 155):
    rec = next(q for q in meta['frames'] if q['frame'] == n)
    g = np.asarray(Image.open(historic / f'gun_{n:03}.png'))
    full = np.zeros((384, 384), np.uint8)
    full[120:200, 112:208] = g
    yy, xx = np.nonzero(full)
    edge = xx == xx.min()
    muzzle = [int(xx.min()-160), float(np.median(yy[edge])-160)]
    # Authored gun can be covered by body; report true overlap separately.
    vg = full > 0
    base = a.layer(n, 0)[0]
    mismatches = vg & (full != base)
    forms = {}
    for mask, arm, label in [(0, 1, 'after'), (15, 1, 'before_arm1'), (15, 2, 'before_arm2')]:
        rgba = np.asarray(a.composite(n, mask, arm)[0])
        gx, my = rec['original_muzzle_world']
        X, Y = np.meshgrid(np.arange(384)-160, np.arange(384)-160)
        roi = (X >= gx) & (X < gx+8) & (Y >= my-3) & (Y <= my+5)
        forms[label] = {'roi_world': [gx, my-3, gx+8, my+6], 'rgba_sha256': sha(rgba[roi].tobytes()),
                        'base_rgba_exact': bool(np.array_equal(rgba[roi], np.asarray(a.composite(n, 0, 1)[0])[roi]))}
    gunproof.append({'ref': n, 'source_image': rel(historic/f'gun_{n:03}.png'),
                     'source_sha256': sha((historic/f'gun_{n:03}.png').read_bytes()),
                     'historical_original_muzzle_world': rec['original_muzzle_world'],
                     'current_source_left_edge_world': muzzle, 'source_gun_opaque': int(vg.sum()),
                     'current_base_source_mismatches': int(mismatches.sum()),
                     'mismatch_bbox': bbox(mismatches), 'forms_first8column_window': forms})

sheets = []
def sheet(name, refs):
    crop = (112, 112, 208, 208); scale = 3; cw, ch = 306, 316
    board = Image.new('RGB', (cw*len(refs), ch*2), '#263345'); dr = ImageDraw.Draw(board)
    for row, mask in enumerate((15, 0)):
        for col, n in enumerate(refs):
            im = a.composite(n, mask, 2)[0].crop(crop).resize((288, 288), Image.Resampling.NEAREST)
            board.paste(im, (col*cw+8, row*ch+24), im)
            dr.text((col*cw+8, row*ch+5), f'current Nana {n} mask{mask}', fill='white')
    p = OUT / name; board.save(p)
    sheets.append({'path': rel(p), 'sha256': sha(p.read_bytes()), 'refs': refs, 'scale': scale, 'crop_world': [-48, -48, 48, 48]})

sheet('shots.png', [0, 149, 150, 155, 154])
sheet('mirror_a.png', [144, 145, 146, 147])
sheet('mirror_b.png', [149, 148, 151, 152])
shotold = D / 'ultimate_ladder_shots01/report.json'
mirrorold = D / 'ultimate_ladder_aliases01/report.json'
old = json.loads(shotold.read_text('utf8'))

# 레코드 완전범위뿐 아니라 부분주소 공유도 독립 수집한다.
record_sharing=[]
for pb in PBS:
 maps={n:{p['record_offset']for p in cp(n,pb)['parts']}for n in range(cp(0,pb)['bank_frame_count'])}
 for n in REFS:
  other=[m for m,addresses in maps.items()if m not in REFS and maps[n]&addresses]
  record_sharing.append({'ref':n,'bank':pb,'non_target_overlapping_refs':other})
outside=[]
Y,X=np.indices((384,384));Y-=160;X-=160
for target_ref in(150,155):
 for source_ref in(149,154):
  for mask,form in((0,'after'),(15,'before')):
   v=np.asarray(a.composite(source_ref,mask,2)[0]);w=np.asarray(a.composite(target_ref,mask,2)[0]);m=np.any(v!=w,axis=2)
   roi=(X>=-28)&(X<=5)&(Y>=-20)&(Y<=1)
   outside.append({'source':source_ref,'target':target_ref,'form':form,'outside_broad_arm_gun_ROI':int((m&~roi).sum()),'ROI_inclusive':[-28,-20,5,1],'difference':delta(v,w)})
for name,refs in(('body_a.png',[143,144,146,149]),('body_b.png',[151,153,154,183])):sheet(name,refs)
result={'scope':'현재 나나 Ultimate 사다리14: 5층·원시 공유·반전·사격 관계 읽기. 새원화/패킹/실기 검사 아님.',
 'source':rel(SOURCE),'source_sha256':EXPECTED,'graphics_groups':groups,'frames':frames,'mirror_pairs':pairs,
 'shooting_comparisons':shotcomparisons,'shooting_outside_broad_ROI':outside,'pistol_historical_PL00_source_comparison':gunproof,
 'non_target_record_sharing':record_sharing,'original_code_evidence':[{'path':rel(p),'sha256':sha(p.read_bytes())}for p in(shotold,mirrorold)],
 'original_92_93':old['sequences'][-2:],'sheets':sheets,'actual_sheet_views':False,'producer_functions_called':False,'runtime_verified':False,
 'limits':['PL00 제작정책을 현재 PL02의 동일성으로 가정하지 않았다.','gun150/155의 역사 PL00 출처 창은 위치 비교용이다. 현재 Ultimate 실제총이 그 원화와 같다는 주장은 mismatch 수가0일 때만 가능하다.','unused_by_player5_layers는 조사된 소비범위이며 삭제허용 목록이 아니다.']}
assert SOURCE.read_bytes()==data
(OUT/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((OUT/'report.json').read_bytes()),'groups':[{'owners':g['owners'],'tiles':g['tile_count']}for g in groups],'mirrors':[{'source':p['source'],'target':p['target'],'forms':p['forms'],'layer_changes':{k:v['expected_k_comparison']['changed_pixels']for k,v in p['layers'].items()}}for p in pairs],'shots':shotcomparisons,'outside':outside,'guns':gunproof,'non_target_record_sharing':[q for q in record_sharing if q['non_target_overlapping_refs']]},ensure_ascii=False))
