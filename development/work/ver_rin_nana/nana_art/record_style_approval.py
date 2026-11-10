import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
quote='좋아 디자인 만족스러워 바로 진행해줘. 단, 아까 린 할때처럼 모션마다 도트질감이 서로 다르는 이슈가생기면안돼!'
pilot=ROOT/'out/ver_rin_nana/nana_pilot_v9'
approval={'date':'2026-10-29','quote':quote,'candidate':'out/ver_rin_nana/nana_pilot_v9','scope':'나나 기준안 수용 및 같은 도트 질감을 유지한 기본형 모션 제작·실적용 진행','master_sha256':hashlib.sha256((pilot/'nana_000_indexed.png').read_bytes()).hexdigest(),'palette_sha256':hashlib.sha256((pilot/'palette.bin').read_bytes()).hexdigest()}
for relative in ('projects/ver_rin_nana/project.json','projects/ver_rin_nana/nana_candidate.json'):
    p=ROOT/relative;d=json.loads(p.read_text('utf8'))
    if p.name=='project.json':
        d['active_substage']='NANA_IDLE_STANDING_PRODUCTION';d['nana_pilot'].update(status='user_art_accepted',art_approved=True,approval=approval)
        d['nana_style_approval']=approval
    else:d.update(art_approved=True,approval=approval)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
p=ROOT/'docs/DECISIONS.md';s=p.read_text('utf8');header='# 결정 기록\n'
s=s.replace(header,header+'\n## 2026-10-29 — 나나 기준안 수용·질감 일관성 필수\n\n사용자 “'+quote+'”로 `nana_pilot_v9` 대기·권총 디자인을 수용하고 기본형 모션 제작 및 적용을 진행한다. 원본 미국판 해시·첫 모드 보존 조건을 유지한다. 같은 팔레트·체형·얼굴·윤곽 질감과 모션 연결을 검수한다. 기준안 수용을 이후 애니메이션 실기 완료로 기록하지 않는다.\n',1);p.write_text(s,'utf8')
print(json.dumps(approval,ensure_ascii=False))
