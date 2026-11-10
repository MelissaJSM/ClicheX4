"""다음 대시 범위의 네 폼 실제12판 열람과 미완료 결함을 기록한다."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive
from native_pose_pack import need, sha, write

def main():
    d = H / 'dash_followup_audit01'
    out = d / 'visual_review.json'
    need(not out.exists(), 'Fresh result required')
    source = json.loads((d / 'report.json').read_text('utf8'))
    archives = [Archive((ROOT / p['path']).read_bytes()) for p in source['source_archives']]
    streak_rows = []
    for first, second in [(71, 73), (72, 74)]:
        p, q = [np.array(archives[0].composite(n, 0)[0]) for n in (first, second)]
        mask = np.any(p != q, axis=2)
        need(int(mask.sum()) == 54, 'Base speed-pattern difference changed')
        Image.fromarray(mask.astype(np.uint8) * 255).save(d / f'streak_{first}_{second}_mask.png')
        for form, m in [('ultimate_before', 15), ('ultimate_after', 0)]:
            p, q = [np.array(archives[1].composite(n, m)[0]) for n in (first, second)]
            excess = np.any(p != q, axis=2) & ~mask
            Image.fromarray(excess.astype(np.uint8) * 255).save(d / f'{form}_{first}_{second}_beyond_streak.png')
            streak_rows.append({'form': form, 'first': first, 'second': second, 'base_streak_mask_pixels': 54, 'different_body_pixels_outside_streak': int(excess.sum()), 'world_pixels': [[int(x - 160), int(y - 160)] for y, x in np.argwhere(excess)]})
    write(out, {'reviewed_sheets': {p: sha((ROOT / p).read_bytes()) for p in source['comparison_sheets']}, 'actual_view_image_count': 12, 'native_displays': 80, 'forms': ['base', 'fourth', 'ultimate_before', 'ultimate_after'], 'refs': [*range(67, 85), 93, 94], 'confirmed_style_gaps': [{'forms': '네 폼', 'refs': '67..84,93,94', 'finding': '대기와 이번 새공중보다 머리 상부가 큰 단색 덩어리이며 귀안쪽/머릿결·표정의 단계가 적다. 단순 머리크기 차이만을 문제삼은 것이 아니라 같은 라벤더 면 내부의 세부 표현 차이를 직접 보았다.'}, {'forms': '기본', 'refs': '67..84', 'finding': '등 뒤 소매가 길고 평평한 하늘색 판이며 대기 소매의 굴곡·옷깃 대비가 줄었다. 무릎 굽힘 자체는 정상 자세로 보존할 부분이다.'}, {'forms': '포스', 'refs': '68,70,72,76,78,80,84', 'finding': '발사 소매에 기본형과 유사한 밝은 하늘색 면이 남아 대기 검정/보라 의상과 이질감이 있다. 슬롯7은 실제 존재하므로 단순 빈 오버레이로 단정하지 않고 팔 소유/팔레트 및 새원화 의상 등록을 함께 검사해야 한다.'}, {'forms': 'Ultimate 전', 'refs': '67..84,93,94', 'finding': '대기 지퍼·칼라·금테 머리장식이 대시에서는 거의 없어지고 재킷이 큰 흰 면으로 뭉친다. 이전 하체 재질 복원으로 맨다리 색이 나아진 것과 세부 통일 완료는 구별한다.'}, {'forms': 'Ultimate 후', 'refs': '68,70,72,76,78,80,84', 'finding': '대기 맨팔과 달리 발사손 부근에 흰 소매/덩어리가 남고 총열 외곽도 프레임마다 들쑥날쑥하다. 새 앞팔과 동일한 수용총열 기준으로 교정할 대상이다.'}], 'new_sharing_findings': streak_rows, 'sharing_interpretation': '현 기본71→73 및72→74는54픽셀 속도선 차이이며 Ultimate 전은 그마스크 밖 동일하다. Ultimate 후는30/56픽셀이 더 다르므로 단순 속도선 차이라고 간주하면 안 된다. 새몸 제작 때 각원시파츠/원US 속도선의 가림순서를 확인한 뒤 같은몸+원속도선으로 재구성할 후보이다.', 'classification_correction': '93/94는 사격짝이 아니라 실제애니18/19에서 연속되는 공중대시 진입/종료 두자세이다.', 'first_body_keys_proposed': [67, 69, 71, 75, 77, 79, 81, 83, 93, 94], 'derived_frames_proposed': '73/74의 속도선·가림순서는 별도 보존; 나머지67..84 사격짝은 새몸 위 별도팔 제작.', 'all_motion_complete': False, 'new_art_or_resource_written': False, 'gameplay_validation': False})
    print({'reviewed_sheets': 12, 'confirmed_partial_after_body_differences': [r['different_body_pixels_outside_streak'] for r in streak_rows]})

if __name__ == '__main__':
    main()
