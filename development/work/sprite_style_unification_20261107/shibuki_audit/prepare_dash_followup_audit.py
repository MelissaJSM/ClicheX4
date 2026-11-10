"""다음 대시 범위의 실제 네 폼·공유속도선·원애니메이션을 읽기만 한다."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from scripts.export_x_consistency import Archive, page
from src.psx_player import composition_frame
from native_pose_pack import need, sha, write

def main():
    out = H / 'dash_followup_audit01'
    need(not out.exists(), 'Fresh audit required')
    sources = [('PL00', H / 'prepared_rising_right_base01/PL00_U.ARC', '13a29023365419d32475cf5a6551adc4658116c8f03622d962d5b8071744e8b8'), ('PL02', H / 'prepared_ultimate_air01/PL02_U.ARC', '3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7')]
    out.mkdir()
    rows, shared, pictures = [], [], []
    refs = [*range(67, 85), 93, 94]
    for name, path, digest in sources:
        need(sha(path.read_bytes()) == digest, 'Wrong current resource')
        a = Archive(path.read_bytes())
        forms = [('base', 0), ('fourth', 15)] if name == 'PL00' else [('ultimate_after', 0), ('ultimate_before', 15)]
        for form, mask in forms:
            folder = out / form
            folder.mkdir()
            pics = []
            for ref in refs:
                im = a.composite(ref, mask)[0]
                im.save(folder / f'{ref:03}.png')
                pics.append((f'{ref} current / idle comparison', im))
                f = a.banks[0]['frames'][ref]
                aliases = [q['index'] for q in a.banks[0]['frames'] if q['offset'] == f['offset']]
                rows.append({'form': form, 'ref': ref, 'source_arc_sha256': digest, 'raw_aliases': aliases, 'png': (folder / f'{ref:03}.png').relative_to(ROOT).as_posix(), 'png_sha256': sha((folder / f'{ref:03}.png').read_bytes())})
            for i in range(0, len(pics), 8):
                image = folder / f'comparison_{i // 8:02}.png'
                page(pics[i:i + 8], a.composite(0, mask)[0], image, cols=4, scale=6)
                pictures.append(image.relative_to(ROOT).as_posix())
            for first, second in [(71, 73), (72, 74)]:
                p, q = [np.array(a.composite(n, mask)[0]) for n in (first, second)]
                body = p[:, :, 3] > 0
                diff = np.any(p != q, axis=2)
                shared.append({'form': form, 'first': first, 'second': second, 'difference_pixels': int(diff.sum()), 'differences_over_body': int((diff & body).sum()), 'second_only_pixels': int(((q[:, :, 3] > 0) & ~body).sum()), 'same_full_rgba': bool(np.array_equal(p, q))})
        for first, second in [(71, 73), (72, 74)]:
            p = composition_frame(a.c, 0, first)['parts']; q = composition_frame(a.c, 0, second)['parts']
            shared.append({'archive': name, 'first': first, 'second': second, 'composition_counts': [len(p), len(q)], 'prefix_records_equal': p == q[:len(p)], 'extra_records': q[len(p):]})
    anim_path = ROOT / 'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json'
    anim = json.loads(anim_path.read_text('utf8'))
    selected = [a for a in anim['animations'] if a['id'] in (16, 17, 18, 19, 128, 129)]
    write(out / 'report.json', {'source_archives': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': d} for _, p, d in sources], 'frames': rows, 'comparison_sheets': pictures, 'speed_streak_sharing': shared, 'animation_source': {'path': anim_path.relative_to(ROOT).as_posix(), 'sha256': sha(anim_path.read_bytes()), 'previous_native_table_validation': True}, 'animation_sequences': selected, 'classification': {'67_84': '지상대시/공중대시 본체와 사격짝.73/74는71/72+속도선 공유 여부를 실제 자원으로 조사.', '93_94': '사격짝 아님. 애니18 공중대시 진입93→94, 애니19 종료94→93의 별도몸체.', 'other_consumers': '81은승리/특수진입에도공유되어 후속패킹 때 해당연결 재검토 필요.'}, 'new_art_generated': False, 'resource_changed': False, 'visual_review_pending': True})
    print({'native_displays': len(rows), 'sheets': len(pictures), 'sharing': shared[:4]})

if __name__ == '__main__':
    main()
