"""기존 독립 reader 검사를 새 동결 전 후보에 바인딩한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).parent;E=D/'rin_extension';C='cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a'
# Reader/quantizer는 제작 코드 import 없이 재사용한다. 새 회전 mapping은 명시한다.
s=(D/'verify_rin191_readback.py').read_text('utf8')
s=s.replace("P=D/'prepared_ice01';A=D/'ice_registered_v1'","P=D/'prepared_spin01';A=D/'ice_spin_registered_v1'")
s=s.replace("prepared_saber_followup05_v2","prepared_ice01")
s=s.replace('70b483ba78dedefa9c4af45c9b4c5fe4fb8ef915290a4c92c1dd5dea6b0b01d8',C).replace('0f6665a4cca930edf7e90351b8a8ac044b23326b19836eaa52d473b1b2390941','70b483ba78dedefa9c4af45c9b4c5fe4fb8ef915290a4c92c1dd5dea6b0b01d8')
s=s.replace("r['generated_sha256']","reg['source_generated_sha256']")
start=s.index('mapping={');end=s.index('g,c=entry(old,2)',start)
s=s[:start]+'''mapping={161:(161,0),163:(163,0),165:(161,1),167:(163,1),169:(161,2),171:(163,2),173:(161,3),175:(163,3)}
def rotate(a,k):
 assert not a[320:,:].any()and not a[:,320:].any();z=np.zeros_like(a);z[:320,:320]=np.rot90(a[:320,:320],k);return z
targets={(1,n):rotate(masters[1,m],k)for n,(m,k)in mapping.items()};targets[1,144]=masters[1,144]
for n,(m,k)in mapping.items():
 before=render(old,1,5,n)[0];rot=rotate(render(old,1,5,m)[0],k);y,x=np.where(before!=rot)
 assert len(y)=={167:18,171:15}.get(n,0)
 if len(y):assert np.all(x+y==319)
''' + s[end:]
s=s.replace('support={(1,132)}','support={(1,n)for n in (145,146,147,162,164,166,168,170,172,174,176)}')
s=s.replace("counts['authored_exact']==11 and counts['other_display_exact']==425","counts['authored_exact']==9 and counts['other_display_exact']==427")
s=s.replace('rin191_components','rin200_components').replace("'cumulative_authored_refs':191,'incremental_refs':11,'previous180_preserved':True","'cumulative_authored_refs':200,'incremental_refs':9,'previous191_preserved':True")
s=s.replace('final191_readback_audit','final200_readback_audit')
(D/'verify_rin200_readback.py').write_text(s,'utf8')
plan=json.loads((E/'rin191_components.json').read_text('utf8'));r=plan['resources']['PL01_U.ARC'];r['path']=str((E/'prepared_spin01/PL01_U.ARC').as_posix());r['after']=C
# 경로는 workspace 상대형으로 저장한다.
r['path']='work/sprite_style_unification_20261107/zero_audit/rin_extension/prepared_spin01/PL01_U.ARC'
(E/'rin200_components.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
s=(D/'review_rin191.py').read_text('utf8').replace('ice191_review','spin200_review').replace("prepared_ice01/PL01_U.ARC","prepared_spin01/PL01_U.ARC").replace('prepared_saber_followup05_v2','prepared_ice01').replace('70b483ba78dedefa9c4af45c9b4c5fe4fb8ef915290a4c92c1dd5dea6b0b01d8',C)
s=s.replace("groups={'ice_drop':(97,'Ice drop'),'ice_recovery':(98,'Ice recovery')}","groups={'air_spin':(100,'Air spin native 100'),'rising_start':(101,'Rising start native 101')}")
s=s.replace('린168 원순서 검토','린200 원순서 검토').replace('린 검격 비교','린 회전·용염인 진입 비교')
(D/'review_rin200.py').write_text(s,'utf8')
s=(D/'check_rin191_guards.py').read_text('utf8').replace('pack_rin_ice01','pack_rin_spin02').replace('rin191','rin200')
s=s.replace('133','144').replace('135','161').replace('132','162').replace('134','165')
(D/'check_rin200_guards.py').write_text(s,'utf8')
print(C)
