from pathlib import Path
import json, hashlib

D = Path(__file__).parent
ROOT = D.parents[2]
P = D.parent / 'nana_audit/ultimate_vehicle_repaint/common_probe_v2'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
v = {
 'scope': '나나 Ultimate 차량 common_probe_v2 두 비교판 실제 정적 열람 의견',
 'sheets': [{'path': str((P/n).relative_to(ROOT)).replace('\\','/'), 'sha256': sha(P/n), 'actually_viewed': True} for n in ('comparison_1.png','comparison_2.png')],
 'findings': [
  '162/166에서 목 아래 검정 상의와 맨팔이 연결되고 접힌 허벅지·무릎·발목에 새 확정 단절은 보이지 않았다. 166 낮게 접힌 다리는 원래 탑승 자세 범위로 읽히며 단순 전체축소처럼 보이지 않았다.',
  '170은 앞으로 내민 팔/상체와 무릎 아래 긴 다리가 이어지고, 174는 앞손/손목과 아래로 모인 두 신발이 구별된다. 네 자세의 머릿결과 피부 명암은 대기와 연결되는 방향이다.',
  '166/170의 팔 뒤·허리 쪽 작은 분홍 면은 bare donor에도 보인다. 이 판만으로 옛 소매 잔재라고 확정할 수 없으며 머리/허리 장식의 원화 의미 출처를 보존해야 한다.',
  '새 후폼에서 긴 밝은 소매선이 별도로 남거나 관절을 가로막는 추가 확정 결함은 찾지 못했다.'
 ],
 'new_confirmed_art_defect_found': False,
 'limits': ['두 판에 표시된 중간 후보에 대한 의견이며 ARC/부분층/원화 재구성/기술 독립감사를 실행한 결과가 아니다.', '차량 몸체 없이 본 정적 판이므로 실제 페달/손잡이/충돌 접점이나 게임 실행 검증으로 계산하지 않는다.', '픽셀 통과·최종 수용·전체 제작 완료를 주장하지 않는다.'],
 'producer_functions_called': False, 'resource_changed': False, 'runtime_verified': False
}
out = D / 'nana_ultimate_vehicle_common_v2_visual01.json'
out.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', 'utf8')
print(sha(out))
