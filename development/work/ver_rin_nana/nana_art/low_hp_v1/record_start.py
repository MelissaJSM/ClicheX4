import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import write
quote='방금 사다리테스트를 내가했어 충분해 다음으로 바로 작업넘어가도좋아'
p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j['nana_ladder'].update(user_accepted=True,user_quote=quote,date='2026-10-30',acceptance_source='user gameplay test');j['active_substage']='NANA_LOW_HP_PRODUCTION';write(p,j)
p=ROOT/'out/ver_rin_nana/nana_ladder_20261029T232724676396Z/manifest.json';j=json.loads(p.read_text('utf8'));j.update(new_animation_user_accepted=True,user_acceptance={'quote':quote,'date':'2026-10-30','automated_full_audit_complete':False});write(p,j)
p=ROOT/'docs/NANA_LADDER.md';s=p.read_text('utf8').replace('새 미술은 아직 사용자 수용 전이다.','사용자가 직접 사다리를 테스트하고 수용했다. 자동 전수 검사는 미완료로 남긴다.');s+='\n2026-10-30 사용자 “'+quote+'”로 사다리 범위를 수용했다.\n';p.write_text(s,'utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8').replace('**사다리14참조 실기/사용자 미술 수용은 아직 미완료**다. 다음 제작은 체력 부족 대기.','사다리는 사용자 직접 테스트로 수용했다. 자동14참조 전수 검사는 미완료다. 체력 부족 대기6참조 제작 중.');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 사다리 사용자 수용·체력 부족 제작\n\n사용자 “'+quote+'”. 사다리 적용판 `a4c10012…`의 직접 테스트 수용으로 기록하며 자동 전수 검사와 구분한다. 다음 승인된 기본형 범위로 체력 부족 대기120..125를 제작한다.\n\n'+p.read_text('utf8'),'utf8')
