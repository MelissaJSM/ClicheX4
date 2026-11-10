"""세 번째 사격 페이지의 같은 팔 외곽 두 픽셀을 두 의상에 공유한다."""
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
    out = H / 'ultimate_air_shot_aligned04'
    need(not out.exists(), 'Fresh output required')
    source = H / 'ultimate_air_shot_native03'
    need(json.loads((source / 'report.json').read_text('utf8'))['source_sha256'] == '54bc91e9d989a70fc7b8bb2b3d119d519568f0660560bc4ad0e86aaa2aa36f2e', 'Wrong source')
    a = Archive((H / 'prepared_rising_right_ultimate01/PL02_U.ARC').read_bytes())
    out.mkdir()
    rows, values = [], {}
    expected = {46: [], 48: [[-11, 4, 15]], 50: [[-8, -1, 15]]}
    for ref in (46, 48, 50):
        before = np.array(Image.open(source / f'before_{ref:03}_indices.png'))
        after = np.array(Image.open(source / f'after_{ref:03}_indices.png'))
        oldb = before.copy()
        excess = [[int(x - 160), int(y - 160), int(after[y, x])] for y, x in np.argwhere((after > 0) & (before == 0))]
        need(excess == expected[ref], 'Unreviewed alpha excess')
        for x, y, v in excess:
            before[y + 160, x + 160] = v
        need(not ((after > 0) & (before == 0)).any(), 'After alpha outside jacket')
        for form, v, pal in [('before', before, 16), ('after', after, 0)]:
            old = oldb if form == 'before' else after
            gun = np.array(Image.open(source / f'{form}_{ref:03}_barrel_mask.png')) > 0
            need(np.array_equal(v[gun], old[gun]), 'Gun changed')
            lab, _ = label(v > 0, np.ones((3, 3)))
            sizes = sorted(np.bincount(lab.ravel())[1:].tolist(), reverse=True)
            need(len(sizes) == 1, 'Disconnected target')
            Image.fromarray(v).save(out / f'{form}_{ref:03}_indices.png')
            a.rgba(v, pal).save(out / f'{form}_{ref:03}.png')
            values[form, ref] = v
            rows.append({'form': form, 'ref': ref, 'source_sha256': sha((source / f'{form}_{ref:03}_indices.png').read_bytes()), 'output_sha256': sha((out / f'{form}_{ref:03}_indices.png').read_bytes()), 'changed_pixels': int(np.count_nonzero(v != old)), 'new_after_outline_union': excess, 'barrel_exact': True, 'components': sizes})
    for form, pal, mask in [('before', 16, 15), ('after', 0, 0)]:
        page([(f'{ref} native firing', a.rgba(values[form, ref], pal)) for ref in (46, 48, 50)], a.composite(0, mask)[0], out / f'{form}_comparison.png', cols=3, scale=7)
    write(out / 'report.json', {'candidate_only': True, 'rows': rows, 'after_alpha_subset': True, 'visual_review': '두 원 등록 비교판을 실제 열람하여 새 앞팔과 원래 뒷팔, 머리·의상·하체가 이어짐을 확인했다. 새 맨팔의 검정 외곽 2픽셀만 재킷 공통층에 보탰다.', 'arc_written': False, 'runtime_tested': False})
    print({'rows': len(rows), 'new_outline_points': 2})

if __name__ == '__main__':
    main()
