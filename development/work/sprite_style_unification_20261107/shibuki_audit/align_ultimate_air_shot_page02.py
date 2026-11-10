"""새 사격팔과 국소 머리 교정의 두 의상을 동일한 공통층으로 정합한다."""
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
    out = H / 'ultimate_air_shot_aligned03'
    need(not out.exists(), 'Fresh output required')
    a = Archive((H / 'prepared_rising_right_ultimate01/PL02_U.ARC').read_bytes())
    need(sha(a.data) == 'd636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d', 'Wrong parent')
    source = H / 'ultimate_air_shot_native02'
    local = H / 'ultimate_air_extra_arm_native01'
    need(json.loads((source / 'report.json').read_text('utf8'))['source_sha256'] == 'e4891163b53c0bd0fd7b12b87f8aff6c44e227e6c7447ea61cdf8da6b9d71fab', 'Wrong firing source')
    need(json.loads((local / 'report.json').read_text('utf8'))['source_sha256'] == '022b5439f066abe9bfd6b700983e78fad5d5e4617f3e1fd25db3fef041013a06', 'Wrong local source')
    colors = np.array([[(int(w) >> s & 31) * 255 // 31 for s in (0, 5, 10)] for w in a.words], np.int32)
    lut = np.r_[0, 1 + ((colors[17:32, None] - colors[None, 1:16]) ** 2).sum(2).argmin(1)].astype(np.uint8)
    out.mkdir()
    values, rows = {}, []
    for ref in (40, 42, 44):
        d = source if ref == 40 else local
        before = np.array(Image.open(d / f'before_{ref:03}_indices.png'))
        after = np.array(Image.open(d / f'after_{ref:03}_indices.png'))
        original = {'before': before.copy(), 'after': after.copy()}
        gun = np.array(Image.open(source / f'before_{ref:03}_barrel_mask.png')) > 0
        master = np.array(Image.open(H / 'ultimate_air_shot_inputs01' / 'barrels' / f'{ref:03}_indices.png'))
        common = np.zeros(before.shape, bool)
        if ref != 40:
            # Both outfits share the same exposed head. Use the new corrected
            # before drawing, never an old body/head or flat replacement fill.
            common = (np.array(Image.open(local / f'before_{ref:03}_local_mask.png')) > 0) & ~gun
            after[common] = lut[before[common]]
        # The edit rectangle overlaps several original gun texels. It is a
        # head-only correction: the accepted module always wins that overlap.
        before[gun] = master[gun]
        after[gun] = master[gun]
        outline = []
        for y, x in np.argwhere((after > 0) & (before == 0)):
            need(ref == 40 and [int(x - 160), int(y - 160)] in [[-12, -14], [-12, -8]] and int(after[y, x]) == 2, 'Unreviewed alpha excess')
            before[y, x] = after[y, x]
            outline.append([int(x - 160), int(y - 160), int(after[y, x])])
        need(not ((after > 0) & (before == 0)).any(), 'After alpha outside before')
        for form, v, pal in [('before', before, 16), ('after', after, 0)]:
            old = original[form]
            gun = np.array(Image.open(source / f'{form}_{ref:03}_barrel_mask.png')) > 0
            need(np.array_equal(v[gun], master[gun]), 'Accepted casing changed')
            need(np.array_equal(v[160:], old[160:]), 'Lower body changed')
            if ref != 40:
                need(np.array_equal(v[~(common | gun)], old[~(common | gun)]), 'Non-head body/arms changed')
            lab, _ = label(v > 0, np.ones((3, 3)))
            sizes = sorted(np.bincount(lab.ravel())[1:].tolist(), reverse=True)
            need(len(sizes) == 1, 'Disconnected target')
            Image.fromarray(v).save(out / f'{form}_{ref:03}_indices.png')
            a.rgba(v, pal).save(out / f'{form}_{ref:03}.png')
            values[form, ref] = v
            rows.append({'form': form, 'ref': ref, 'input_sha256': sha((d / f'{form}_{ref:03}_indices.png').read_bytes()), 'output_sha256': sha((out / f'{form}_{ref:03}_indices.png').read_bytes()), 'new_local_head_common': ref != 40, 'head_common_pixels': int(common.sum()), 'changed_pixels': int(np.count_nonzero(old != v)), 'local_edit_gun_overlap_restored': int(np.count_nonzero(old[gun] != v[gun])), 'source_outline_union': outline, 'connected_components': sizes, 'accepted34_casing_exact': True, 'lower_body_exact': True, 'older_head_pasted': False})
    for form, pal, mask in [('before', 16, 15), ('after', 0, 0)]:
        page([(f'{ref} firing / two arms', a.rgba(values[form, ref], pal)) for ref in (40, 42, 44)], a.composite(0, mask)[0], out / f'{form}_comparison.png', cols=3, scale=7)
    write(out / 'report.json', {'candidate_only': True, 'rows': rows, 'local_correction_visual_review': '교정 전후 두 판에서 잘못 남은 왼팔 제거 및 다른 두 팔/몸체 연결을 직접 확인했다. 전체 교정 원화는 자세가 달라 채택하지 않고 국소 머리 영역만 사용했다.', 'after_alpha_subset': True, 'old_three_arm_source_rejected': True, 'barrel_module_not_per_frame_legacy_casing': True, 'resource_written': False, 'actual_gameplay_test': False})
    print(json.dumps({'rows': len(rows), 'alpha_subset': True, 'all_connected': True}))

if __name__ == '__main__':
    main()
