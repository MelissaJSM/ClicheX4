"""새 부츠의 채색만 원래 접점/실루엣 안에 등록한다. 다른 신체는 원형 보존."""
from pathlib import Path
import sys, json, hashlib, struct
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.overhaul_sprites_audit import render, rgba
from scripts.prepare_riko_ui import entry

D = Path(__file__).resolve().parent / 'ground_boots21'
OUT = D / 'registered01'
OUT.mkdir(exist_ok=False)
info = json.loads((D / 'inputs.json').read_text('utf8'))
arc = (ROOT / info['parent']).read_bytes()
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(arc) == info['sha256']
pal = struct.unpack_from('<16H', entry(arc, 9))
colors = np.array([[(v >> s & 31) * 255 // 31 for s in (0, 5, 10)] for v in pal], np.int32)
im = Image.open(D / 'generated.png').convert('RGBA')
assert im.width / 192 == im.height / 288
a = np.array(im.resize((192, 288), Image.Resampling.NEAREST))
ix = 1 + ((a[:, :, None, :3].astype(np.int32) - colors[None, None, 1:, :]) ** 2).sum(3).argmin(2).astype(np.uint8)
ix[a[:, :, 3] < 128] = 0
rects = {62: [(144,173,159,183),(165,173,180,184)],
         63: [(141,173,155,183),(162,173,174,184)],
         65: [(144,173,157,183),(163,173,176,184)],
         82: [(143,173,158,183),(164,174,178,184)]}
targets = {}
rows = []
for i, n in enumerate([62, 63, 65, 82]):
    old = render(arc, 0, 0, n)[0]
    authored = np.zeros_like(old)
    authored[112:208, 112:208] = ix[i // 2 * 96:(i // 2 + 1) * 96, i % 2 * 96:(i % 2 + 1) * 96]
    region = np.zeros_like(old, bool)
    for x0, y0, x1, y1 in rects[n]:
        region[y0:y1, x0:x1] = True
    # These boots use the original cool-neutral material. Skin/cape/alpha are protected.
    neutral = [1, 3, 7, 12, 15]
    mask = region & np.isin(old, neutral) & np.isin(authored, neutral)
    out = old.copy()
    out[mask] = authored[mask]
    assert np.array_equal(out > 0, old > 0)
    assert np.array_equal(out[~region], old[~region])
    for label, data in [('indices', out), ('authored', authored), ('edit_mask', mask.astype('uint8') * 255)]:
        Image.fromarray(data).save(OUT / f'b0_{n:03}_{label}.png')
    p = OUT / f'b0_{n:03}_indices.png'
    rows.append(dict(bank=0, ref=n, target=str(p.relative_to(ROOT)), target_sha256=sha(p.read_bytes()),
                     native_translation=[0, 0], boot_material_regions=rects[n],
                     changed_pixels=int(np.count_nonzero(old != out)), silhouette_and_contacts_exact=True,
                     head_arms_skin_cape_exact=True, generated_pixels_applied_only_inside_original_boots=True))
    targets[n] = (old, authored, out)
for name, row in [('normal', 0), ('black', 13)]:
    palette = struct.unpack_from('<16H', entry(arc, 9), row * 32)
    sheet = Image.new('RGB', (1536, 400 * len(targets)), '#64717b')
    draw = ImageDraw.Draw(sheet)
    for j, (n, pictures) in enumerate(targets.items()):
        for c, (title, picture) in enumerate(zip(['idle', 'before', 'authored', 'local boots'],
                                               [render(arc, 0, 0, 147)[0], *pictures])):
            image = rgba(picture, palette).crop((112, 112, 208, 208)).resize((384, 384), Image.Resampling.NEAREST)
            sheet.paste(image, (c * 384, j * 400 + 16), image)
            draw.text((c * 384 + 4, j * 400 + 2), f'{n} {title}', fill='white')
    sheet.save(OUT / f'{name}_comparison.png')
(OUT / 'registration.json').write_text(json.dumps(dict(source_arc=info['parent'], source_sha256=sha(arc),
    generated_sha256=sha((D / 'generated.png').read_bytes()), uniform_scale=im.width / 192,
    frames=rows, candidate_only=True, game_applied=False), indent=2) + '\n', 'utf8')
print(json.dumps(rows))
