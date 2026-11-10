"""Final Nana running artwork and Shibuki UI beam visual review."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
W = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
folder = W / 'nana_audit/ultimate_run_repaint/packed_run_candidate_v1'
paths = [folder / f'readback_{i}.png' for i in range(1, 5)]
paths += [folder / f'timeline_{i}.png' for i in (7, 8, 38, 119, 120, 16, 128)]
paths += [W / 'selection_shibuki_beam13' / f'{s}.png' for s in ('before', 'after')]
record = {
    'art_review_images': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p),
                           'root_actually_viewed': True} for p in paths],
    'nana_candidate_sha256': sha(folder / 'PL02_U.ARC'),
    'selection_candidate_sha256': sha(W / 'selection_shibuki_beam13/ST0E_U1.ARC'),
    'findings': [
        '나나 Ultimate 이동1..32 최종 재추출4판 전부 직접 열람. 두 의상에서 새 머릿결/소매 주름/피부 중간톤이 대기 기준과 이어지고, 사격4/8 팔 아래 윤곽 개선이 실제 ARC에도 유지됨을 확인했다.',
        '원표7/8/38/119/120/16/128 순서7판을 직접 열람했다. 이동 순환과 대시 진입의 크기/머릿결 연결에서 추가 확정 절단을 찾지 못했다.',
        '시부키 UI23 빛기둥 수정 전/후를 직접 열람했다. 플레이용160과 같은 보라색 빛으로 바뀌었으며 독립 UI 원점 검증과 빌드 가드는 별도로 수행한다.'
    ],
    'limits': ['원순서 정적 패널 검토이며 실제 실행 영상을 본 것으로 대체하지 않는다.',
               '나나 새 이동32 및 시부키 UI23 실제 게임 재생은 아직 수행하지 않았다.'],
    'final_user_accepted': False
}
dest = W / 'root_review_checkpoint48.json'
body = json.dumps(record, ensure_ascii=False, indent=2) + '\n'
if dest.exists():
    assert dest.read_text('utf8') == body
else:
    dest.write_text(body, 'utf8')
print(json.dumps({'record': str(dest), 'images': len(paths), 'sha256': sha(dest)}))
