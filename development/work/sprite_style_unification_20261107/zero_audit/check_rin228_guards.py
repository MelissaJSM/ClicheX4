"""메모리 안에서 잘못된 입력을 거부하고 실제 후보를 새 프로세스로 재생성."""
from pathlib import Path
import sys,json,hashlib,contextlib,io
D=Path(__file__).parent;sys.path.insert(0,str(D));import pack_rin_bank1_special01 as p
a=p.P.read_bytes();tt=p.configure(a);cases=[]
for case in('wrong_parent','missing91','extra_idle','changed103','invalid_palette','changed_effect92','changed_prior222'):
 arc=a;t={k:v.copy()for k,v in tt.items()}
 if case=='wrong_parent':arc=bytes([a[0]^1])+a[1:]
 elif case=='missing91':del t[1,91]
 elif case=='extra_idle':t[0,147]=t[1,91].copy()
 elif case=='changed103':t[1,103]=t[1,105].copy()
 elif case=='invalid_palette':t[1,91][150,150]=16
 elif case=='changed_effect92':t[1,92][150,150]^=1
 else:t[0,158]=t[1,91].copy()
 try:p.engine.build(arc,t)
 except(ValueError,AssertionError)as exc:cases.append({'case':case,'reason':str(exc)})
 else:raise AssertionError('Unsafe input accepted: '+case)
with contextlib.redirect_stdout(io.StringIO()):result,_=p.engine.build(a,tt)
assert result==(p.O/'PL01_U.ARC').read_bytes()
j={'passed':True,'candidate_sha256':hashlib.sha256(result).hexdigest(),'rejections':cases,'fresh_process_reproduction_exact':True,'source_written':False}
(D/'rin_extension/rin228_guard_checks.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'rejections':len(cases)}))
