from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='8eb84afaa7c201dfcaee8e5cbf4c2fef152d423b10b501e8238362f9b5cca5b2';new='fdcebed25fb3ffde641d9a6fc5f56180e74f2d3367057eea2f70c5123ac613b9'
assert sha(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v40/rin_nana.bin')==new
files=[]
for name in ['read_menu','record','open_continue','load_ultimate','advance_hq']:
 src=R/f'{name}_rn39.py';dest=R/f'{name}_rn40.py';assert not dest.exists();s=src.read_text('utf8').replace(old,new).replace('rn39','rn40').replace('checkpoint39','checkpoint40');dest.write_text(s,'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
out=R/'tools_binding_rn40.json';assert not out.exists();out.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8')
p=R/'rn40_nova_plan.json';assert not p.exists();p.write_text(json.dumps({'duration':7,'events':[{'at':.1,'hold':.1,'keys':['right']},{'at':.5,'hold':.15,'keys':['r2']},{'at':3.,'hold':.1,'keys':['left']},{'at':3.5,'hold':.15,'keys':['r2']}],'rationale':'기존 실제 노바 f=scan33=현재R2 바인딩을 확인한 짧은 일반조작 계획. 발동 여부는 캡처로 별도 판정.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(new)
