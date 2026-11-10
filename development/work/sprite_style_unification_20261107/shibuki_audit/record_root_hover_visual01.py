"""Root 소유 호버 후보의 이미 제공된 재추출10판을 실제 열람한 별도 시각 기록."""
from pathlib import Path
import json
import sys

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write


def main():
    src = H.parent / 'root_shibuki_hover/packed_hover_candidate03'
    d = H / 'root_hover_visual01'
    need(not d.exists(), '시각 기록 보호')
    digest = sha((src / 'PL00_U.ARC').read_bytes())
    need(digest == '8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397', '검토 후보 변경')
    proof = json.loads((src / 'verification.json').read_text('utf8'))
    need(proof['after'] == digest, '제작자 재추출 결속')
    views = [src / f'readback_{n}.png' for n in range(221, 231)]
    d.mkdir()
    write(d / 'visual_review.json', {
        'scope': '시부키 기본/포스 호버의 Root 소유 최종 재추출10판을 UI 담당자가 직접 열람한 시각 의견. 별도 기술 reader나 재추출 실행은 아니다.',
        'observer': '/root/overhaul_ui', 'actually_viewed': True,
        'candidate': {'path': (src / 'PL00_U.ARC').relative_to(ROOT).as_posix(), 'sha256': digest},
        'producer_readback_proof': {'path': (src / 'verification.json').relative_to(ROOT).as_posix(), 'sha256': sha((src / 'verification.json').read_bytes())},
        'images': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())} for p in views], 'actual_images': 10,
        'findings': [
            '새 머릿결·땋은 부분·옷깃 및 기본 흰/붉은 소매와 포스 검보라 소매의 명암이 대기 기준과 이어진다. 대기 대비 갑자기 커진 머리나 몸통은 이10판에서 찾지 못했다.',
            '221/229는 두 높은 손이 읽히고222/230은 발사팔과 남은 높은 반대팔로 읽힌다. 이전의 추가 높은 손이 남아 세 팔로 보이는 확정 문제는 이 재추출판에서 발견하지 못했다.',
            '222/224의 손목과 버스터 뒤가 밝은 바탕에서 이어진다. 226/228은 총 아래로 접힌 팔꿈치→손목 연결이 보이며 새 투명 절단으로 읽히는 확정 공백을 발견하지 못했다.',
            '223/225/227의 접힌 무릎과 신발,229/230의 같은 굽힌 하체가 서로 이어진다. 공중 자세의 지지점이나 제트 접촉은 이 몸체판만으로 확정하지 않는다.'
        ],
        'new_confirmed_visual_defect': False,
        'limits': ['이10판은 Root 제작 재추출 이미지이며 이번 지원에서 ARC를 독립 디코드하거나 원화를 재구성하지 않았다.', 'HUD가 수행 중인50층/16저장순열·부분·GPU/원MIPS 독립 검사와 구분한다.', '제트15위상·발사점·탄환시간·실제 게임·부분아머 전수 미술 수용은 이 시각 의견의 범위 밖이다.'],
        'source_or_candidate_changed': False, 'new_image_generation': False, 'new_MIPS_execution': False, 'runtime_verified': False,
    })
    print(json.dumps({'report': str((d / 'visual_review.json').relative_to(ROOT)), 'sha256': sha((d / 'visual_review.json').read_bytes())}))


if __name__ == '__main__':
    main()
