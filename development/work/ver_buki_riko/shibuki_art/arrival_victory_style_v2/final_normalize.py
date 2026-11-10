from pathlib import Path
import json,sys,shutil,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
d=Path(__file__).parent;a=d/'production09';shutil.copytree(d/'production07',a,dirs_exist_ok=True);art=json.loads((a/'art.json').read_text());rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in art['palette_words']],np.int32)
src=Image.open(d/'final_poses.png').convert('RGBA');cells=[]
for i in range(6):
 im=src.crop((i%3*512,i//3*512,(i%3+1)*512,(i//3+1)*512));y,x=np.nonzero(np.array(im)[:,:,3]>=160);box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));cells.append(im.crop(box))
scale=47/cells[1].height;records=[]
for n,im in zip([133,135,204,205,206,207],cells):
 size=tuple(round(z*scale) for z in im.size);v=quantize(im,size,rgb,160);y,x=np.nonzero(v);ey,ex=np.nonzero((v==7)&(np.indices(v.shape)[0]<v.shape[0]*.65));left=round(75-float(np.median(ex[ey<=ey.min()+1])));top=102-int(y.max());out=np.zeros((160,160),np.uint8);out[top:top+size[1],left:left+size[0]]=v;save_image(out.tobytes(),(160,160),art['palette_words'],a/f'frame_{n:03}.png');records.append({'frame':n,'size':size,'offset':[left,top],'scale':scale,'eye_y':float(np.median(ey[ey<=ey.min()+1]))+top})
 if n==135:
  v=np.zeros_like(out);y,x=np.nonzero(out);v[y-1,x]=out[y,x];save_image(v.tobytes(),(160,160),art['palette_words'],a/'frame_136.png')
arc=(ROOT/art['parent']/'modified.arc').read_bytes();es=psx_arc(arc);g,c=[arc[e['offset']:e['offset']+e['size']] for t in (2,3) for e in es if int(e['type'],16)==t];bank=graphics_bank(g,0,allow_bank_aliases=True);f=bank['frames'][129];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;bg=canvas_from_parts(raw,f['tile_count'],composition_frame(c,0,129))%16;v=np.array(Image.open(a/'frame_133.png'));bg[v!=0]=np.where(v[v!=0]==15,5,9);save_image(bg.tobytes(),(160,160),art['palette_words'],a/'frame_134.png')
art['final_normalization']=records;art['accepted_pose_reuse']=[];(a/'art.json').write_text(json.dumps(art,indent=2))
changed=[133,134,135,136,204,205,206,207];ls=json.loads((a/'layout.json').read_text());(a/'layout.json').write_text(json.dumps([r for r in ls if r['frame'] not in changed],indent=2))
for n in changed:
 p=a/f'packing_{n:03}.json'
 if p.exists():p.unlink()
for name in ['layout','optimize']:(d/(name+'_v9.py')).write_text((d/(name+'.py')).read_text().replace('production01','production09'))
items=[0,133,134,135,136,137,138,139,204,205,206,207];sheet=Image.new('RGB',(6*240,2*264),'#253546');dr=ImageDraw.Draw(sheet)
for i,n in enumerate(items):
 path=ROOT/art['parent']/f'sprite_review/frame_{n:03}.png' if n==0 else a/f'frame_{n:03}.png';im=Image.open(path).convert('RGBA').crop((40,35,120,115)).resize((240,240),Image.Resampling.NEAREST);x=i%6*240;y=i//6*264;sheet.paste(im,(x,y+24),im);dr.text((x+6,y+6),str(n),fill='white')
sheet.save(a/'comparison.png');print(records)
