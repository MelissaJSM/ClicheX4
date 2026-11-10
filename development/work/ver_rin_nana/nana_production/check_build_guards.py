import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.build_nana_motion import validate
base=ROOT/'work/ver_rin_nana/nana_production/idle_shot_v2'
recipe=json.loads((base/'recipe.json').read_text('utf8'))
out=ROOT/'work/ver_rin_nana/nana_production/rejection_checks';out.mkdir(exist_ok=False)
results=[]
for name,key,value in [('wrong_scope','scope','unsupported'),('wrong_parent','parent_sha256','0'*64),('wrong_style','master_sha256','0'*64)]:
    a=out/name;a.mkdir();r={**recipe,key:value};(a/'recipe.json').write_text(json.dumps(r),'utf8')
    try:validate(a,a)
    except ValueError as e:results.append({'case':name,'rejected':True,'reason':str(e)})
    else:raise AssertionError(name+' was accepted')
try:validate(ROOT/'out/ver_buki_riko',base)
except ValueError as e:results.append({'case':'other_variant','rejected':True,'reason':str(e)})
else:raise AssertionError('Wrong variant accepted')
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n','utf8')
print('Rejected four invalid inputs before any disc write.')
