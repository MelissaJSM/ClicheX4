import json,sys,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];d=Path(__file__).parent;src=d/'production03';dst=d/'negative_inputs03';shutil.copytree(src,dst)
results=[]
for kind in ('wrong_palette','wrong_effect_palette','missing_frame','stale_packing_hash','armor_write'):
 for name in ('art.json','packing.json'):shutil.copyfile(src/name,dst/name)
 filename='packing.json' if kind in ('stale_packing_hash','armor_write') else 'art.json';p=dst/filename;data=json.loads(p.read_text())
 if kind=='wrong_palette':data['palette_words'][1]^=1
 elif kind=='wrong_effect_palette':data['effect_palette_words'][1]^=1
 elif kind=='missing_frame':data['frames'].pop()
 elif kind=='stale_packing_hash':data[0]['raw_sha256']='0'*64
 else:data[0]['writable'].append(8)
 p.write_text(json.dumps(data,indent=2),encoding='utf-8')
 r=subprocess.run([sys.executable,'scripts/prepare_shibuki_hurt.py','--art',str(dst),'--parent','out/ver_buki_riko/shibuki_wall_20261026T135224131979Z'],cwd=ROOT,capture_output=True,text=True)
 reason=r.stderr.strip().splitlines()[-1] if r.stderr.strip() else '';assert r.returncode!=0 and 'ValueError' in reason
 results.append({'name':kind,'rejected':True,'reason':reason});print(results[-1])
(d/'negative_checks03.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
