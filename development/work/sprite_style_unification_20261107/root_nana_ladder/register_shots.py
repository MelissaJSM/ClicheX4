from pathlib import Path
import json,sys,hashlib,shutil
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,helper
from register_page import register
sha=lambda b:hashlib.sha256(b).hexdigest()
source=Path(sys.argv[1]);out=D/'shot_art01';out.mkdir(exist_ok=False);dest=out/'generated.png';shutil.copy2(source,dest)
im=Image.open(dest).convert('RGBA');m=json.loads((D/'shot_inputs01/manifest.json').read_text('utf8'));a=Archive((ROOT/m['source_arc']).read_bytes());assert sha(a.data)==m['source_arc_sha256']
for p in m['inputs']:assert sha((ROOT/p['path']).read_bytes())==p['sha256']
(out/'generation.json').write_text(json.dumps({'tool':'builtin image_gen','source':str(source),'workspace':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest.read_bytes()),'prompt_sha256':m['prompt_sha256'],'size':list(im.size),'alpha':list(im.getchannel('A').getextrema())},ensure_ascii=False,indent=2)+'\n','utf8')
reg=D/'shot_registered01';reg.mkdir(exist_ok=False);rows=[];records=[]
for q in m['frames']:
 cell,form,ref=q['cell'],q['form'],q['ref'];start=16 if q['mask']else 0;box=tuple(round(v)for v in(cell%2*im.width/2,cell//2*im.height/2,(cell%2+1)*im.width/2,(cell//2+1)*im.height/2));crop=im.crop(box)
 pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
 z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(crop,(96,96),pal,'area_vote');Image.fromarray(z).save(reg/f'{form}_{ref:03}_indices.png');rgba=a.rgba(z,start);rgba.save(reg/f'{form}_{ref:03}_rgba.png')
 rows.append((f'{form} {ref}',[('new rest149',Image.open(D/'contact_registration02'/f'{form}_149_rgba.png')),('current shot guide',a.composite(ref,q['mask'],2)[0]),('new shot fixed cell',rgba)]))
 records.append({**q,'sha256':sha(z.tobytes()),'bbox':rgba.getbbox(),'source_cell':box})
for i in range(0,4,2):helper.grid(rows[i:i+2],reg/f'comparison_{i//2+1}.png',6)
(reg/'registration.json').write_text(json.dumps({'frames':records,'art_sha256':sha(dest.read_bytes()),'fixed_cell':[96,96],'world_origin':[160,160],'packed':False,'arm_extraction_pending':True},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(records))
