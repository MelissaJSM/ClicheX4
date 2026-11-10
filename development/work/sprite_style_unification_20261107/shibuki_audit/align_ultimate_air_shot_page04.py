"""마지막 사격의 원팔 끝 잔점과 전후 외곽을 새 원화에 맞춰 정합한다."""
from pathlib import Path
import sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import label
from native_pose_pack import need, sha, write
from scripts.export_x_consistency import Archive, page

def main():
    out = H / 'ultimate_air_shot_aligned05'
    need(not out.exists(), 'Fresh output required')
    source = H / 'ultimate_air_shot_native04'
    need(sha((H / 'ultimate_air_shot_inputs01/page04/generated.png').read_bytes()) == '66cdf5c051c42b2445061a458b67cb5174f100ed3bc2c4a53321b95236604632', 'Source changed')
    a = Archive((H / 'prepared_rising_right_ultimate01/PL02_U.ARC').read_bytes())
    out.mkdir()
    rows, values = [], {}
    for ref in (52, 54):
        before = np.array(Image.open(source / f'before_{ref:03}_indices.png'))
        after = np.array(Image.open(source / f'after_{ref:03}_indices.png'))
        oldb = before.copy()
        if ref == 54:
            # One old bent-sleeve outline texel lies just outside the original
            # arm polygon. The new firing source is transparent here; adopt
            # that source at the exact coordinate, without painting a fill.
            x, y = -16 + 160, 6 + 160
            source_full = np.array(Image.open(source / 'before_054_source_indices.png'))
            body = np.array(Image.open(H / 'ultimate_air_shot_inputs01/bodies/before_053_indices.png'))
            arm = np.array(Image.open(source / 'before_054_arm_mask.png')) > 0
            need(before[y, x] == body[y, x] == 2 and not arm[y, x] and source_full[y, x] == 0, 'Residual provenance changed')
            lab, _ = label(before > 0, np.ones((3, 3)))
            need(np.count_nonzero(lab == lab[y, x]) == 1, 'Residual no longer isolated')
            before[y, x] = source_full[y, x]
        excess = [[int(x - 160), int(y - 160), int(after[y, x])] for y, x in np.argwhere((after > 0) & (before == 0))]
        need(excess == ({52: [[-14, -4, 15]], 54: []}[ref]), 'Unreviewed alpha excess')
        for x, y, v in excess:
            before[y + 160, x + 160] = v
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
            rows.append({'form': form, 'ref': ref, 'source_sha256': sha((source / f'{form}_{ref:03}_indices.png').read_bytes()), 'output_sha256': sha((out / f'{form}_{ref:03}_indices.png').read_bytes()), 'changed_pixels': int(np.count_nonzero(v != old)), 'outline_union': excess, 'old_bent_sleeve_residue_removed_from_new_source': [-16, 6] if form == 'before' and ref == 54 else None, 'barrel_exact': True, 'components': sizes})
        need(not ((after > 0) & (before == 0)).any(), 'After alpha outside before')
    for form, pal, mask in [('before', 16, 15), ('after', 0, 0)]:
        page([(f'{ref} native firing', a.rgba(values[form, ref], pal)) for ref in (52, 54)], a.composite(0, mask)[0], out / f'{form}_comparison.png', cols=2, scale=7)
    write(out / 'report.json', {'candidate_only': True, 'rows': rows, 'after_alpha_subset': True, 'visual_review': '네 등록 표시를 실제 열람했고 다른 손/머리/하체 유지, 원총열과 새 팔 연결을 확인했다.54 재킷의 원팔 끝 잔점1픽셀은 새 원화의 동일 좌표 투명을 등록했다.', 'arc_written': False, 'runtime_tested': False})
    print({'rows': len(rows), 'residual_1px_removed_from_source': True})

if __name__ == '__main__':
    main()
