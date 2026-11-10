"""공중 원래 총구 좌표와 실제 각 의상 케이싱을 읽어 비교한다."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive, page
from native_pose_pack import need, sha, write

def main():
    out = H / 'ultimate_air_barrels_probe01'
    need(not out.exists(), 'Fresh output required')
    out.mkdir()
    a = Archive((H / 'prepared_rising_right_ultimate01/PL02_U.ARC').read_bytes())
    meta = json.loads((H / 'ultimate_air_inputs01/manifest.json').read_text('utf8'))
    rows = []
    for form, mask, pal in [('before', 15, 16), ('after', 0, 0)]:
        pics = []
        for pair in meta['pairs']:
            n = pair['shot']
            mx, my = map(int, pair['original_muzzle_world'])
            box = [mx - 1, my - 3, mx + 9, my + 5]
            x0, y0, x1, y1 = box
            actual = a.composite(n, mask)[0]
            isolated = Image.new('RGBA', (384, 384))
            crop = actual.crop((x0 + 160, y0 + 160, x1 + 160, y1 + 160))
            isolated.alpha_composite(crop, (x0 + 160, y0 + 160))
            crop.resize((200, 160), Image.Resampling.NEAREST).save(out / f'{form}_{n:03}_crop.png')
            pics.extend([(f'{n} original complete', actual), (f'{n} muzzle window', isolated)])
            rows.append({'form': form, 'shot': n, 'body': n - 1, 'muzzle_world': [mx, my], 'window_world': box, 'window_rgba_sha256': sha(crop.tobytes()), 'opaque': int(np.count_nonzero(np.array(crop)[:, :, 3]))})
        for i in range(0, len(pics), 8):
            page(pics[i:i + 8], a.composite(0, mask)[0], out / f'{form}_{i // 8:02}.png', cols=2, scale=6)
    write(out / 'report.json', {'parent_sha256': sha(a.data), 'rows': rows, 'source_graphics_unchanged': True, 'rectangle_may_include_old_wrist_or_sleeve': True, 'not_final_protection_mask': True})

if __name__ == '__main__':
    main()
