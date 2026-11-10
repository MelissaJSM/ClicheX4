"""벽 자세에 공통 축척을 적용하고 원본 얼굴 높이·벽쪽 접점에 등록한다."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
d=Path(__file__).parent;out=d/'normalized05';assert not (out/'art.json').exists();out.mkdir(exist_ok=True)
src=Image.open(d/'compact_generated.png').convert('RGBA');pal=json.loads((d.parent/'idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words']
rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
original=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';inv=json.loads((original/'inventory.json').read_text())
def face(n):
 a=np.array(Image.open(original/f'base_{n:03d}.png'));mask=np.isin(a,[3,4]);mask[a.shape[0]//2:]=False;yy,xx=np.nonzero(mask);bb=inv['base_frames'][n]['bounds'];return np.array([float(np.median(xx)+bb[0]),float(np.median(yy)+bb[1])])
cells=[]
for i,n in enumerate(range(55,67,2)):
 chosen=Image.open(d/'contact_generated.png').convert('RGBA') if n in (61,65) else src;c=chosen.crop((i%3*512,i//3*512,(i%3+1)*512,(i//3+1)*512));yy,xx=np.nonzero(np.array(c)[:,:,3]>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));cells.append((n,c.crop(bb),bb))
# One fixed scale across all six poses, calibrated to the accepted ear-to-eye height.
scale=0.15;records=[];sheet=Image.new('RGB',(7*288,264),'#28394b');draw=ImageDraw.Draw(sheet)
for i,(n,crop,bb) in enumerate(cells):
 size=tuple(round(v*scale) for v in crop.size);a=quantize(crop,size,rgb,128);head=np.indices(a.shape)[0]<size[1]*.6;ey,ex=np.nonzero((a==7)&head);assert len(ex)
 a[(a==7)&~head]=12
 goal=np.array([43.,32.+face(n)[1]-face(0)[1]]);left,top=[round(v) for v in goal-[np.median(ex),np.median(ey)]]
 yy,xx=np.nonzero(a)
 if n>=61:
  orig=np.array(Image.open(original/f'base_{n:03d}.png'));ox=np.nonzero(orig)[1];wall_x=int(ox.max()+inv['base_frames'][n]['bounds'][0]+48);gy,gx=np.indices(a.shape);hand=np.isin(a,[11,12,13])&(gx>np.median(ex)+5)&(gy<np.median(ey));hy,hx=np.nonzero(hand);assert len(hx);left=wall_x-int(hx.max())
 canvas=np.zeros((80,96),np.uint8);assert left>=0 and top>=0 and left+size[0]<=96 and top+size[1]<=80
 canvas[top:top+size[1],left:left+size[0]]=a;im=save_image(canvas.tobytes(),(96,80),pal,out/f'run_{n:03d}.png').convert('RGBA');im=im.resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,((i+1)*288,24),im);draw.text(((i+1)*288+8,5),str(n),fill='white')
 records.append({'frame':n,'image':f'run_{n:03d}.png','source_box':bb,'scale':scale,'size':size,'canvas_offset':[left,top],'eye_canvas':[float(np.median(ex)+left),float(np.median(ey)+top)],'registration':'source X relative face height; 61/63/65 source X wall contact registered to palm; single head-calibrated scale'})
im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(0,24),im);draw.text((8,5),'ACCEPTED IDLE',fill='white');sheet.save(out/'review.png')
(out/'art.json').write_text(json.dumps({'frames':records,'palette_words':pal,'source_inventory':str((original/'inventory.json').relative_to(ROOT))},indent=2));print(json.dumps(records))
