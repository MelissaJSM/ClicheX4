"""승리 네 자세의 붉은 외곽 인덱스만 기존 중성 윤곽색으로 교정한다."""
import argparse, json, struct, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion
from scripts.prepare_nana_fourth_pilot import entry, require, write
from scripts.prepare_nana_ultimate_shot_arm import D, full, pack_resources
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import sha256

PARENT = ROOT / 'out/ver_rin_nana/nana_ultimate_ceremony_20261104T105449575234Z'
PARENT_SHA = '5470afa3d7073a9733e7a34b5b4604652da35bc4794a381681aa26f26f703188'
ARC_SHA = 'c196227e1431960c4411d47e85a03bf2ff518c487d5139f298d9f78370d9fc92'
FRAMES = [204, 205, 206, 207]
GUNS = {206: [65, 68, 72, 77], 207: [58, 40, 74, 54]}
FACE = [73, 64, 83, 73]

def correction_mask(v, n):
    # Only the one-native-pixel outer shadow is changed: no palette mutation,
    # dilation, thinning, rescaling, inner shadows, or pink highlights.
    edge = (v > 0) & ~binary_erosion(v > 0, np.ones((3, 3), bool))
    mask = edge & (v == 5)
    for x, y, x2, y2 in [FACE] + ([GUNS[n]] if n in GUNS else []):
        mask[y:y2, x:x2] = False
    return mask

def prepare(out, art_only=False):
    out = out.resolve()
    require(out.is_relative_to(D) and not out.exists(), 'Fresh isolated output required')
    require(digest(PARENT / 'rin_nana.bin') == PARENT_SHA and digest(PARENT / 'PL02_U.ARC') == ARC_SHA, 'Parent changed')
    arc = (PARENT / 'PL02_U.ARC').read_bytes()
    words = struct.unpack_from('<16H', entry(arc, 9), 32)
    rgb = np.array([[(w >> s & 31)*255//31 for s in (0, 5, 10)] for w in words], np.uint8)
    out.mkdir()
    targets, records = {}, []
    board = Image.new('RGB', (1120, 880), '#46545c')
    draw = ImageDraw.Draw(board)
    for i, n in enumerate(FRAMES):
        before = full(arc, n)
        mask = correction_mask(before, n)
        after = before.copy()
        after[mask] = 1
        require(np.any(mask) and np.array_equal(before > 0, after > 0), 'Empty edit or silhouette change')
        require(np.array_equal(before[~mask], after[~mask]), 'Pixels changed outside rim')
        targets[n] = after
        save_image(after.tobytes(), (160, 160), words, out / f'ultimate_{n:03}.png')
        Image.fromarray((mask*255).astype(np.uint8)).save(out / f'edge_mask_{n:03}.png')
        records.append(dict(frames=[n, n], pistol_present=n in GUNS, pistol_mask_bbox=GUNS.get(n),
                            changed_pixels=int(mask.sum()), index_change=[5, 1],
                            changed_coordinates=[[int(x), int(y)] for y, x in np.argwhere(mask)],
                            silhouette_and_all_other_pixels_preserved=True))
        for row, v in enumerate((before, after)):
            rgba = np.concatenate((rgb[v], ((v > 0)*255).astype(np.uint8)[..., None]), axis=2)
            im = Image.fromarray(rgba).crop((54, 36, 98, 104)).resize((264, 408), Image.Resampling.NEAREST)
            x, y = i*280+8, row*440+24
            board.paste(im, (x, y), im)
            draw.text((x, y-18), ('BEFORE ' if row == 0 else 'AFTER ') + str(n), fill='white')
    board.save(out / 'victory_edge_before_after_6x.png')
    write(out / 'registration.json', records)
    if art_only:
        return
    result, packed = pack_resources(arc, targets, FRAMES)
    (out / 'PL02_U.ARC').write_bytes(result)
    write(out / 'recipe.json', dict(task='ultimate_armor_nana', kind='ultimate_victory_edge',
          parent_sha256=PARENT_SHA, parent_arc_sha256=ARC_SHA, frames=FRAMES,
          registration=records, **packed, files={'PL02_U.ARC': sha256(result)}, full_ultimate_complete=False))
    print(json.dumps(dict(output=str(out), sha256=sha256(result), changed_pixels=sum(r['changed_pixels'] for r in records))))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--art-only', action='store_true')
    a = p.parse_args()
    prepare(a.output, a.art_only)
