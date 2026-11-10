"""등록·팔레트·공간 검토 후보. 게임 BIN 변경 없음."""
from pathlib import Path
import sys,struct,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));H=Path(__file__).resolve().parent/'ver_rin_nana'
from scripts.prepare_riko_ui import entry
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_ui_render import render_static_rgba
arc=(H/'originals/ST00_00.ARC').read_bytes();g=entry(arc,0x10102)[204800:217088];parts=entry(arc,10);pal=entry((H/'originals/COL00_0X.ARC').read_bytes(),5)[62*32:63*32];words=struct.unpack('<16H',pal);rgb=np.array([[int(w>>s&31)*255//31 for s in [0,5,10]] for w in words],np.int32)
base=np.frombuffer(compose_static(g,local_composition(aliased_composition(parts,11,0)))[0],np.uint8).reshape(96,112);opened=np.frombuffer(compose_static(g,local_composition(aliased_composition(parts,11,4)))[0],np.uint8).reshape(96,112)
def native(im):
 im=im.convert('RGBA');alpha=np.array(im)[:,:,3]>=192;box=None
 for y in range(im.height-1,int(im.height*.8),-1):
  runs=np.diff(np.r_[False,alpha[y],False].astype(np.int8));starts=np.where(runs==1)[0];ends=np.where(runs==-1)[0]
  if len(starts):
   j=int(np.argmax(ends-starts))
   if ends[j]-starts[j]>=im.width*.94:box=(int(starts[j]),0,int(ends[j]),y+1);break
 assert box is not None,'Generated lower edge needs correction'
 im=im.crop(box).convert('RGBa').resize((112,94),Image.Resampling.LANCZOS).convert('RGBA');a=np.array(im);d=((a[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[1:])**2).sum(3);out=np.zeros((96,112),np.uint8);out[:94]=np.where(a[:,:,3]>=192,d.argmin(2)+1,0);return out
force=native(Image.open(H/'force_generated.png'));u=Image.open(H/'ultimate_generated.png');left=native(u.crop((0,0,u.width//2,u.height)));right=native(u.crop((u.width//2,0,u.width,u.height)))
# The accepted facial region is invariant; costume-only edits retain its eyes,
# cheek/forelock detail, closed-mouth placement and dialogue animation pixels.
for a in [force,left,right]:a[32:65,56:96]=base[32:65,56:96]
# Both Ultimate portraits share exactly the same head. The old hair outside the
# new headband region is retained, not a separately generated/shifted face.
for a in [left,right]:
 a[32:64]=base[32:64]
left[:64]=right[:64]
targets={}
for n in range(8):
 a=base.copy()
 if n&1:a[:64]=force[:64]
 if n&2:a[64:]=force[64:]
 if n&4:a[base!=opened]=opened[base!=opened]
 targets[n]=a
for n,a in [(8,left),(9,right),(10,left),(11,right)]:
 b=a.copy()
 if n>=10:b[base!=opened]=opened[base!=opened]
 targets[n]=b
out=H/'native_proposal';out.mkdir(exist_ok=True);board=Image.new('RGB',(1344,960),(32,40,55));draw=ImageDraw.Draw(board);patterns=set();counts=[]
for n,a in targets.items():
 im=Image.fromarray(a,'P');im.putpalette(rgb.astype(np.uint8).reshape(-1).tolist()+[0]*(768-48));im.info['transparency']=0;im.save(out/f'{n:02}.png');im=im.convert('RGBA');big=im.resize((336,288),Image.Resampling.NEAREST);board.paste(big,(n%4*336,n//4*320+28),big);draw.text((n%4*336+4,n//4*320+4),str(n),fill='white')
 for y in range(0,96,16):
  for x in range(0,112,16):patterns.add(a[y:y+16,x:x+16].tobytes())
 counts.append([n,len(patterns)])
board.save(out/'review.png');(out/'capacity.json').write_text(json.dumps({'incremental_unique_16x16_tiles':counts,'capacity':96,'fits':len(patterns)<=96},indent=2)+'\n','utf8');print(counts)
