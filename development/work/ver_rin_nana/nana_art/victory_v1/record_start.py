import json,sys
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));from scripts.prepare_nana_idle_shot import write
quote='오케이 다음 작업으로 진행하자';p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j['nana_arrival'].update(user_accepted=True,user_quote=quote,date='2026-10-30',user_gameplay_test_reported=False);j['active_substage']='NANA_VICTORY_RETURN_PRODUCTION';write(p,j)
p=ROOT/'out/ver_rin_nana/nana_arrival_20261029T235340020385Z/manifest.json';j=json.loads(p.read_text('utf8'));j.update(new_animation_user_accepted=True,user_acceptance={'quote':quote,'date':'2026-10-30','user_gameplay_test_reported':False});write(p,j)
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8').replace('반대 방향·사용자 새 미술 수용은 미완료다.','반대 방향 자동 검사는 미완료다. 사용자 다음 진행 지시로 등장 결과를 수용했다.').replace('다음 제작은 승리·귀환.','승리·귀환10참조 제작 중.');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 등장 수용·승리/귀환 제작\n\n사용자 “'+quote+'”를 등장 결과 수용과 후속 기본형 제작 지시로 기록한다. 별도 직접 테스트 완료 진술은 없다. 수용 부모 `30e4ee72…`에 승리204..207·귀환156..161만 누적하며, 원래 슬롯·아머·팔레트·게임 동작을 보존한다.208..212는 애니메이션98의 별도 특수 참조이므로 이번 귀환 작업에 포함하지 않는다.\n\n'+p.read_text('utf8'),'utf8')
