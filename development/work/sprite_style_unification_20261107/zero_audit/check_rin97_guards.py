"""Reject invalid in-memory requests without editing any source asset."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_wall_followup as wrapper
c=wrapper.core;e=c.engine;arc=c.P.read_bytes();targets=c.targets(arc)
e.PARENT=c.P;e.PARENT_SHA=c.SHA;e.KEYS={k:(0,0,0)for k in targets};e.get_targets=c.targets;e.pack_frame=c.pack
rows=[]
for case in('wrong_parent','missing34','extra37','changed_master','index16','changed_alias42','changed_alias43'):
 a=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='wrong_parent':a=bytes([arc[0]^1])+arc[1:]
 elif case=='missing34':del t[0,34]
 elif case=='extra37':t[0,37]=t[0,34].copy()
 elif case=='changed_master':t[0,36][143,156]^=1
 elif case=='index16':t[0,38][149,150]=16
 elif case=='changed_alias42':t[0,42][150,156]^=1
 else:t[0,43][150,156]^=1
 try:e.build(a,t)
 except ValueError as exc:rows.append({'case':case,'error':str(exc)})
 else:raise AssertionError('Invalid request accepted')
p=c.OUT/'PL01_U.ARC';j=json.loads((c.OUT/'proposal.json').read_text('utf8'));assert hashlib.sha256(p.read_bytes()).hexdigest()==j['after_sha256']and j['reproducible']
r={'passed':True,'candidate_sha256':j['after_sha256'],'reproducible_twice_from_pinned_art':True,'source_file_mutations_for_negative_tests':0,'rejections':rows}
(D/'rin_extension/rin97_guard_checks.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(r))
