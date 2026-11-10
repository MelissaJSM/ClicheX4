import json,sys,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];d=Path(__file__).parent;src=d/'production15';dst=d/'negative_inputs15';shutil.copytree(src,dst)
results=[]
for kind in ('wrong_palette','missing_frame','stale_packing_hash','armor_write'):
 for name in ('art.json','packing.json'):shutil.copyfile(src/name,dst/name)
 filename='packing.json' if kind in ('stale_packing_hash','armor_write') else 'art.json';p=dst/filename;data=json.loads(p.read_text())
 if kind=='wrong_palette':data['palette_words'][1]^=1
 elif kind=='missing_frame':data['frames'].pop()
 elif kind=='stale_packing_hash':data[0]['raw_sha256']='0'*64
 else:data[0]['writable'].append(6)
 p.write_text(json.dumps(data,indent=2),encoding='utf-8')
 r=subprocess.run([sys.executable,'scripts/prepare_shibuki_ladder.py','--art',str(dst),'--parent','out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z'],cwd=ROOT,capture_output=True,text=True)
 reason=r.stderr.strip().splitlines()[-1] if r.stderr.strip() else '';assert r.returncode!=0 and 'ValueError' in reason
 results.append({'name':kind,'rejected':True,'reason':reason});print(results[-1])
(d/'negative_checks15.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
