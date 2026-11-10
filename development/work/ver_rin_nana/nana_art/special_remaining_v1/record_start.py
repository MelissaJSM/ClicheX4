import json,sys
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));from scripts.prepare_nana_idle_shot import write
quote='확인다했어 다음으로 진행하자';p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j['nana_special_charge_cyclone'].update(user_accepted=True,user_quote=quote,date='2026-10-30',user_gameplay_test_reported=True);j['active_substage']='NANA_SPECIAL_FROST_FIRE_PRODUCTION';write(p,j)
p=ROOT/'out/ver_rin_nana/nana_special_20261030T004646283984Z/manifest.json';j=json.loads(p.read_text('utf8'));j.update(new_animation_user_accepted=True,user_acceptance={'quote':quote,'date':'2026-10-30','user_gameplay_test_reported':True});write(p,j)
p=ROOT/'docs/NANA_SPECIALS.md';p.write_text(p.read_text('utf8')+'\n2026-10-30 사용자 “'+quote+'”로 이번 차지·사이클론 결과를 수용했다. 사용자 직접 확인과 자동 전수 검증 한계를 구분하며, 다음 프로스트 타워·라이징 파이어 계열9참조 제작으로 진행한다.\n','utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8').replace('새 미술 사용자 수용 전.','새 미술은 사용자 직접 확인으로 수용했다.').replace('다음은 남은 특수 자세.','현재 프로스트 타워·라이징 파이어 계열9참조 제작 중.');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 차지·사이클론 수용, 다음 특수 자세 제작\n\n사용자 “'+quote+'”를 직접 확인 후 수용으로 기록한다. 수용 부모 `796238e5…`에95/96,100..104,231/232의9참조를 누적한다. 기존157참조·몸/효과 팔레트·공격 효과·아머·타이밍을 보존하고 새 은행 재배치는 하지 않는다.\n\n'+p.read_text('utf8'),'utf8')
