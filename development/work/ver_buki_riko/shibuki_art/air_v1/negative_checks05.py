import json,sys,shutil,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];d=Path(__file__).parent;source=d/'production05';target=d/'negative_inputs05b';target.mkdir(exist_ok=False)
for f in source.iterdir():
 if f.is_file():shutil.copyfile(f,target/f.name)
original=(source/'art.json').read_bytes();art=json.loads(original)
cmd=[sys.executable,str(ROOT/'scripts/prepare_shibuki_run.py'),'--scope','air','--art',str(target),'--pairs',str(target),'--layout',str(d/'layout05.json'),'--parent',str(ROOT/'out/ver_buki_riko/shibuki_standing_20261026T093104097708Z')];results=[]
def check(name,expected):
 r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode!=0 and expected in r.stderr,(name,r.stderr);results.append({'name':name,'rejected':True,'reason':expected})
art['palette_words'][1]^=1;(target/'art.json').write_text(json.dumps(art));check('wrong_palette','Pair art mismatch')
art=json.loads(original);art['frames'].pop();(target/'art.json').write_text(json.dumps(art));check('missing_frame','Incomplete art/layout')
(target/'art.json').write_bytes(original);im=Image.open(target/'shoot_033.png');v=im.getpixel((26,30));im.putpixel((26,30),1 if v!=1 else 2);im.save(target/'shoot_033.png');check('stale_packing_after_pixel_edit','Packing source changed')
(d/'negative_checks05.json').write_text(json.dumps(results,indent=2));print(results)
