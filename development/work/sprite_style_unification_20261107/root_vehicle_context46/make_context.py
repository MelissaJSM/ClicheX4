"""과거 실제 조종석 몸체와 최신 머리를 결합하는 정적 크기 검토. 실기 아님."""
from pathlib import Path
import ast
import gzip
import hashlib
import json
import struct
import sys
import numpy as np
from PIL import Image, ImageDraw

O = Path(__file__).resolve().parent
W = O.parent
ROOT = W.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.build_sprite_style_album import zero_palettes, zero_image
from scripts.overhaul_sprites_audit import render, rgba
from scripts.prepare_riko_ui import entry
from src.epsxe_state import framebuffer

sha = lambda b: hashlib.sha256(b).hexdigest()
inputs = {}

def read(p):
    b = p.read_bytes()
    inputs[p.relative_to(ROOT).as_posix()] = sha(b)
    return b

def js(p):
    return json.loads(read(p))

def artifact(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())}

assert not (O / 'context_manifest.json').exists()
old_dir = W / 'zero_audit/rin_extension/ride_cockpit_review01'
old_meta = js(old_dir / 'context_manifest.json')
state_path = ROOT / 'work/ver_rin_nana/checkpoints/ride_armor_accepted_20261029T005856936087Z/accepted_ride_armor/SLUS_005.61.000'
packed = read(state_path)
assert sha(packed) == old_meta['source_state_sha256'] == 'a07e488ce7ed48a69af7d5175e7f16794e2c2a196810d395ab71a5ac78fdbf46'
s = gzip.decompress(packed)
ram = s[442:442+2097152]
vram = np.frombuffer(s, dtype='<u2', count=524288, offset=2569183).reshape(512, 1024)
source = read(W / 'zero_audit/compose_ride_cockpit.py').decode('utf8')
tree = ast.parse(source)
defs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('pal', 'parts', 'draw')]
assert len(defs) == 3
ns = {'np': np, 'struct': struct, 'ram': ram, 'vram': vram}
exec(compile(ast.Module(body=defs, type_ignores=[]), '<read-only historical body renderer>', 'exec'), ns)
body = Image.fromarray(ns['draw'](0, 384, 0, 'x', False, (576, 128)))
assert np.array_equal(np.array(body), np.array(Image.open(old_dir / 'native_body.png').convert('RGBA')))
read(old_dir / 'native_body.png')

# Reproduce the previously exact historical scene; this does not run the new game.
old_arc = read(W / 'zero_audit/rin_extension/prepared_bank1_recovery128/PL01_U.ARC')
words = struct.unpack_from('<16H', entry(old_arc, 9))
head = rgba(render(old_arc, 1, 5, 66)[0], words).crop((96, 96, 224, 224))
combined = np.array(Image.alpha_composite(body, head))
screen = np.array(framebuffer(s, 2569183, 0))[85:213, 96:224]
m = combined[:, :, 3] > 0
assert int(m.sum()) == 2498 and np.all(combined[:, :, :3][m] == screen[m])

plans = {tag: js(W / f'staging_{tag}.json') for tag in ('br_v30', 'br_v31', 'rn_v43')}
arcs = {}
for tag, plan in plans.items():
    arcs[tag] = {}
    for name in ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC'):
        source = plan['resources'][name]
        blob = read(ROOT / source['path'])
        assert sha(blob) == source['after']
        arcs[tag][name] = blob

def x_head(tag, form, ref):
    name = 'PL02_U.ARC' if form.startswith('ultimate') else 'PL00_U.ARC'
    mask = 15 if form in ('fourth', 'ultimate_before') else 0
    return Archive(arcs[tag][name]).composite(ref, mask)[0].crop((96, 96, 224, 224))

def zero_head(tag, form):
    blob = arcs[tag]['PL01_U.ARC']
    return zero_image(blob, 'riko' if tag == 'br_v31' else 'rin',
                      {'id': form + ':b1_066', 'form': form, 'bank': 1, 'ref': 66},
                      zero_palettes(blob)).crop((96, 96, 224, 224))

pages = []
sheet = Image.new('RGB', (1024, 1168), '#26313f')
d = ImageDraw.Draw(sheet)
rows = []
for y, form in enumerate(('base', 'fourth', 'ultimate_before', 'ultimate_after')):
    for x, (tag, ref) in enumerate((('br_v30', 184), ('br_v31', 184), ('br_v30', 196), ('br_v31', 196))):
        h = x_head(tag, form, ref)
        im = Image.alpha_composite(body, h)
        d.text((x * 256 + 4, y * 292 + 4), f'{form} / {tag} / head {ref}', fill='white')
        d.text((x * 256 + 4, y * 292 + 18), 'STATIC mech0 context; not live pair', fill='#d4cf8a')
        pic = im.resize((256, 256), Image.Resampling.NEAREST)
        sheet.paste(pic, (x * 256, y * 292 + 36), pic)
        rows.append({'form': form, 'tag': tag, 'ref': ref, 'head_bbox': h.getbbox(), 'composite_rgba_sha256': sha(im.tobytes())})
p = O / 'shibuki_before_after_static.png'
sheet.save(p)
pages.append(artifact(p))

sheet = Image.new('RGB', (1024, 876), '#26313f')
d = ImageDraw.Draw(sheet)
cases = []
for name, tag in (('riko', 'br_v31'), ('rin', 'rn_v43')):
    for form in ('normal', 'black'):
        cases.append((name, form, zero_head(tag, form)))
for name, tag in (('shibuki', 'br_v31'), ('nana', 'rn_v43')):
    for form in ('base', 'fourth', 'ultimate_before', 'ultimate_after'):
        cases.append((name, form, x_head(tag, form, 184)))
for i, (name, form, h) in enumerate(cases):
    x, y = i % 4 * 256, i // 4 * 292
    im = Image.alpha_composite(body, h)
    d.text((x + 4, y + 4), f'{name} / {form}', fill='white')
    d.text((x + 4, y + 18), 'STATIC native origin; not live test', fill='#d4cf8a')
    pic = im.resize((256, 256), Image.Resampling.NEAREST)
    sheet.paste(pic, (x, y + 36), pic)
p = O / 'four_characters_current_static.png'
sheet.save(p)
pages.append(artifact(p))

report = {
    'scope': '보존 상태에서 정확히 재구성한 원작 조종석 몸체0에 최신 머리의 원좌표를 놓은 정적 미술 검토.',
    'inputs': inputs,
    'historical_rin_scene_opaque_exact': 2498,
    'historical_body_rgba_exact_to_saved_proof': True,
    'body_native_origin': [64, 64],
    'head_source_window': [96, 96, 224, 224],
    'head_native_origin': [64, 64],
    'head_or_body_pixels_repainted': False,
    'latest_head_current_gameplay_verified': False,
    'rows': rows,
    'pages': pages,
    'actually_viewed': False,
    'limits': [
        '과거 린66+몸체0의2498불투명 픽셀만 당시 화면과 exact 검증했다. 최신 머리를 실제 게임에서 띄운 증거가 아니다.',
        '모든 셀에 동일한 몸체0를 사용한다.196 등은 해당 실제 차량 동작과의 정확한 쌍이 아니라 크기/가림 위치 비교다.',
        '차량 움직임·손잡이/발판·호출자의 임시 파츠 마스크·실제 GPU 순서를 실행하지 않는다.',
        '기본/포스/Ultimate 전후는 현재 렌더 정책의마스크0/15를 사용한다. 빈198은 앞서 별도 보존검사를 통과했고 이 비교판에서 채워 넣지 않는다.',
    ],
}
(O / 'context_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'historical_exact_pixels': 2498, 'pages': len(pages), 'current_forms': len(cases), 'gameplay_verified': False}))
