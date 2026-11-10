import json,sys,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];d=Path(__file__).parent
src=d/'production19';dest=d/'negative_inputs19';shutil.copytree(src,dest)
base=[sys.executable,'scripts/prepare_shibuki_run.py','--scope','wall','--art',str(dest),'--pairs',str(dest),'--layout',str(d/'layout19.json'),'--parent','out/ver_buki_riko/shibuki_dash_20261026T113618370649Z']
results=[]
for kind in ('wrong_palette','missing_frame','stale_packing_hash','armor_overlap_write'):
 for name in ('art.json','pairs.json','packing.json'):shutil.copyfile(src/name,dest/name)
 filename='art.json' if kind in ('wrong_palette','missing_frame') else 'packing.json'
 p=dest/filename;data=json.loads(p.read_text())
 if kind=='wrong_palette':data['palette_words'][1]^=1
 elif kind=='missing_frame':data['frames'].pop()
 elif kind=='stale_packing_hash':data[0]['raw_sha256']='0'*64
 else:data[0]['overlap_fill']=[[17,0,0,1]]
 p.write_text(json.dumps(data,indent=2),encoding='utf-8')
 r=subprocess.run(base,cwd=ROOT,capture_output=True,text=True)
 reason=r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ''
 assert r.returncode!=0 and 'ValueError' in reason,(kind,r.stdout,r.stderr)
 results.append({'name':kind,'rejected':True,'reason':reason});print(results[-1])
(d/'negative_checks19.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
