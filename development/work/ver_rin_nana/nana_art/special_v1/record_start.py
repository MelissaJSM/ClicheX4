import json,sys
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));from scripts.prepare_nana_idle_shot import write
quote='좋아 내가직접봤어 다음작업으로 가도 돼'
p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j['nana_victory_return'].update(user_accepted=True,user_quote=quote,date='2026-10-30',user_gameplay_test_reported=True);j['active_substage']='NANA_SPECIAL_PRODUCTION';write(p,j)
p=ROOT/'out/ver_rin_nana/nana_victory_20261030T002449610350Z/manifest.json';j=json.loads(p.read_text('utf8'));j.update(new_animation_user_accepted=True,user_acceptance={'quote':quote,'date':'2026-10-30','user_gameplay_test_reported':True});write(p,j)
p=ROOT/'docs/NANA_VICTORY_RETURN.md';p.write_text(p.read_text('utf8')+'\n2026-10-30 사용자 “'+quote+'”로 직접 관찰한 승리·귀환 결과를 수용했다. 자동 전수 발동 검증과는 구분한다. 다음 제작은 나나 특수 자세다.\n','utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8').replace('**보스 클리어 승리·귀환 실기와 사용자 미술 수용은 미완료**다.','사용자가 직접 확인한 승리·귀환 결과를 수용했다. 자동 전수 발동 검증은 미완료다.').replace('다음 기본형 제작은 특수무기 자세.','현재 정지 차지 연계·더블 사이클론7참조를 제작 중이다.');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 승리·귀환 사용자 수용, 특수 자세 시작\n\n사용자 “'+quote+'”를 직접 관찰 후 수용과 다음 기본형 제작 지시로 기록한다. 수용 부모 `a225875d…`에서 차지 연계88..91·더블 사이클론97..99부터 제작한다. 원래 효과/탄환/타이밍·아머·기존150참조는 보존하며 새로운 자원 재배치는 하지 않는다.\n\n'+p.read_text('utf8'),'utf8')
