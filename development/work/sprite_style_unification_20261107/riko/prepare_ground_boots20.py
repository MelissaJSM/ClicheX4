"""지상 공격 부츠의 원형·접점을 보호하는 국소 상세 보완 입력."""
from pathlib import Path
import sys, json, hashlib, struct
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.overhaul_sprites_audit import render, rgba
from scripts.prepare_riko_ui import entry

D = Path(__file__).resolve().parent / 'ground_boots20'
D.mkdir(exist_ok=False)
P = D.parent / 'prepared_ground_boots_v2/PL01_U.ARC'
arc = P.read_bytes()
sha = hashlib.sha256(arc).hexdigest()
assert sha == 'ff9108b32b580bd6e4974970bb1df70e5974cd907bf0573d213d1bd3311b94d4'
pal = struct.unpack_from('<16H', entry(arc, 9))
crop = (112, 112, 208, 208)
refs = [62, 63, 65, 67, 147, 17]
sheet = Image.new('RGBA', (1536, 2304))
rows = []
for i, n in enumerate(refs):
    indices = render(arc, 0, 0, n)[0]
    image = rgba(indices, pal)
    image.save(D / f'b0_{n:03}_source.png')
    Image.fromarray(indices).save(D / f'b0_{n:03}_indices.png')
    sheet.paste(image.crop(crop).resize((768, 768), Image.Resampling.NEAREST),
                (i % 2 * 768, i // 2 * 768))
    rows.append(dict(bank=0, ref=n, cell=i, locked=i >= 4))
sheet.save(D / 'targets.png')
prompt = '''Edit the TOP FOUR sprites ONLY in this transparent 2-column, 3-row pixel-art game sheet. BOTTOM TWO sprites are locked finished idle/running style references. This is a tiny LOCAL BOOT DETAIL repair, NOT a redesign. Riko has short fine green hair, a fitted white jacket and skirt, attached teal-lined cape, and white knee-high boots. ALL heads, faces, arms, hands, torso, cape, skin, thighs and poses in the top four are already final and must be unchanged. Refine ONLY the large flat white areas of the boots: add crisp, economical cool gray/navy pixel clusters for shin panels, knee cuff seams, ankle folds, heel and toe planes, matching the lower two references. Preserve the exact outer boot silhouette, sole and toe locations, leg thickness and knees. Do NOT enlarge feet or shorten legs. Keep light edges light and use thin selective dark outlines, never a heavy black border. Do not add ornaments, straps, armor, glows, particles or weapons. No blur, no anti-aliasing. Each cell represents96x96 native pixels enlarged8x. Keep every native pixel grid, position, sprite scale and the transparent background. Four top boot-detail edits with everything else locked.'''
(D / 'prompt.txt').write_text(prompt, 'utf8')
(D / 'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)), sha256=sha,
    native_cell=[96, 96], grid=[2, 3], crop=crop, frames=rows, apply_only_keys=[[0, n] for n in refs[:4]],
    detail_only_boots=True, shared_region_proof='riko/ground_detail_analysis18/analysis.json',
    gameplay_unchanged=True), indent=2) + '\n', 'utf8')
print(D)
