"""Inspect authored native-aligned cloth tones of the accepted movement source."""
from pathlib import Path
import sys,json,math,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'motion_cloth_probe';OUT.mkdir(exist_ok=True)
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import front,component
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
ART=ROOT/'work/ver_buki_riko/art_pilot/scale_consistency/walk_design_basis';arc=(D/'prepared_rear_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<64H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[:16]],np.float32);records=json.loads((ART/'fit_registration.json').read_text('utf8'));saved=np.load(ART/'worlds_final.npz');path=ART/'generated_motion.png';im=Image.open(path).convert('RGBA');groups=[[21],[22,23],[24],[25,26],[27,28,29,30,31,32],[33],[34],[3],[4]];targets={};proof=[];hc=colors[front];hg=(hc[:,:,1]>hc[:,:,0]+8)&(hc[:,:,1]>hc[:,:,2]+8)&(front>0);hgy,hgx=np.nonzero(hg)
for i,refs in enumerate(groups):
 n=refs[0];box=(round(i%3*im.width/3),round(i//3*im.height/3),round((i%3+1)*im.width/3),round((i//3+1)*im.height/3));cell=np.array(im.crop(box));components=component(cell[:,:,3]>=180);keep=np.zeros(cell.shape[:2],bool)
 for y,x in components[0]:keep[y,x]=True
 cell[~keep,3]=0;ys,xs=np.nonzero(keep);crop=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];a=cell[crop[1]:crop[3],crop[0]:crop[2]];h,w=[math.ceil(v*.148)for v in a.shape[:2]];xx=np.minimum(((np.arange(w)+.5)/.148).astype(int),a.shape[1]-1);yy=np.minimum(((np.arange(h)+.5)/.148).astype(int),a.shape[0]-1);sample=a[yy[:,None],xx[None,:]];m=sample[:,:,3]>=180;rgb=sample[:,:,:3].astype(np.float32);native=np.zeros((h,w),np.uint8);native[m]=1+np.argmin(((rgb[m,None,:]-colors[None,1:])**2).sum(2),1);green=(rgb[:,:,1]>rgb[:,:,0]+8)&(rgb[:,:,1]>rgb[:,:,2]+8)&m&(np.indices(native.shape)[0]<h*.45);gy,gx=np.nonzero(green);hx=round(float(gx.mean()-hgx.mean()));hw=records['head_positions'][str(n)];source_origin=[hw[0]-hx,hw[1]]
 historical=np.zeros((384,384),np.uint8);historical[96:224,96:224]=saved[str(n)];before=render(arc,0,0,n)[0];opts=[]
 for dy in range(-3,4):
  for dx in range(-12,13):opts.append((int(np.count_nonzero(np.roll(np.roll(historical,dy,0),dx,1)!=before)),abs(dx)+abs(dy),dx,dy))
 mismatch,_,dx,dy=min(opts);source_origin=[source_origin[0]+dx,source_origin[1]+dy];hw=[hw[0]+dx,hw[1]+dy];authored=np.zeros_like(before);authored[160+source_origin[1]:160+source_origin[1]+h,160+source_origin[0]:160+source_origin[0]+w]=native;votes=np.zeros((h,w,16),np.float32)
 for y in range(h):
  for x in range(w):
   block=a[math.floor(y/.148):min(a.shape[0],math.ceil((y+1)/.148)),math.floor(x/.148):min(a.shape[1],math.ceil((x+1)/.148))];mm=block[:,:,3]>=180
   if not mm.any():continue
   val=block[mm,:3].astype(np.float32);ix=1+np.argmin(((val[:,None,:]-colors[None,1:])**2).sum(2),1);votes[y,x]=np.bincount(ix,minlength=16)/len(ix)
 full=np.zeros((384,384,16),np.float32);full[160+source_origin[1]:160+source_origin[1]+h,160+source_origin[0]:160+source_origin[0]+w]=votes;editable=np.ones_like(before,bool);editable[160+hw[1]:160+hw[1]+19,160+hw[0]:160+hw[0]+23]=False;target=before.copy();changes=[]
 for y,x in np.argwhere(editable&(before==authored)&np.isin(before,[12,15])):
  col=int(full[y,x].argmax());old=int(before[y,x]);fraction=float(full[y,x,col])
  if (old,col)not in((15,12),(15,7),(12,7))or fraction<.4 or np.any(before[y-1:y+2,x-1:x+2]==0):continue
  target[y,x]=col;changes.append({'world':[int(x-160),int(y-160)],'before':old,'after':col,'source_vote':fraction})
 targets[f'b0_{n:03d}']=target;proof.append({'ref':n,'same_source_refs':refs,'source_cell':i,'source_cell_box':box,'source_component_crop':crop,'source_scale':.148,'source_native_origin_world':source_origin,'current_historical_alignment':[dx,dy],'current_historical_different_pixels':mismatch,'head_world':hw,'changes':changes,'changed_pixels':len(changes)})
np.savez_compressed(OUT/'targets.npz',**targets);crop=(120,112,200,192);cw=400;ch=428;board=Image.new('RGB',(1200,ch*10),'#65727a');draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
for row,n in enumerate([147]+[q[0]for q in groups]):
 before=render(arc,0,0,n)[0];after=targets.get(f'b0_{n:03d}',before);diff=np.where(after!=before,after,0).astype(np.uint8)
 for col,(v,label)in enumerate(((before,'current'),(after,'source votes'),(diff,'changed only'))):
  p=rgba(v,pal).crop(crop).resize((400,400),Image.Resampling.NEAREST);board.paste(p,(col*cw,row*ch+28),p);draw.text((col*cw+4,row*ch+5),str(n)+' '+label,font=font,fill='white')
board.save(OUT/'comparison.png');report={'source_arc_sha256':hashlib.sha256(arc).hexdigest(),'source_image':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':proof,'game_changed':False,'native_packed':False};(OUT/'inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'changes':{r['ref']:[r['changed_pixels'],r['current_historical_different_pixels']]for r in proof}}))
