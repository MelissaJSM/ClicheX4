"""추가 왼팔만 새 교정 원화에서 읽는다. 다른 두 팔/몸/원총열은 불변."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import label
from native_pose_pack import need, sha, write
from scripts.export_x_consistency import Archive, page

def main():
    d = H / 'ultimate_air_shot_extra_arm_edit01'
    src = d / 'generated.png'
    need(sha(src.read_bytes()) == '022b5439f066abe9bfd6b700983e78fad5d5e4617f3e1fd25db3fef041013a06', 'Wrong source')
    im = Image.open(src).convert('RGBA')
    need(im.size == (1254, 1254), 'Actual canvas changed')
    # Actual output is a uniformly scaled two-by-two canvas, not1024x1024.
    # Use each whole627x627 cell as native64x64; never fit the character bbox.
    small = np.array(im.resize((128, 128), Image.Resampling.NEAREST))
    a = Archive((H / 'prepared_rising_right_ultimate01/PL02_U.ARC').read_bytes())
    out = H / 'ultimate_air_extra_arm_native01'
    need(not out.exists(), 'Fresh output required')
    out.mkdir()
    boxes = {42: [-19, -30, -9, -13], 44: [-21, -25, -9, -12]}
    rows = []
    for row, (form, pal, mask) in enumerate([('before', 16, 15), ('after', 0, 0)]):
        colors = np.array([[(int(w) >> s & 31) * 255 // 31 for s in (0, 5, 10)] for w in a.words[pal:pal + 16]], np.int32)
        pics = []
        for col, ref in enumerate((42, 44)):
            px = small[row * 64:(row + 1) * 64, col * 64:(col + 1) * 64]
            q = (1 + ((px[:, :, :3].astype(np.int32)[:, :, None, :] - colors[None, None, 1:, :]) ** 2).sum(3).argmin(2)).astype(np.uint8)
            q[px[:, :, 3] < 128] = 0
            source = np.zeros((384, 384), np.uint8)
            source[124:188, 128:192] = q
            old = np.array(Image.open(H / 'ultimate_air_shot_native02' / f'{form}_{ref:03}_indices.png'))
            selected = np.zeros(old.shape, bool)
            x0, y0, x1, y1 = boxes[ref]
            selected[y0 + 160:y1 + 160, x0 + 160:x1 + 160] = True
            target = old.copy()
            target[selected] = source[selected]
            need(np.array_equal(target[~selected], old[~selected]), 'Other body/arms changed')
            skin_before = int(np.count_nonzero(np.isin(old, [10, 11, 12, 13]) & selected))
            skin_after = int(np.count_nonzero(np.isin(target, [10, 11, 12, 13]) & selected))
            labels, _ = label(target > 0, np.ones((3, 3)))
            components = sorted(np.bincount(labels.ravel())[1:].tolist(), reverse=True)
            for name, v in [('indices', target), ('whole_source_indices', source), ('local_mask', selected.astype(np.uint8) * 255)]:
                Image.fromarray(v).save(out / f'{form}_{ref:03}_{name}.png')
            a.rgba(target, pal).save(out / f'{form}_{ref:03}.png')
            pics.extend([(f'{ref} rejected third arm', a.rgba(old, pal)), (f'{ref} local source correction', a.rgba(target, pal)), (f'{ref} whole new source diagnostic', a.rgba(source, pal))])
            rows.append({'form': form, 'ref': ref, 'local_world_box_exclusive': boxes[ref], 'changed_pixels': int(np.count_nonzero(target != old)), 'extra_region_skin_before': skin_before, 'extra_region_skin_after': skin_after, 'components': components, 'outside_region_exact': True, 'both_true_arms_and_gun_exact': True, 'source_translated': [0, 0], 'whole_source_adopted': False})
        page(pics, a.composite(0, mask)[0], out / f'{form}_comparison.png', cols=3, scale=5)
    write(out / 'report.json', {'source_sha256': sha(src.read_bytes()), 'source_size_requested': [1024, 1024], 'source_size_actual': list(im.size), 'full_cell_registration_factor': 64 / 627, 'bbox_based_resizing': False, 'alpha_threshold': 128, 'rows': rows, 'candidate_only': True, 'visual_geometry_review_pending': True, 'resource_written': False})
    print(json.dumps(rows))

if __name__ == '__main__':
    main()
