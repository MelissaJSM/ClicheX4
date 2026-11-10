from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pages=[W/'shibuki_audit/base_run_shot_page01_registered02'/f'{x}_comparison.png' for x in ('base','fourth')]
pages += [W/'nana_audit/rising_repaint/canonical_weapon_probe_v2'/f'comparison_{i}.png' for i in (1,2,3)]
pages += [W/'nana_audit/rising_repaint/body_contacts_probe_v1/grounded_feet.png']
report={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
 'findings':['시부키 기본/포스 사격4/6/8의 새 앞팔·몸체 연결과 머리/옷 명암 방향을 수용한다.','나나 라이징의 사랑이 고정 크기와 손 연결, 지상231/232의 발목/신발 접지 정합 방향을 수용한다.'],
 'limits':['최종 패킹·부분층·재추출 검토 전 후보이며 현재 시험 BIN 반영이 아니다.','사용자 최종 수용을 뜻하지 않는다.']}
p=W/'root_review_checkpoint57.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
for mode,target in [('br','br14'),('rn','rn15')]:
 src=(R/f'open_selection_{mode}13.py').read_text('utf8')
 dest=R/f'open_selection_{target}.py';assert not dest.exists()
 dest.write_text(src.replace(f'{mode}13',target),'utf8')
plan={'duration':8,'events':[{'at':1,'hold':.1,'keys':['cross']}]}
p=R/'shibuki_selection14_plan.json';assert not p.exists();p.write_text(json.dumps(plan)+'\n','utf8')
print(sha(W/'root_review_checkpoint57.json'))
