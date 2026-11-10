"""새 공중 사격 앞팔만 고정 원점 등록; 머리/하체와 수용 총열은 보호."""
from pathlib import Path
import argparse, json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import label
from native_pose_pack import need, sha, write
from scripts.export_x_consistency import Archive, page
from register_air_shot_arms import arm_masks
from prepare_air_body_layers import rect

FACEBOX = {33: (-9, -13, 1, -4), 35: (-9, -13, 1, -4), 37: (-9, -14, 1, -4), 39: (-8, -16, 1, -5), 41: (-7, -16, 2, -5), 43: (-9, -15, 1, -5), 45: (-10, -13, 0, -3), 47: (-9, -13, 1, -3), 49: (-9, -13, 1, -3), 51: (-10, -9, 0, 1), 53: (-10, -10, 0, 0)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page', type=int, required=True, choices=(1, 2, 3, 4))
    ap.add_argument('--source-sha', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    d = H / 'ultimate_air_shot_inputs01'
    metadata = json.loads((d / 'manifest.json').read_text('utf8'))
    source_path = d / f'page{args.page:02}/generated.png'
    need(sha(source_path.read_bytes()) == args.source_sha, 'Generated source changed')
    out = (H / args.out).resolve()
    need(out.is_relative_to(H.resolve()) and out != H.resolve() and not out.exists(), 'Fresh owned output required')
    a = Archive((H / 'prepared_rising_right_ultimate01/PL02_U.ARC').read_bytes())
    need(sha(a.data) == metadata['parent_sha256'], 'Wrong parent')
    image = Image.open(source_path).convert('RGBA')
    need(image.size == (1536, 1024), 'Wrong source dimensions')
    cells = np.array(image.resize((192, 128), Image.Resampling.NEAREST))
    out.mkdir()
    refs = metadata['page_body_refs'][args.page - 1]
    rows = []
    values = {}
    for row, (form, mask, pal) in enumerate([('before', 15, 16), ('after', 0, 0)]):
        colors = np.array([[(int(w) >> s & 31) * 255 // 31 for s in (0, 5, 10)] for w in a.words[pal:pal + 16]], np.int32)
        pics = []
        for col, n in enumerate(refs):
            body_path = d / 'bodies' / f'{form}_{n:03}_indices.png'
            body = np.array(Image.open(body_path))
            px = cells[row * 64:(row + 1) * 64, col * 64:(col + 1) * 64]
            q = (1 + ((px[:, :, :3].astype(np.int32)[:, :, None, :] - colors[None, None, 1:, :]) ** 2).sum(3).argmin(2)).astype(np.uint8)
            q[px[:, :, 3] < 128] = 0
            source = np.zeros_like(body)
            source[124:188, 128:192] = q
            remove, add = arm_masks(n)
            face = rect(FACEBOX[n])
            patch = (remove | add) & ~face
            barrel = np.array(Image.open(d / 'barrels' / f'{n + 1:03}_indices.png'))
            guard = np.array(Image.open(d / 'barrels' / f'{n + 1:03}_mask.png')) > 0
            target = body.copy()
            target[patch] = source[patch]
            target[guard] = barrel[guard]
            allowed = patch | guard
            need(np.array_equal(target[~allowed], body[~allowed]), 'Non-arm body changed')
            need(np.array_equal(target[face & ~guard], body[face & ~guard]), 'Face changed')
            need(np.array_equal(target[guard], barrel[guard]), 'Gun changed')
            lab, _ = label(target > 0, np.ones((3, 3)))
            components = sorted(np.bincount(lab.ravel())[1:].tolist(), reverse=True)
            for suffix, v in [('indices', target), ('source_indices', source), ('arm_mask', patch.astype(np.uint8) * 255), ('head_face_guard', face.astype(np.uint8) * 255), ('barrel_mask', guard.astype(np.uint8) * 255), ('changed', (body != target).astype(np.uint8) * 255)]:
                Image.fromarray(v).save(out / f'{form}_{n + 1:03}_{suffix}.png')
            a.rgba(target, pal).save(out / f'{form}_{n + 1:03}.png')
            values[form, n] = target
            pics.extend([(f'{n} protected new body', a.rgba(body, pal)), (f'{n + 1} source arm registered', a.rgba(target, pal))])
            rows.append({'form': form, 'body_ref': n, 'shot_ref': n + 1, 'source_sha256': args.source_sha, 'body_source_sha256': sha(body_path.read_bytes()), 'fixed_scale': 0.125, 'source_translation': [0, 0], 'alpha_threshold': 128, 'body_outside_arm_exact': True, 'face_guard_exact': True, 'accepted34_barrel_exact': True, 'old_body_pasted': False, 'arm_stretched': False, 'changed_pixels': int(np.count_nonzero(target != body)), 'connected_components': components, 'visual_review_pending': True})
        page(pics, a.composite(0, mask)[0], out / f'{form}_comparison.png', cols=2, scale=6)
    outside = []
    for n in refs:
        leak = (values['after', n] > 0) & (values['before', n] == 0)
        Image.fromarray(leak.astype(np.uint8) * 255).save(out / f'{n + 1:03}_after_outside.png')
        outside.append({'ref': n + 1, 'count': int(leak.sum()), 'world': [[int(x - 160), int(y - 160), int(values['after', n][y, x])] for y, x in np.column_stack(np.nonzero(leak))]})
    write(out / 'report.json', {'candidate_only': True, 'source_path': source_path.relative_to(ROOT).as_posix(), 'source_sha256': args.source_sha, 'parent_sha256': sha(a.data), 'rows': rows, 'after_outside_before': outside, 'alpha_registration_and_common_arm_pending': True, 'extra_arm_and_joints_visual_review_pending': True, 'no_arc_written': True, 'actual_gameplay_test': False})
    print(json.dumps({'rows': rows, 'outside': outside}))

if __name__ == '__main__':
    main()
