"""승리 입력의 동작 설명을 한국어로 명확히 기록한다."""
from pathlib import Path
import re,json
D=Path(__file__).resolve().parent
POLICY='204 가슴 손/205 빈손 경례,206 뺨옆/207 머리위 권총. 역사 자세의 의미를 보존한다.'
p=D/'prepare_inputs.py';s=p.read_text('utf8');s=re.sub("'gesture_policy':'[^']*'",lambda m:"'gesture_policy':"+repr(POLICY),s);p.write_text(s,'utf8')
for group in('a','b'):
 p=D/f'{group}_inputs_v1/manifest.json'
 if p.exists():
  j=json.loads(p.read_text('utf8'));j['gesture_policy']=POLICY;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
