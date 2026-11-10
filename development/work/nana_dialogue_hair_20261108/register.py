"""Register generated repairs while keeping approved face, costume and other forms."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
OLD=ROOT/'work/armor_dialogue_20261108/ver_rin_nana/native_proposal'
palette=Image.open(OLD/'00.png').getpalette();rgb=np.array(palette,dtype=np.int32).reshape(-1,3)[:16]
original={n:np.array(Image.open(OLD/f'{n:02}.png'))for n in range(12)}
sheet=Image.open(H/'generated.png').convert('RGBA')
def native(im):
 im=im.convert('RGBa').resize((112,94),Image.Resampling.LANCZOS).convert('RGBA');a=np.array(im)
 out=np.zeros((96,112),np.uint8);d=((a[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[1:])**2).sum(3)
 out[:94]=np.where(a[:,:,3]>=192,d.argmin(2)+1,0);return out
generated={}
for n in range(4):
 x0,x1=(0,677)if n%2==0 else(677,1355);y0,y1=(0,568)if n<2 else(576,1160)
 generated[n]=native(sheet.crop((x0,y0,x1,y1)))

out=H/'native_v1';out.mkdir(exist_ok=False);targets={n:a.copy()for n,a in original.items()}
face=Image.new('1',(112,96));d=ImageDraw.Draw(face)
d.polygon([(58,39),(68,43),(85,46),(85,52),(78,61),(73,63),(62,57),(58,48)],fill=1)
face=np.array(face)
mask=np.zeros((96,112),bool);mask[54:82,:]=True;mask[32:82,84:]=True;mask[32:82,42:62]=True
mask &=~face
for n in [1,2,3]:
 a=targets[n];a[mask]=generated[n][mask]
 mouth=original[n]!=original[n+4];b=a.copy();b[mouth]=original[n+4][mouth];targets[n+4]=b
board=Image.new('RGB',(1344,960),(32,40,55));d=ImageDraw.Draw(board);patterns=set();counts=[]
for n,a in targets.items():
 im=Image.fromarray(a,'P');im.putpalette(palette);im.info['transparency']=0;im.save(out/f'{n:02}.png');im=im.convert('RGBA');board.paste(im.resize((336,288),0),(n%4*336,n//4*320+28),im.resize((336,288),0));d.text((n%4*336+4,n//4*320+4),str(n),fill='white')
 for y in range(0,96,16):
  for x in range(0,112,16):patterns.add(a[y:y+16,x:x+16].tobytes())
 counts.append((n,len(patterns)))
board.save(out/'review.png');(out/'capacity.json').write_text(json.dumps(counts,indent=2),'utf8');print(counts)
