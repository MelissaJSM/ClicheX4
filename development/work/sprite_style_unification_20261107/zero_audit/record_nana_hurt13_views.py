"""Record the five independent native readback sheets actually inspected."""
from pathlib import Path
import hashlib
import json

D = Path(__file__).parent
ROOT = D.parents[2]
P = D / 'nana_hurt13_independent01/report.json'
j = json.loads(P.read_text('utf8'))
assert j['passed'] and j['candidate_sha256'] == '978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f'
assert len(j['new_readback_sheets']) == 5
for e in j['new_readback_sheets']:
    assert hashlib.sha256((ROOT / e['path']).read_bytes()).hexdigest() == e['sha256']
j['readback_actually_viewed'] = True
j['visual_review'] = {
    'method': 'view_image', 'boards': 5,
    'observations': [
        '106/110/233/234 양폼의 머리결·소매·치마·부츠가 기존 큰 면보다 분리되어 읽힌다. 이 정적판에서 새 목·무릎·손목 절단은 찾지 못했다.',
        '107/108/111의 원효과와 새 몸체 연결,109/112..114 새 몸체형 섬광의 대응을 실제 재독출판에서 확인했다.',
        '235/236 국소 정합 오라가 새 머리·모자 내부를 가르는 인상은 줄었다.236 뒤머리 아래 틈은 이전보다 넓지만 이 정적판에서 확정 부조화는 찾지 못했다.',
    ],
    'limits': [
        '기본/포스 정적 팔레트 미리보기다. 원게임 피격 중 특수 CLUT 교대·블렌딩·실제 화면은 검사하지 않았다.',
        '235/236의 빠른 교대에서 오라만 옆으로 흔들리는지는 별도 원표 재생·게임에서 판단해야 한다.',
        '원감긴눈과 새열린눈의 표정 차이는 앞선 원화 검토에서 따로 기록한 항목이며 이 기술 통과로 자동 승인하지 않는다.',
    ],
    'root_final_review': False, 'user_accepted': False,
}
P.write_text(json.dumps(j, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(hashlib.sha256(P.read_bytes()).hexdigest())
