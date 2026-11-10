import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;out=d/'normalized01';out.mkdir(exist_ok=True)
src=Image.open(d/'generated_with_backdrop.png').convert('RGBA');pal=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
inv=json.loads((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json').read_text());source=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z'
def face(n):
 a=np.array(Image.open(source/f'base_{n:03d}.png'));mask=np.isin(a,[3,4]);mask[a.shape[0]//2:]=False;yy,xx=np.nonzero(mask);bb=inv['base_frames'][n]['bounds'];return np.array([float(np.median(xx)+bb[0]),float(np.median(yy)+bb[1])])
baseline=np.array(Image.open(ROOT/'work/ver_buki_riko/shibuki_art/standing_buster_v1/parent_000.png'));yy,xx=np.nonzero(baseline==7);eye0=np.array([float(np.median(xx)),float(np.median(yy))]);face0=face(0)
order=[list(range(33,45,2)),list(range(34,45,2)),list(range(45,55,2)),list(range(46,55,2))];cells=[]
for row,ns in enumerate(order):
 for col,n in enumerate(ns):
  cell=src.crop((col*256,row*256,(col+1)*256,(row+1)*256));a=np.array(cell);yy,xx=np.nonzero(a[:,:,3]>=128);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));crop=cell.crop(bb);cells.append((row,col,n,bb,crop))
first=np.array(cells[0][4]);delta=first[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:];lab=np.argmin((delta*delta).sum(3),axis=2)+1;ys,xs=np.nonzero((lab==7)&(first[:,:,3]>=128));scale=16/float(np.median(ys))
records=[];sheet=Image.new('RGB',(6*288,4*272),'#28394b');draw=ImageDraw.Draw(sheet)
for row,col,n,bb,crop in cells:
 size=tuple(round(v*scale) for v in crop.size);a=quantize(crop,size,rgb,64);yy,xx=np.nonzero(a==7)
 if not len(xx):raise ValueError(f'No eye {n}')
 goal=eye0+face(n)-face0;left,top=[round(v) for v in goal-np.array([np.median(xx),np.median(yy)])];canvas=np.zeros((80,96),np.uint8)
 if left<0 or top<0 or left+size[0]>96 or top+size[1]>80:raise ValueError('Clipped canvas')
 canvas[top:top+size[1],left:left+size[0]]=a;pic=save_image(canvas.tobytes(),(96,80),pal,out/f'air_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(pic,(col*288,row*272+24),pic);draw.text((col*288+8,row*272+5),str(n),fill='white')
 records.append({'frame':n,'image':f'air_{n:03d}.png','source_cell':[col,row],'source_box':bb,'scale':scale,'native_size':size,'canvas_offset':[left,top],'eye_world':(goal-[48,40]).tolist()})
sheet.save(out/'review.png');(out/'art.json').write_text(json.dumps({'palette_words':pal,'frames':records,'source_inventory':str((source/'inventory.json').relative_to(ROOT))},indent=2));print(json.dumps({'scale':scale,'frames':[{k:v for k,v in r.items() if k in ('frame','native_size','eye_world')} for r in records]}))
