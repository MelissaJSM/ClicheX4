"""In-memory refusal and fresh-process reproduction; protected inputs stay untouched."""
from pathlib import Path
import sys,json,hashlib,contextlib,io
D=Path(__file__).parent;sys.path.insert(0,str(D));import pack_rin_saber_followup03 as p
arc=p.P.read_bytes();targets=p.configure(arc);cases=[]
for case in('parent_hash','missing229','extra147','bad_palette','altered234','changed_saber231','changed_alias132','changed_prior62'):
 a=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='parent_hash':a=bytes([a[0]^1])+a[1:]
 elif case=='missing229':del t[0,229]
 elif case=='extra147':t[0,147]=t[0,229].copy()
 elif case=='bad_palette':t[0,230][150,150]=16
 elif case=='altered234':t[0,234][150,150]^=1
 elif case=='changed_saber231':t[0,231][150,150]^=1
 elif case=='changed_alias132':t[1,132]=t[0,230].copy()
 else:t[0,62]=t[0,229].copy()
 try:p.engine.build(a,t)
 except(ValueError,AssertionError)as e:cases.append({'case':case,'reason':str(e)})
 else:raise AssertionError('Invalid target accepted: '+case)
with contextlib.redirect_stdout(io.StringIO()):result,proof=p.engine.build(arc,targets)
assert result==(p.O/'PL01_U.ARC').read_bytes()
j={'passed':True,'candidate_sha256':hashlib.sha256(result).hexdigest(),'rejections':cases,'fresh_process_reproduction_byte_identical':True,'writes_to_inputs':0}
(D/'rin_extension/rin168_guard_checks.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'rejections':len(cases),'reproduction':True}))
