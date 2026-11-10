"""Read-only coordinate evidence for the current Nana Ultimate 138/139 pair."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc

D = Path(__file__).parent
N = D.parent / 'nana_audit'
O = D / 'nana_ultimate_ceremony_sources02'
O.mkdir(exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
sources = {}

def get(p):
    data = p.read_bytes()
    sources[rel(p)] = sha(data)
    return data

path = N / 'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC'
a = Archive(get(path))
assert sha(a.data) == 'c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
old = Archive(get(ROOT / 'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC'))
disc, _ = read_disc(ROOT / 'MegaMan X4.bin', ('PL02_U.ARC',))
us = Archive(disc['PL02_U.ARC'])

def shift(v):
    z = np.zeros_like(v)
    z[:-1] = v[1:]
    return z

def full(ar, n):
    v = ar.layer(n)[0].copy()
    for pb in (8, 5, 7, 6):
        q = ar.layer(n, pb)[0]
        v[q > 0] = q[q > 0]
    return v

def bbox(m):
    y, x = np.nonzero(m)
    return [int(x.min()-160), int(y.min()-160), int(x.max()-159), int(y.max()-159)] if len(x) else None

def compare(x, y):
    m = x != y
    alpha = (x > 0) != (y > 0)
    return {'index_different': int(m.sum()), 'bbox_world': bbox(m),
            'alpha_different': int(alpha.sum()), 'alpha_bbox_world': bbox(alpha)}

layers = {}
for label, ar in [('current', a), ('historical_baseline', old), ('original_US', us)]:
    layers[label] = {str(pb): compare(shift(ar.layer(138, pb)[0]), ar.layer(139, pb)[0]) for pb in (0, 5, 6, 7, 8)}
    layers[label]['full'] = compare(shift(full(ar, 138)), full(ar, 139))

s = shift(a.layer(138)[0]); t = a.layer(139)[0]; m = s != t
yy, xx = np.indices(m.shape)
cells = [{'x': int(x-160), 'y': int(y-160), 'shifted138': int(s[y,x]), 'current139': int(t[y,x])}
         for y, x in zip(*np.nonzero(m))]
row_spans = []
for y in np.flatnonzero(m.any(axis=1)):
    xs = np.flatnonzero(m[y])
    row_spans.append({'y': int(y-160), 'xs': (xs-160).tolist(), 'count': len(xs)})

regional = []
for name, y0, y1 in [('head_ear_face', -34, -14), ('neck_shoulders_upper_chest', -14, -5), ('lower_chest_waist', -5, 5), ('legs_and_shoes', 5, 25)]:
    region = (yy >= y0+160) & (yy < y1+160)
    regional.append({'coordinate_band_label': name, 'world_y_interval': [y0,y1],
                     'changed': int(np.count_nonzero(region&m)),
                     'alpha_changed': int(np.count_nonzero(region&((s>0)!=(t>0)))),
                     'bbox': bbox(region&m)})

crop = (140,126,188,186)
cw, ch = 400, 510
board = Image.new('RGB', (cw*4,ch*2), '#bac5cb'); dr = ImageDraw.Draw(board)
for row, (form, u, v) in enumerate([('after',s,t),('before',shift(full(a,138)),full(a,139))]):
    change = u != v
    old_only = np.where(change,u,0).astype(np.uint8)
    new_only = np.where(change,v,0).astype(np.uint8)
    for col,(title,arr) in enumerate([('138 y-1',u),('139',v),('changed old colors',old_only),('changed new colors',new_only)]):
        im=a.rgba(arr,16 if form=='before' else 0).crop(crop).resize((384,480),Image.Resampling.NEAREST)
        x,y=col*cw+8,row*ch+24;board.paste(im,(x,y),im)
        dr.text((col*cw+8,row*ch+5),f'{form} {title}',fill='black')
        if col<2:
            for yworld in (-14,-5,5):
                py=y+(yworld+160-crop[1])*8
                dr.line((x,py,x+383,py), fill='#557783',width=1)
                dr.text((x+2,py+1),f'y={yworld}',fill='#446570')
board.save(O/'current_pair_diff.png')

# A historical source assertion is evidence of a former creation policy, not proof of the US pose.
for f in ('scripts/prepare_nana_ultimate_ceremony.py','scripts/normalize_nana_arrival.py'):
    get(ROOT/f)

report = {'scope':'현재 나나 Ultimate 138→139의 world y−1 관계를 좌표별로 분해한 읽기 보충 자료. 제작/게임 실행 없음.',
          'source_hashes':sources, 'original_US_PL02_sha256':sha(disc['PL02_U.ARC']),
          'parent_report':'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ceremony_sources01/report.json',
          'parent_report_sha256':sha((D/'nana_ultimate_ceremony_sources01/report.json').read_bytes()),
          'comparisons':layers, 'after_different_cells':cells, 'row_spans':row_spans,
          'coordinate_bands':regional,
          'index_transitions':[{'from':int(i),'to':int(j),'count':int(c)} for (i,j),c in collections.Counter(zip(s[m],t[m])).most_common()],
          'body_below_y5_exact':bool(np.array_equal(s[165:],t[165:])),
          'image':rel(O/'current_pair_diff.png'), 'image_sha256':sha((O/'current_pair_diff.png').read_bytes()),
          'actual_visual_review':False,
          'limits':['좌표 대역 이름은 임시 시각 구분이며 자동 의미 마스크가 아니다.','현재 그림 동일성과 원US 자세 동일성을 별도로 기록했다.']}
for p,h in sources.items():assert sha((ROOT/p).read_bytes())==h
(O/'coordinate_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha':sha((O/'coordinate_report.json').read_bytes()),'comparisons':layers,'bands':regional},ensure_ascii=False))
