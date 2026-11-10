"""In-memory negative cases only; pinned files stay unchanged."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_hurt_lowhp as pack
arc=pack.P.read_bytes();targets,effects=pack.derive(arc)
cases=[]
for case in ('wrong_parent','missing135','extra147','wrong_pose139','changed_art_pixel','index16','changed_original_lightning','missing_ring'):
 data=arc;t={n:a.copy()for n,a in targets.items()};f={n:a.copy()for n,a in effects.items()}
 if case=='wrong_parent':data=bytes([arc[0]^1])+arc[1:]
 elif case=='missing135':del t[135]
 elif case=='extra147':t[147]=t[135].copy()
 elif case=='wrong_pose139':t[139]=t[135].copy()
 elif case=='changed_art_pixel':t[149][152,154]^=1
 elif case=='index16':t[152][155,153]=16
 elif case=='changed_original_lightning':f[141][140,155]^=1
 else:del f[145]
 try:pack.build(data,t,f)
 except ValueError as exc:cases.append({'case':case,'rejection':str(exc)})
 else:raise AssertionError('Unsafe input accepted')
p=pack.OUT/'PL01_U.ARC';h=hashlib.sha256(p.read_bytes()).hexdigest()
assert h=='4e18b1cda6731f97272eba361a2ac19df3606f75a19b5352f6025d403196e769'
j={'passed':True,'candidate_sha256':h,'rejections':cases,'candidate_reproduced_twice_during_prepare':True,'files_mutated_for_negative_tests':0}
(D/'rin_extension/rin117_guard_checks.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j))
