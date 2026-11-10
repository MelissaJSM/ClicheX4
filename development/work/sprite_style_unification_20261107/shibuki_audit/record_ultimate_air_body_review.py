"""직접 열람한 새 공중 몸체22표시의 범위와 남은 사격 검증을 기록한다."""
from pathlib import Path
import sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write

def main():
    out = H / 'ultimate_air_body_visual_review01.json'
    need(not out.exists(), 'Fresh review required')
    paths = [H / 'ultimate_air_contacts02' / f'{form}_comparison_{i:02}.png' for form in ('before', 'after') for i in range(4)]
    paths.append(H / 'ultimate_air51_arm_registered01/comparison.png')
    write(out, {'reviewer': 'overhaul_ui', 'method': 'view_image로 아래9판 직접 열람; 수용 대기 옆 새 원화 고정배율 등록 비교', 'actually_viewed': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())} for p in paths], 'body_refs': list(range(33, 55, 2)), 'forms': ['ultimate_before', 'ultimate_after'], 'observations': [{'refs': [33, 35, 37], 'finding': '옛 머리 단색면·각진 피부 발덩어리보다 새 머릿결/선글라스·칼라·짧은 샌들 구분이 분명. 굽힌 무릎의 높이 변화는 원래 공중자세에 대응하며 정적 비교에서 새 몸 단절 없음.'}, {'refs': [39, 41, 43], 'finding': '팔을 머리 위로 드는 자세 유지.41의 이전 세 번째 손 원화 교정본을 사용하며 두 실제 손과 뒤 네이비 장식이 구별됨. 사격에서 앞팔만 내려야 하므로 추가팔 재발 검사가 필요.'}, {'refs': [45, 47, 49], 'finding': '머리·귀 외곽과 재킷 소매/옷단 세분화가 대기와 이어짐. 후폼은 맨팔을 유지하고 다리 정합에서 전체 몸 리사이즈를 하지 않음. 눈에 띄는 추가 관절 단절을 찾지 못함.'}, {'refs': [51], 'finding': '후폼의 반대팔이 전폼보다3px 내려간 원화 차이를 발견해 국소 새 원화38px로 수정. 최종 별도 판에서 가슴옆 주먹이 양폼 같은 높이로 연결됨. 외부 머리/몸/다리 exact, 알파가 재킷 안에 포함.'}, {'refs': [53], 'finding': '두 의상 주먹/팔꿈치 높이가 유사하고 붕 뜬 손이나 새 분리가 보이지 않아 임의 추가 재작화하지 않음.'}], 'accepted_for_following_shot_registration': True, 'only_body_art_review': True, 'shot_pairs_still_pending': list(range(34, 55, 2)), 'new_body_arc_packed': False, 'native_mips_test': False, 'actual_gameplay_test': False, 'all_style_unification_complete': False, 'user_accepted': False})
    print(out)

if __name__ == '__main__':
    main()
