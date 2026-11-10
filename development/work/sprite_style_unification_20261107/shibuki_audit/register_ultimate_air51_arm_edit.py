"""새51 몸체의 팔 관절 국소 원화만 등록하고 기존 새그림 외부를 보존한다."""
from pathlib import Path
import sys, json
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label
from scripts.export_x_consistency import Archive, page
from native_pose_pack import need, sha, write

def main():
    src = H / 'ultimate_air51_arm_edit01/generated.png'
    need(sha(src.read_bytes()) == '6c8747b31c02091d18a533c4b7971febc2818a23a33212c4ef5cbf1f9ddf652e', 'Wrong source')
    parent = H / 'prepared_rising_right_ultimate01/PL02_U.ARC'
    a = Archive(parent.read_bytes())
    need(sha(a.data) == 'd636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d', 'Wrong parent')
    out = H / 'ultimate_air51_arm_registered01'
    need(not out.exists(), 'Fresh output required')
    out.mkdir()
    im = Image.open(src).convert('RGBA')
    need(im.size == (1536, 1024), 'Wrong dimensions')
    cell = np.array(im.crop((768, 128, 1536, 896)).resize((64, 64), Image.Resampling.NEAREST))
    rgb = np.array([[(int(w) >> s & 31) * 255 // 31 for s in (0, 5, 10)] for w in a.words[:16]], np.int32)
    q = (1 + ((cell[:, :, :3].astype(np.int32)[:, :, None, :] - rgb[None, None, 1:, :]) ** 2).sum(3).argmin(2)).astype(np.uint8)
    q[cell[:, :, 3] < 128] = 0
    source = np.zeros((384, 384), np.uint8)
    source[124:188, 128:192] = q
    mask_image = Image.new('L', (384, 384))
    region = [(-2, -1), (3, -1), (5, 2), (8, 5), (8, 9), (3, 10), (-2, 6)]
    ImageDraw.Draw(mask_image).polygon([(x + 160, y + 160) for x, y in region], fill=255)
    mask = np.array(mask_image) > 0
    old = np.array(Image.open(H / 'ultimate_air_contacts02/after_051_indices.png'))
    before = np.array(Image.open(H / 'ultimate_air_contacts02/before_051_indices.png'))
    after = old.copy()
    after[mask] = source[mask]
    need(np.array_equal(after[~mask], old[~mask]), 'Outside local arm changed')
    need(not ((after > 0) & (before == 0)).any(), 'New bare arm exceeds jacket silhouette')
    labels, _ = label(after > 0, np.ones((3, 3)))
    components = sorted(np.bincount(labels.ravel())[1:].tolist(), reverse=True)
    need(len(components) == 1, 'Body disconnected')
    Image.fromarray(after).save(out / 'after_051_indices.png')
    a.rgba(after, 0).save(out / 'after_051.png')
    Image.fromarray(source).save(out / 'source_indices.png')
    mask_image.save(out / 'allowed_region.png')
    Image.fromarray((old != after).astype(np.uint8) * 255).save(out / 'changed_pixels.png')
    page([('51 jacket joint reference', a.rgba(before, 16)), ('51 old bare-arm joint', a.rgba(old, 0)), ('51 corrected local arm', a.rgba(after, 0))], a.composite(0, 0)[0], out / 'comparison.png', cols=3, scale=7)
    changed = np.column_stack(np.nonzero(old != after))
    write(out / 'report.json', {'passed': True, 'source': src.relative_to(ROOT).as_posix(), 'source_sha256': sha(src.read_bytes()), 'parent_sha256': sha(a.data), 'fixed_native_scale': 1 / 12, 'alpha_threshold': 128, 'local_region_world_polygon': region, 'changed_pixels': len(changed), 'changed_world': [[int(x - 160), int(y - 160), int(old[y, x]), int(after[y, x])] for y, x in changed], 'outside_region_exact': True, 'after_alpha_subset': True, 'connected_components': components, 'old_coarse_art_pasted': False, 'new_head_body_feet_outside_arm_exact': True, 'game_written': False, 'user_accepted': False})
    print(json.dumps({'changed': len(changed), 'connected': components, 'subset': True}))

if __name__ == '__main__':
    main()
