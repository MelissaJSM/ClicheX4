"""새 9몸체/사격쌍의 손실 없는 고정 경계 패킹을 메모리에서 시험한다."""
from pathlib import Path
import sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
import pack_ultimate_lowhp as core
from native_pose_pack import need, sha, write

def main():
    out = H / 'ultimate_air_nine_pairs_capacity01.json'
    need(not out.exists(), 'Fresh report required')
    parent = H / 'prepared_rising_right_ultimate01/PL02_U.ARC'
    data = parent.read_bytes()
    need(sha(data) == 'd636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d', 'Parent changed')
    core.PSHA = sha(data)
    core.SELECTED = set(range(33, 51))
    values, source_files = {}, []
    for form in ('before', 'after'):
        values[form] = {}
        for ref in sorted(core.SELECTED):
            folder = 'ultimate_air_shot_inputs01/bodies' if ref % 2 else ('ultimate_air_shot_aligned01' if ref < 40 else 'ultimate_air_shot_aligned03' if ref < 46 else 'ultimate_air_shot_aligned04')
            source = H / folder / f'{form}_{ref:03}_indices.png'
            values[form][ref] = np.array(Image.open(source))
            source_files.append({'path': source.relative_to(ROOT).as_posix(), 'sha256': sha(source.read_bytes())})
    packed, report = core.pack(data, values['before'], values['after'])
    report.update({'source_images': source_files, 'arc_written': False, 'in_memory_sha256': sha(packed), 'last_two_pairs_pending': True, 'actual_gameplay_tested': False})
    write(out, report)
    print({k: report[k] for k in ('after_arc_sha256', 'parts_slack', 'raw_checked', 'non_target_raw_preserved', 'exact_target_composites')})

if __name__ == '__main__':
    main()
