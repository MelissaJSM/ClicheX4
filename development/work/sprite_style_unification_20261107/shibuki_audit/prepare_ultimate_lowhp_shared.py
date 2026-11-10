"""새 두 의상의 공통 머리·다리·손을 같은 원화의 재킷형에 맞춘다."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from scripts.export_x_consistency import Archive, page, metrics
from native_pose_pack import need, write, sha

P = H / 'prepared_run_complete03/PL02_U.ARC'
I = H / 'ultimate_lowhp_native02'
O = H / 'ultimate_lowhp_shared01'
P_SHA = 'c7eb1c7998a6780d04f4397a64af653265e3d83985c3c05768dd3de46eae5265'

def make():
    need(sha(P.read_bytes()) == P_SHA, 'Parent hash changed')
    a = Archive(P.read_bytes())
    before = np.array(Image.open(I / 'before_indices.png'))
    fresh_after = np.array(Image.open(I / 'after_indices.png'))
    need(before.shape == fresh_after.shape == (384, 384), 'Wrong native size')
    y, x = np.indices(before.shape)
    x, y = x - 160, y - 160
    # Both source forms contain the same head, side hair, tail and bare legs.
    # Canonicalize those actual new pixels; keep new after torso/forearms.
    common = (y <= -5) | (y >= 11) | ((x >= 8) & (y >= -4))
    # Exact new hand interiors, retaining the after's bare wrist/forearm.
    hand = ((x >= -5) & (x <= -4) & (y >= -4) & (y <= -2))
    hand |= ((x >= 6) & (x <= 8) & (y >= 7) & (y <= 10))
    common |= hand
    rgb = np.array([[(int(v) >> s & 31) * 255 // 31 for s in (0, 5, 10)] for v in a.words], np.int32)
    lut = np.r_[0, 1 + (((rgb[16:32][1:, None] - rgb[:16][None, 1:]) ** 2).sum(2)).argmin(1)].astype(np.uint8)
    after = fresh_after.copy()
    after[common] = lut[before][common]
    uncovered = (after > 0) & (before == 0)
    need(not uncovered.any(), 'After art cannot be erased by transparent coat')
    need(np.array_equal(after[~common], fresh_after[~common]), 'New after costume unexpectedly replaced')
    need(np.array_equal(before, np.array(Image.open(I / 'before_indices.png'))), 'New before source modified')
    info = {
        'parent_sha256': P_SHA,
        'source_art_sha256': 'aae841c4de541d42afc625288db6b9d29b7f70d554ad8c8ffd9f5ee3615c9a86',
        'source_before_indices_sha256': sha((I / 'before_indices.png').read_bytes()),
        'source_after_indices_sha256': sha((I / 'after_indices.png').read_bytes()),
        'before_unchanged': True,
        'common_geometry_alpha_exact': bool(np.array_equal(after[common] > 0, before[common] > 0)),
        'common_palette_mapping_16_to_0': lut.tolist(),
        'palette_approximation_indices': [i for i in range(1, 16) if not np.array_equal(rgb[16+i], rgb[lut[i]])],
        'new_common_opaque_pixels': int(np.count_nonzero(before[common])),
        'new_after_torso_forearm_pixels': int(np.count_nonzero(after[~common])),
        'after_pixels_changed_by_registration': int(np.count_nonzero(after != fresh_after)),
        'after_opaque_outside_before': int(uncovered.sum()),
        'old_lowhp_art_pixels_copied': 0,
        'body_resized': False,
        'foot_anchor_world': [-1, 22],
        'before_metrics': metrics(a.rgba(before, 16)),
        'after_metrics': metrics(a.rgba(after, 0)),
        'explanation': '새 재킷형의 머리·옆머리·꼬리·맨다리와 손 내부를 공통 앵커로 사용했다. 새 민소매 원화의 몸통·전완은 보존했다. 원 팔레트 1/4/11의 의상별 차이는 가장 가까운 기존 색으로 매핑하며 팔레트 자체는 수정하지 않는다.',
        'runtime_verified': False,
        'packed': False,
    }
    return a, before, after, common, info

if __name__ == '__main__':
    need(not O.exists(), 'Fresh output required')
    a, before, after, common, info = make()
    O.mkdir()
    for name, q, start, mask in (('before', before, 16, 15), ('after', after, 0, 0)):
        Image.fromarray(q).save(O / f'{name}_indices.png')
        a.rgba(q, start).save(O / f'{name}.png')
        page([('120 old', a.composite(120, mask)[0]), ('120 new shared', a.rgba(q, start))], a.composite(0, mask)[0], O / f'{name}_comparison.png', cols=2, scale=6)
    Image.fromarray(common.astype(np.uint8) * 255).save(O / 'shared_mask.png')
    page([('before jacket', a.rgba(before, 16)), ('after sailor', a.rgba(after, 0))], a.composite(0, 15)[0], O / 'pair.png', cols=2, scale=6)
    write(O / 'provenance.json', info)
    print(info)
