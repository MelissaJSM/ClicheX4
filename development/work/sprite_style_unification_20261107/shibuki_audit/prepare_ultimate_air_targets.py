"""22공중 참조의 최종 양의상 인덱스와 출처를 입력 전용 묶음으로 고정한다."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import label
from native_pose_pack import need, sha, write

def source_folder(ref):
    if ref % 2:
        return 'ultimate_air_shot_inputs01/bodies'
    return 'ultimate_air_shot_aligned01' if ref < 40 else 'ultimate_air_shot_aligned03' if ref < 46 else 'ultimate_air_shot_aligned04' if ref < 52 else 'ultimate_air_shot_aligned05'

def main():
    out = H / 'ultimate_air_targets02'
    need(not out.exists(), 'Fresh output required')
    parent = H / 'prepared_rising_right_ultimate01/PL02_U.ARC'
    need(sha(parent.read_bytes()) == 'd636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d', 'Wrong parent')
    out.mkdir()
    files, sources, rows = {}, {}, []
    source_names = set()
    for ref in range(33, 55):
        values = {}
        for form in ('before', 'after'):
            path = H / source_folder(ref) / f'{form}_{ref:03}_indices.png'
            v = np.array(Image.open(path))
            need(v.shape == (384, 384) and v.dtype == np.uint8 and v.max() < 16, 'Wrong target schema')
            lab, _ = label(v > 0, np.ones((3, 3)))
            sizes = sorted(np.bincount(lab.ravel())[1:].tolist(), reverse=True)
            need(len(sizes) == 1, f'Disconnected target {form}/{ref}')
            name = f'{form}_{ref:03}_indices.png'
            Image.fromarray(v).save(out / name)
            files[name] = sha((out / name).read_bytes())
            source_names.add(path.relative_to(H).as_posix())
            source_names.add(source_folder(ref) + ('/../manifest.json' if ref % 2 else '/report.json'))
            values[form] = v
            rows.append({'form': form, 'ref': ref, 'source': path.relative_to(ROOT).as_posix(), 'source_sha256': sha(path.read_bytes()), 'target_sha256': files[name], 'connected_pixels': sizes[0]})
        need(not ((values['after'] > 0) & (values['before'] == 0)).any(), f'Overlay erase impossible: {ref}')
        if not ref % 2:
            gun_path = H / 'ultimate_air_shot_inputs01/barrels' / f'{ref:03}_indices.png'
            guard_path = gun_path.with_name(f'{ref:03}_mask.png')
            gun = np.array(Image.open(gun_path)); mask = np.array(Image.open(guard_path)) > 0
            need(int(np.count_nonzero(gun)) == 60 and np.all(mask[gun > 0]), 'Wrong casing size')
            for v in values.values():
                need(np.array_equal(v[mask], gun[mask]), f'Casing target changed: {ref}')
            source_names.update([gun_path.relative_to(H).as_posix(), guard_path.relative_to(H).as_posix()])
    # These raw generated assets and registration records resolve the geometry
    # back to new artwork; none is an old body/head pasted over a new drawing.
    source_names.update(['ultimate_air_contacts02/report.json', 'ultimate_air51_arm_registered01/report.json', 'ultimate_air_shot_inputs01/manifest.json', 'ultimate_air_shot_extra_arm_edit01/generated.png', 'ultimate_air_extra_arm_native01/report.json', 'ultimate_air_shot_aligned03/report.json'])
    for pn in range(1, 5):
        source_names.add(f'ultimate_air_inputs01/page{pn:02}/generated.png')
        source_names.add(f'ultimate_air_shot_inputs01/page{pn:02}/generated.png')
        source_names.add(f'ultimate_air_shot_inputs01/page{pn:02}/prompt_used.txt')
    source_names.update(['ultimate_air41_extra_hand_edit01/generated.png', 'ultimate_air51_arm_edit01/generated.png'])
    for name in sorted(source_names):
        path = (H / name).resolve()
        need(path.is_relative_to(H.resolve()) and path.is_file(), f'Missing owned source {name}')
        sources[path.relative_to(H).as_posix()] = sha(path.read_bytes())
    write(out / 'LOCK.json', {'frozen_source_images': True, 'files': files, 'source_files': sources, 'targets': rows, 'refs': list(range(33, 55)), 'origin': [160, 160], 'canvas': [384, 384], 'parent_arc_sha256': sha(parent.read_bytes()), 'source_style': '수용대기 정밀도를 따른 새 전신과 새 사격팔. 구형 머리/몸 덮어쓰기 없음.', 'casing': '수용 PL02 after34의60픽셀 모듈을 각 원래 총구로 평행이동. 기존 각프레임의 찌그러진총열까지 동일하다는 주장은 하지 않음.', 'after_alpha_subset': True, 'scope': '22참조×2의상44표시; 전후 사격/비사격 원몸체 공유. 완성 전체모션/실기/사용자수용은 별도.', 'actual_gameplay_tested': False})
    print({'lock_sha256': sha((out / 'LOCK.json').read_bytes()), 'targets': len(files), 'source_files': len(sources)})

if __name__ == '__main__':
    main()
