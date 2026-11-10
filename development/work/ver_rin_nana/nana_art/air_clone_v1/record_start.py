import json,sys
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));from scripts.prepare_nana_idle_shot import write
quote='좋아 테스트 해봤어 다음 작업으로 넘어가도 돼';p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j['nana_special_frost_fire'].update(user_accepted=True,user_quote=quote,date='2026-10-30',user_gameplay_test_reported=True);j['active_substage']='NANA_AIR_CLONE_PRODUCTION';write(p,j)
p=ROOT/'out/ver_rin_nana/nana_special_remaining_20261030T010327624138Z/manifest.json';j=json.loads(p.read_text('utf8'));j.update(new_animation_user_accepted=True,user_acceptance={'quote':quote,'date':'2026-10-30','user_gameplay_test_reported':True,'does_not_prove_unobserved_charge_variants':True});write(p,j)
p=ROOT/'docs/NANA_FROST_FIRE.md';p.write_text(p.read_text('utf8')+'\n2026-10-30 사용자 “'+quote+'”로 관찰한 프로스트·라이징 파이어 결과를 수용했다. 어떤 차지 전용 조건을 추가 시험했는지는 진술되지 않았으므로100..102와 분신의 실기 미확인 상태는 유지한다.\n','utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8').replace('새 미술 사용자 수용 전.','새 미술은 사용자 테스트 후 수용했다.').replace('다음은 추가 공중·분신 계열.','현재 추가 공중·분신 기본몸17참조 제작 중.');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 프로스트·파이어 수용, 추가 공중·분신 제작\n\n사용자 “'+quote+'”를 테스트 후 수용으로 기록한다. 수용 부모 `1521ce51…`에93/94,208..212,221..230의17기본형 참조를 누적한다. 수용 공중 도트를 재사용하고 몸 소멸은 나나 실루엣으로 바꾼다. 아머 의상·노바213..220은 이번 범위가 아니며 기존166참조·아머 타일·공격 효과·팔레트·시간표를 보존한다.\n\n'+p.read_text('utf8'),'utf8')
