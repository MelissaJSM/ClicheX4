"""첫3공중/사격쌍을 메모리에서만 패킹해 경계/32타일/비대상 보존을 시험."""
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
    out = H / 'ultimate_air_first_pairs_capacity01.json'
    need(not out.exists(), 'Fresh report only')
    parent = H / 'prepared_rising_right_ultimate01/PL02_U.ARC'
    data = parent.read_bytes()
    need(sha(data) == 'd636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d', 'Parent changed')
    core.PSHA = sha(data)
    core.SELECTED = set(range(33, 39))
    values = {}
    sources = []
    for form in ('before', 'after'):
        values[form] = {}
        for ref in sorted(core.SELECTED):
            folder = 'ultimate_air_shot_inputs01/bodies' if ref % 2 else 'ultimate_air_shot_aligned01'
            source = H / folder / f'{form}_{ref:03}_indices.png'
            values[form][ref] = np.array(Image.open(source))
            sources.append({'path': source.relative_to(ROOT).as_posix(), 'sha256': sha(source.read_bytes())})
    packed, report = core.pack(data, values['before'], values['after'])
    report.update({'test': '메모리 내 첫3몸체/사격쌍 패킹. 결과 ARC 파일은 쓰지 않음.', 'source_images': sources, 'in_memory_candidate_sha256': sha(packed), 'arc_written': False, 'full22_refs_not_checked': True, 'other8_pairs_not_ready': True, 'visual_or_gameplay_final_approval': False})
    write(out, report)
    print({k: report[k] for k in ('after_arc_sha256', 'parts_slack', 'raw_checked', 'non_target_raw_preserved', 'exact_target_composites')})

if __name__ == '__main__':
    main()
