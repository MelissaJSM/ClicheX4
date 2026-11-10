import json,sys,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];d=Path(__file__).parent;src=d/'production03';bad=d/'negative_inputs';bad.mkdir(exist_ok=False)
for name in ('art.json','packing.json','standing_085.png','standing_086.png','standing_087.png','standing_092.png'):shutil.copyfile(src/name,bad/name)
art=json.loads((bad/'art.json').read_text());pack=json.loads((bad/'packing.json').read_text());results=[];before=set((ROOT/'work/ver_buki_riko/shibuki_standing').iterdir())
cases=[('palette','Palette mismatch'),('armor','Writable/armor conflict'),('packing_hash','Packing source changed')]
for kind,expected in cases:
 a=json.loads(json.dumps(art));p=json.loads(json.dumps(pack))
 if kind=='palette':a['palette_words'][1]^=1
 if kind=='armor':p[0]['writable'].append(8)
 if kind=='packing_hash':p[0]['raw_sha256']='0'*64
 (bad/'art.json').write_text(json.dumps(a));(bad/'packing.json').write_text(json.dumps(p))
 r=subprocess.run([sys.executable,str(ROOT/'scripts/prepare_shibuki_standing.py'),'--art',str(bad),'--parent',str(ROOT/'out/ver_buki_riko/shibuki_run_20261026T082418920727Z')],capture_output=True,text=True)
 assert r.returncode!=0 and expected in r.stderr and set((ROOT/'work/ver_buki_riko/shibuki_standing').iterdir())==before
 results.append({'case':kind,'rejected':True,'error':expected,'no_output_created':True})
(d/'negative_checks.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
