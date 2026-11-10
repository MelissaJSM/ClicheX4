from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='8a7ee9c47d170c8869f5415e18dc23e920157e28e9d49d7762a7acebc416a01e';new='8eb84afaa7c201dfcaee8e5cbf4c2fef152d423b10b501e8238362f9b5cca5b2'
assert sha(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v39/rin_nana.bin')==new
files=[]
for name,version in [('read_menu','rn37'),('record','rn37'),('open_continue','rn37'),('load_ultimate','rn19'),('advance_hq','rn37'),('open_selection','rn35')]:
 src=R/f'{name}_{version}.py';dest=R/f'{name}_rn39.py';assert not dest.exists();s=src.read_text('utf8').replace(old,new).replace(version,'rn39').replace('checkpoint37','checkpoint39');dest.write_text(s,'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
p=R/'tools_binding_rn39.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8')
for name in('hover_runtime','hover_shot'):
 src=ROOT/'work/ver_rin_nana/nana_ultimate_armor'/f'{name}_plan.json';j=json.loads(src.read_text('utf8'));dest=R/f'rn39_{name}_plan.json';assert not dest.exists()
 plan={'duration':j['seconds'],'events':[{'at':a,'hold':b-a,'keys':[{'jump':'cross','fire':'square'}.get(k,k)]}for k,a,b in j['keys']]}
 dest.write_text(json.dumps(plan,indent=2)+'\n','utf8')
print(new)
