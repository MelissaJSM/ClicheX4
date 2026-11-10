"""Compare authored clothing cells against exact native victory registration."""
from pathlib import Path
import sys,json,math,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'victory_cloth_probe';OUT.mkdir(exist_ok=True)
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,front,component
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
ART=ROOT/'work/ver_buki_riko/art_pilot/victory_beam_out_v1';arc=(D/'prepared_rear_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<64H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[:16]],np.float32);records={r['frame']:r for r in json.loads((ART/'key_registration.json').read_text('utf8'))};saved=np.load(ART/'key_worlds.npz');targets={};proof=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
for n,i in[(1,0),(2,0),(3,1),(4,2),(5,3),(6,4)]:
 path=ART/('generated_gesture.png'if n>=5 else'generated_corrected.png');im=Image.open(path).convert('RGBA');ax=np.array(im);sx=np.flatnonzero(np.any(ax[:,:,3]>=220,axis=0));spans=[g for g in np.split(sx,np.where(np.diff(sx)>1)[0]+1)if len(g)>10];g=spans[i];box=(int(g[0])-2,0,int(g[-1])+3,im.height);cell=im.crop(box);a=np.array(cell);groups=component(a[:,:,3]>=220);keep=np.zeros(a.shape[:2],bool)
 for y,x in groups[0]:keep[y,x]=True
 a[~keep,3]=0;ys,xs=np.nonzero(keep);cropbox=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));a=a[cropbox[1]:cropbox[3],cropbox[0]:cropbox[2]];native=sample(cell,.095);h,w=native.shape;head=front if n==1 else np.fliplr(front);gy,gx=np.nonzero(np.isin(native,[4,8,14]));hy,hx=np.nonzero(np.isin(head,[4,8,14]));head_local=[round(float(gx.mean()-hx.mean())),int(gy.min()-hy.min())];head_world=records[n]['head_world'];origin=[head_world[0]-head_local[0],head_world[1]-head_local[1]]
 authored=np.zeros((384,384),np.uint8);authored[160+origin[1]:160+origin[1]+h,160+origin[0]:160+origin[0]+w]=native;before=render(arc,1,5,n)[0];stored=np.zeros_like(before);stored[64:256,64:256]=saved[str(n)];assert np.array_equal(stored,before),f'Current differs from authored victory {n}'
 # Area votes sample the same authored pixel footprint, not a resized whole pose.
 votes=np.zeros((h,w,16),np.float32)
 for y in range(h):
  for x in range(w):
   block=a[math.floor(y/.095):min(a.shape[0],math.ceil((y+1)/.095)),math.floor(x/.095):min(a.shape[1],math.ceil((x+1)/.095))];mask=block[:,:,3]>=220
   if not mask.any():continue
   values=block[mask,:3].astype(np.float32);ix=1+np.argmin(((values[:,None,:]-colors[None,1:])**2).sum(2),1);votes[y,x]=np.bincount(ix,minlength=16)/len(ix)
 fullvotes=np.zeros((384,384,16),np.float32);fullvotes[160+origin[1]:160+origin[1]+h,160+origin[0]:160+origin[0]+w]=votes;proposed=before.copy();editable=np.ones_like(before,bool);xx,yy=head_world;editable[160+yy:160+yy+19,160+xx:160+xx+23]=False;changes=[]
 for y,x in np.argwhere(editable&(authored==before)&np.isin(before,[12,15])):
  col=int(fullvotes[y,x].argmax());old=int(before[y,x]);fraction=float(fullvotes[y,x,col])
  if (old,col)not in((15,12),(15,7),(12,7))or fraction<.4:continue
  # Keep original edge/skin/colored-material neighborhoods; cloth-only evidence.
  neighbors=before[max(0,y-1):y+2,max(0,x-1):x+2]
  if np.count_nonzero(neighbors==0)>0:continue
  proposed[y,x]=col;changes.append({'world':[int(x-160),int(y-160)],'before':old,'after':col,'source_vote':fraction,'source_native_pixel':[int(x-160-origin[0]),int(y-160-origin[1])]})
 targets[f'b1_{n:03d}']=proposed;proof.append({'ref':n,'source_image':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_cell':i,'cell_box':box,'component_crop':cropbox,'scale':.095,'source_native_origin_world':origin,'head_world':head_world,'current_exact_previously_authored_native':True,'changes':changes,'changed_pixels':len(changes)})
np.savez_compressed(OUT/'targets.npz',**targets)
crop=(120,120,200,192);cw,ch=400,384;board=Image.new('RGB',(cw*3,(ch+28)*7),'#65727a');draw=ImageDraw.Draw(board)
for row,n in enumerate([147,1,2,3,4,5,6]):
 before=render(arc,0 if n==147 else 1,0 if n==147 else 5,n)[0];after=targets.get(f'b1_{n:03d}',before);diff=np.zeros_like(before);diff[after!=before]=after[after!=before]
 for col,(v,label)in enumerate(((before,'current'),(after,'source votes'),(diff,'changed only'))):
  p=rgba(v,pal).crop(crop).resize((cw,ch),Image.Resampling.NEAREST);board.paste(p,(col*cw,row*(ch+28)+28),p);draw.text((col*cw+4,row*(ch+28)+5),str(n)+' '+label,font=font,fill='white')
board.save(OUT/'comparison.png');report={'source_arc_sha256':hashlib.sha256(arc).hexdigest(),'rule':'Exact original affine grid; source area dominant midtone>=0.4, only current matching white/lightgray cloth interiors. Head/alpha/edge/body geometry unchanged. Candidate visual review only.','frames':proof,'game_changed':False,'native_packed':False};(OUT/'inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'changed':{r['ref']:r['changed_pixels']for r in proof}}))
