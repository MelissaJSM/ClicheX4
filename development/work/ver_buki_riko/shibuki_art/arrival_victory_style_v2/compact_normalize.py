from pathlib import Path
import json,sys,shutil,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;a=d/'production07';shutil.copytree(d/'production06',a,dirs_exist_ok=True);art=json.loads((a/'art.json').read_text());ns=list(range(133,140))+list(range(204,208));art['remaining_frames']=ns;art['groups']=[q for q in art['groups'] if q['frame'] in ns];art['frames']=[r for r in art['frames'] if r['frame'] in ns]
rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in art['palette_words']],np.int32)
src=Image.open(d/'compact_generated.png').convert('RGBA');cells=[]
for i in range(3):
 im=src.crop((round(i*src.width/3),0,round((i+1)*src.width/3),src.height));y,x=np.nonzero(np.array(im)[:,:,3]>=160);box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));cells.append(im.crop(box))
scale=47/cells[2].height;records=[]
for n,im in zip([137,138,0],cells):
 size=tuple(round(z*scale) for z in im.size);v=quantize(im,size,rgb,128);y,x=np.nonzero(v);ey,ex=np.nonzero((v==7)&(np.indices(v.shape)[0]<v.shape[0]*.65));left=round(75-float(np.median(ex[ey<=ey.min()+1])));top=102-int(y.max());out=np.zeros((160,160),np.uint8);out[top:top+size[1],left:left+size[0]]=v;save_image(out.tobytes(),(160,160),art['palette_words'],a/f'frame_{n:03}.png');records.append({'frame':n,'size':size,'offset':[left,top],'scale':scale})
 if n==138:
  v=np.zeros_like(out);y,x=np.nonzero(out);v[y-1,x]=out[y,x];save_image(v.tobytes(),(160,160),art['palette_words'],a/'frame_139.png')
art['compact_normalization']=records;art['accepted_pose_reuse']=[r for r in art['accepted_pose_reuse'] if r['frame'] in [135,136]]
(a/'art.json').write_text(json.dumps(art,indent=2));ls=json.loads((a/'layout.json').read_text());(a/'layout.json').write_text(json.dumps([r for r in ls if r['frame'] not in [137,138,139] and r['frame'] in ns],indent=2))
for n in [137,138,139]:
 p=a/f'packing_{n:03}.json'
 if p.exists():p.unlink()
for name in ['layout','optimize']:(d/(name+'_v7.py')).write_text((d/(name+'.py')).read_text().replace('production01','production07'))
print(records)
