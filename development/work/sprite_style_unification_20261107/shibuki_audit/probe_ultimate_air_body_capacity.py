"""공중 새몸체 두 층의32타일 하한 용량 조사. 사격 결합 성공을 의미하지 않는다."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from native_pose_pack import need, sha, write, crop, lossless_pack, same_rgba
from scripts.export_x_consistency import Archive
from src.psx_compress import encode_stream

def main():
    path = H / 'ultimate_air_body_capacity01.json'
    need(not path.exists(), 'Fresh report required')
    a = Archive((H / 'prepared_rising_right_ultimate01/PL02_U.ARC').read_bytes())
    d = H / 'ultimate_air_shot_inputs01/bodies'
    rows = []
    for n in range(33, 55, 2):
        before = np.array(Image.open(d / f'before_{n:03}_indices.png'))
        after = np.array(Image.open(d / f'after_{n:03}_indices.png'))
        need(not ((after > 0) & (before == 0)).any(), 'Body alpha mismatch')
        coat = np.where(same_rgba(a, before, after), 0, before).astype(np.uint8)
        raw, parts, method = lossless_pack([crop(after), crop(coat)])
        used = sorted({t for ps in parts for t, x, y, f in ps})
        rows.append({'ref': n, 'body_pixels': int(np.count_nonzero(after)), 'coat_pixels': int(np.count_nonzero(coat)), 'body_and_coat_tiles': len(used), 'used_tiles': used, 'parts': list(map(len, parts)), 'compression_bytes': len(encode_stream(raw)), 'method': method, 'sharing_shot_ref': n + 1, 'full_shot_pair_capacity_not_tested': True})
    write(path, {'parent_sha256': sha(a.data), 'rows': rows, 'body_layers_fit_32_tiles': True, 'shot_pair_shared_raw_not_tested': True, 'all_composition_banks_not_repacked': True, 'arc_written': False, 'not_an_art_or_game_pass': True})
    print(json.dumps(rows))

if __name__ == '__main__':
    main()
