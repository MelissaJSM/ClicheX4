import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import write
quote='좋아 계속 작업하자'
p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j['nana_low_hp'].update(user_accepted=True,user_quote=quote,date='2026-10-30',acceptance_source='사용자 계속 진행 수용; 직접 저체력 테스트 진술은 없음');j['active_substage']='NANA_ARRIVAL_PRODUCTION';write(p,j)
p=ROOT/'out/ver_rin_nana/nana_low_hp_20261029T233800161474Z/manifest.json';j=json.loads(p.read_text('utf8'));j.update(new_animation_user_accepted=True,user_acceptance={'quote':quote,'date':'2026-10-30','user_gameplay_test_reported':False,'automated_full_audit_complete':False});write(p,j)
p=ROOT/'docs/NANA_LOW_HP.md';p.write_text(p.read_text('utf8')+'\n2026-10-30 사용자 “'+quote+'”로 현재 결과를 수용하고 다음 제작을 진행한다. 직접 저체력 테스트 완료 진술은 없으므로 발동 실기 미완료는 유지한다.\n','utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8').replace('**저체력6참조 발동 실기·사용자 미술 수용은 미완료**다. 다음 제작은 등장·준비 자세.','저체력 결과는 사용자 계속 진행 수용을 받았다. 직접 저체력 테스트 진술과 자동 발동 검증은 없다. 등장·준비 자세17참조 제작 중.');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 저체력 결과 수용·등장 제작\n\n사용자 “'+quote+'”에 따라 현재 저체력 결과를 수용하고 등장·준비 자세 제작을 진행한다. 이 지시를 직접 저체력 발동 테스트 완료로 기록하지 않는다. 원래 고정 슬롯 범위를 우선 사용하고 기존123참조를 보존한다.\n\n'+p.read_text('utf8'),'utf8')
