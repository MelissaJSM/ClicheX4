"""입력 거부 및 메모리 안의 후보 재생성."""
from pathlib import Path
import sys,json,hashlib,contextlib,io
D=Path(__file__).parent;sys.path.insert(0,str(D));import pack_rin_bank1_recovery128 as p
a=p.P.read_bytes();tt=p.configure(a);cases=[]
for case in('wrong_parent','missing128','extra_idle','changed129','invalid_palette','changed_prior236'):
 arc=a;t={k:v.copy()for k,v in tt.items()}
 if case=='wrong_parent':arc=bytes([a[0]^1])+a[1:]
 elif case=='missing128':del t[1,128]
 elif case=='extra_idle':t[0,147]=t[1,128].copy()
 elif case=='changed129':t[1,129][150,150]^=1
 elif case=='invalid_palette':t[1,128][150,150]=16
 else:t[1,108]=t[1,128].copy()
 try:p.engine.build(arc,t)
 except(ValueError,AssertionError)as exc:cases.append({'case':case,'reason':str(exc)})
 else:raise AssertionError('Unsafe input accepted: '+case)
with contextlib.redirect_stdout(io.StringIO()):result,_=p.engine.build(a,tt)
assert result==(p.O/'PL01_U.ARC').read_bytes()
j={'passed':True,'candidate_sha256':hashlib.sha256(result).hexdigest(),'rejections':cases,'fresh_process_reproduction_exact':True,'source_written':False}
(D/'rin_extension/rin240_guard_checks.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'rejections':len(cases)}))
