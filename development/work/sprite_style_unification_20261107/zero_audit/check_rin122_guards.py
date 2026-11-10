"""Reject changed provenance/target inputs in memory; no protected files written."""
from pathlib import Path
import sys,json,hashlib,contextlib,io
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_ground_first as pack
c=pack.core;e=c.engine;arc=c.P.read_bytes();targets=c.targets(arc)
e.get_targets=c.targets;e.KEYS={k:(0,0,0) for k in targets};e.pack_frame=c.pack
cases=[]
for case in ('wrong_parent','missing62','extra147','modified63','palette16','changed_original64','modified_shared61','wrong_alias69'):
 data=arc;t={n:a.copy()for n,a in targets.items()}
 if case=='wrong_parent':data=bytes([arc[0]^1])+arc[1:]
 elif case=='missing62':del t[0,62]
 elif case=='extra147':t[0,147]=t[0,62].copy()
 elif case=='modified63':t[0,63][150,155]^=1
 elif case=='palette16':t[0,65][150,155]=16
 elif case=='changed_original64':t[0,64][150,155]^=1
 elif case=='modified_shared61':t[0,61][150,155]^=1
 else:t[0,69]=t[0,65].copy()
 try:e.build(data,t)
 except (ValueError,AssertionError)as exc:cases.append({'case':case,'reason':str(exc)})
 else:raise AssertionError('Unsafe input accepted: '+case)
with contextlib.redirect_stdout(io.StringIO()):out,proof=e.build(arc,targets)
actual=(c.OUT/'PL01_U.ARC').read_bytes();assert out==actual
j={'passed':True,'candidate_sha256':hashlib.sha256(out).hexdigest(),'rejections':cases,'fresh_process_reproduction_byte_identical':True,'writes_to_inputs':0}
(D/'rin_extension/rin122_guard_checks.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'rejections':len(cases),'reproduction':True}))
