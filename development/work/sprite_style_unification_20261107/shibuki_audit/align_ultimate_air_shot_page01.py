"""첫 세 사격의 새 노출 머리/팔 외곽을 양 의상에서 동일하게 정합한다."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import label
from scripts.export_x_consistency import Archive, page
from native_pose_pack import need, sha, write

def main():
    out = H / 'ultimate_air_shot_aligned01'
    need(not out.exists(), 'Fresh output required')
    a = Archive((H / 'prepared_rising_right_ultimate01/PL02_U.ARC').read_bytes())
    d = H / 'ultimate_air_shot_native01'
    metadata = json.loads((d / 'report.json').read_text('utf8'))
    need(metadata['source_sha256'] == 'bdefbbcbf9abb2b182db565fc75d0061698af5c4f09e927e81f4442cc577e86f', 'Wrong arm source')
    colors = np.array([[(int(w) >> s & 31) * 255 // 31 for s in (0, 5, 10)] for w in a.words], np.int32)
    lut = np.r_[0, 1 + ((colors[17:32, None] - colors[None, 1:16]) ** 2).sum(2).argmin(1)].astype(np.uint8)
    out.mkdir()
    rows = []
    poses = {}
    for n in (34, 36, 38):
        before = np.array(Image.open(d / f'before_{n:03}_indices.png'))
        after = np.array(Image.open(d / f'after_{n:03}_indices.png'))
        oldb, olda = before.copy(), after.copy()
        common = []
        if n == 38:
            # The former raised forearm uncovered these two hair texels above
            # the firing arm. Same new drawing, same position, palette mapping.
            for x, y in [(-11, -19), (-13, -18)]:
                need(int(before[y + 160, x + 160]) in (4, 15), 'New exposed hair changed')
                after[y + 160, x + 160] = lut[before[y + 160, x + 160]]
                common.append([x, y, int(before[y + 160, x + 160]), int(after[y + 160, x + 160])])
        leaks = []
        for y, x in np.column_stack(np.nonzero((after > 0) & (before == 0))):
            need(int(after[y, x]) == 15, 'Unexpected new skin or clothing beyond jacket')
            before[y, x] = after[y, x]
            leaks.append([int(x - 160), int(y - 160), int(after[y, x])])
        expected = {34: [], 36: [[-17, -4, 15]], 38: [[-16, -4, 15], [-15, -4, 15]]}
        need(leaks == expected[n], 'Unexpected outline union')
        need(not ((after > 0) & (before == 0)).any(), 'After alpha outside jacket')
        for form, v, old, pal in [('before', before, oldb, 16), ('after', after, olda, 0)]:
            guard = np.array(Image.open(d / f'{form}_{n:03}_barrel_mask.png')) > 0
            need(np.array_equal(v[guard], old[guard]), 'Barrel changed')
            need(np.array_equal(v[160:], old[160:]), 'Waist/legs changed')
            lab, _ = label(v > 0, np.ones((3, 3)))
            sizes = sorted(np.bincount(lab.ravel())[1:].tolist(), reverse=True)
            need(len(sizes) == 1, 'Arm/body disconnected')
            Image.fromarray(v).save(out / f'{form}_{n:03}_indices.png')
            a.rgba(v, pal).save(out / f'{form}_{n:03}.png')
            poses[form, n] = v
            rows.append({'form': form, 'ref': n, 'input_sha256': sha((d / f'{form}_{n:03}_indices.png').read_bytes()), 'changed_pixels': int(np.count_nonzero(v != old)), 'connected_components': sizes, 'barrel_exact': True, 'waist_legs_exact': True, 'head_new_source_common_texels': common, 'common_arm_outline_added_to_jacket': leaks})
    for form, pal, mask in [('before', 16, 15), ('after', 0, 0)]:
        page([(f'{n} native aligned firing', a.rgba(poses[form, n], pal)) for n in (34, 36, 38)], a.composite(0, mask)[0], out / f'{form}_comparison.png', cols=3, scale=7)
    write(out / 'report.json', {'candidate_only': True, 'rows': rows, 'after_alpha_subset_all': True, 'source_head_common_only': True, 'new_art_overwritten_with_old': False, 'new_shots_have_two_arms_by_visual_review': True, 'resource_written': False, 'original_muzzle_preserved': True, 'barrel_module_source': 'PL02 after34 existing accepted module; per-ref previous malformed casing changes recorded separately', 'whole_air22_not_finished': True})
    print(json.dumps({'rows': len(rows), 'common_new_hair_texels': 2, 'common_outline_texels': 3}))

if __name__ == '__main__':
    main()
