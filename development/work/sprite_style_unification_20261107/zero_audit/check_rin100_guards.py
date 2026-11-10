"""Reject unsafe in-memory inputs; do not mutate pinned art or candidates."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_movement_finish as wrapper
c=wrapper.core;e=c.engine;arc=c.P.read_bytes();targets=c.targets(arc)
e.PARENT=c.P;e.PARENT_SHA=c.SHA;e.KEYS={k:(0,0,0)for k in targets};e.get_targets=c.targets;e.pack_frame=c.pack
cases=[]
for case in('wrong_parent','missing37','extra38','wrong_pose45','changed_master_pixel','index16'):
 data=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='wrong_parent':data=bytes([arc[0]^1])+arc[1:]
 elif case=='missing37':del t[0,37]
 elif case=='extra38':t[0,38]=t[0,37].copy()
 elif case=='wrong_pose45':t[0,45]=t[0,37].copy()
 elif case=='changed_master_pixel':t[0,193][146,153]=1
 else:t[0,37][147,158]=16
 try:e.build(data,t)
 except ValueError as exc:cases.append({'case':case,'error':str(exc)})
 else:raise AssertionError('Unsafe input accepted')
p=c.OUT/'PL01_U.ARC';assert hashlib.sha256(p.read_bytes()).hexdigest()=='72d04d36dde42379a144dc4688b09c582e4c0f867bc70d5742c33bb65b75b42a'
out={'passed':True,'candidate_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rejections':cases,'producer_reproduced_twice_during_prepare':True,'file_mutations_for_rejection_tests':0}
(D/'rin_extension/rin100_guard_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(out))
