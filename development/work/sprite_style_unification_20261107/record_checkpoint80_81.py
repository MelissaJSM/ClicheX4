from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
items=[(80,[W/'shibuki_audit'/d/n for d in ('ultimate_ladder_native_page02','ultimate_ladder_native_page03') for n in ('before_comparison.png','after_comparison.png')],
 ['149/151/153 및154/183의 전후 의상4판을 직접 열람했다. 뒷머리·등/재킷의 새 분할을 유지하고 맨팔 후폼과 구분한다.',
  '154/183의 낮은 진입/이탈 자세를 서있는 대기의 높이로 일괄 늘리지 않는다. 자세와 스케일을 구분하여 접점을 검토한다.'],
 ['151 낮은 팔의 손끝이 수용 기준보다6px 아래인 것을 제작자가 확인해 국소 수정 중이다. 이 초안을 완성으로 수용하지 않는다.',
  '최종 파츠 공유·손발 좌표·사격150/155와 원순서 재생 검증은 남아 있다.']),
 (81,[W/'nana_audit/hurt_repaint/joint_layers_probe_v1'/n for n in ('comparison_1.png','comparison_2.png','partial_1.png','partial_2.png')]+[W/f'nana_audit/hurt_repaint/effect_probe_v1/comparison_{i}.png' for i in (1,2,3)],
 ['기본·포스/팔유형·일부 파츠 조합4판과 피격효과3판을 실제로 열람했다. 새 머리결·옷 주름이 조합에서도 유지되며 이번 판에서 새 목·무릎의 확정 절단은 찾지 못했다.',
  '107/108/111의 원추가 효과와109/112..114의 새몸 실루엣 표현을 구분하여 보았다.235/236의 기존 오라가 새 뒤머리/모자 외곽에 붙는 부분은 정합 미완료로 분류한다.'],
 ['부분파츠4판 열람이 전128조합의 직접 시각검사를 뜻하지 않는다.',
  '하체 검정 구역의 의미 확인과235/236 국소 오라 간격 수정 중이며 f823 진단 ARC를 최종 채택하지 않았다.',
  '원순서 재생·재현/거부·최종 독립 검사 및 실제 피격 검증은 남아 있다.'])]
for number,pages,findings,limits in items:
 r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
 'findings':findings,'limits':limits,'final_user_accepted':False}
 p=W/f'root_review_checkpoint{number}.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(number,sha(p))
