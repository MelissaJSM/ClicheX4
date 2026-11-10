"""생성 원화의 의상 부분만 네이티브 인덱스로 등록. 다른 픽셀 보호."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import board,write,sha
from scripts.export_x_consistency import Archive
from pack import pack
PBS=(0,5,6,7,8)
# Neckline / waist / hem (left, right, y), in unchanged native world space.
REGIONS={
85:[(-5,0,-4),(-5,1,2),(-8,5,8)],86:[(-5,1,-3),(-5,1,3),(-7,4,9)],87:[(-5,1,-3),(-5,1,3),(-7,4,9)],
89:[(-5,1,-2),(-6,1,3),(-9,4,9)],90:[(-6,0,1),(-6,1,5),(-9,3,10)],91:[(-6,0,1),(-6,1,5),(-9,3,10)],92:[(-4,1,-3),(-4,1,3),(-7,4,9)],
231:[(-4,2,-4),(-4,3,4),(-7,6,12)],95:[(-4,1,-4),(-4,2,2),(-8,5,8)],97:[(-4,1,-3),(-4,2,3),(-7,6,9)],98:[(-4,3,0),(-4,4,5),(-9,10,10)],101:[(-4,2,-5),(-4,3,1),(-6,4,7)],
106:[(-4,1,-2),(-4,2,4),(-7,6,10)],110:[(-2,4,1),(-2,5,6),(-3,7,10)],120:[(-3,3,-1),(-3,4,4),(-7,7,10)],124:[(-3,3,-2),(-3,4,3),(-7,7,9)],
133:[(-1,5,3),(-1,6,7),(-5,9,12)],135:[(-4,2,-2),(-4,3,4),(-7,6,10)],137:[(-4,3,-4),(-4,4,3),(-7,8,10)],138:[(-2,3,-6),(-2,4,1),(-5,7,7)],
156:[(-4,3,-3),(-4,4,3),(-7,7,10)],162:[(-2,3,1),(-2,5,5),(-4,8,10)],166:[(-2,3,1),(-2,5,5),(-4,8,10)],170:[(-1,4,1),(-1,6,5),(-3,8,11)],
204:[(-4,2,-3),(-4,3,3),(-7,7,11)],205:[(-4,2,-3),(-4,3,3),(-7,7,11)],206:[(-4,2,-3),(-4,3,3),(-7,7,11)],207:[(-4,2,-3),(-4,3,3),(-7,7,11)],
213:[(-2,4,1),(-2,5,6),(-4,7,11)],215:[(-3,3,-4),(-3,4,3),(-5,7,10)],217:[(-2,5,6),(1,7,10),(0,10,14)],
221:[(-4,2,0),(-4,3,6),(-7,6,13)],223:[(-4,2,0),(-4,3,6),(-7,6,13)],225:[(-3,3,0),(-3,4,6),(-6,7,12)],227:[(-3,3,0),(-3,4,6),(-6,7,12)],229:[(-4,2,0),(-4,3,6),(-7,6,13)]}
REGIONS.update({
231:[(-6,0,-1),(-5,2,5),(-8,7,11)],95:[(-5,0,-1),(-5,1,4),(-9,5,10)],98:[(-4,3,3),(-4,4,7),(-9,10,13)],101:[(-6,-2,-1),(-6,-1,3),(-7,1,7)],
106:[(-7,-2,0),(-7,-1,4),(-10,2,10)],110:[(-9,-4,0),(-9,-3,4),(-10,-2,8)],120:[(-5,1,-2),(-5,2,3),(-8,5,8)],124:[(-6,0,-4),(-6,1,1),(-8,4,6)],
133:[(-6,-2,7),(-6,0,10),(-5,3,14)],135:[(-6,-1,-1),(-6,0,4),(-9,4,10)],137:[(-6,-1,-2),(-7,0,2),(-9,3,7)],138:[(-7,-3,-2),(-8,-1,3),(-8,0,8)],
162:[(2,5,1),(3,8,4),(1,10,8)],166:[(3,6,1),(3,8,4),(3,10,9)],170:[(4,7,4),(4,8,7),(2,10,11)],
204:[(-8,-3,-3),(-8,-1,2),(-9,2,8)],205:[(-8,-3,-3),(-8,-1,2),(-9,2,8)],206:[(-7,-2,-3),(-7,0,2),(-8,3,8)],207:[(-7,-2,-3),(-7,0,2),(-8,3,8)],
213:[(-4,0,8),(-4,2,11),(-4,4,15)],215:[(-7,-2,-3),(-7,0,2),(-8,1,8)],217:[(-11,-7,3),(-10,-5,7),(-10,-3,11)],
221:[(-7,-2,-3),(-7,0,3),(-8,6,9)],223:[(-8,-3,-3),(-8,-1,3),(-9,5,9)],225:[(-7,-2,-4),(-7,0,1),(-10,3,6)],227:[(-7,-3,-3),(-8,-1,3),(-8,3,7)],229:[(-8,-3,-4),(-8,0,0),(-10,3,5)]})
REGIONS.update({102:[(-6,-2,-1),(-6,-1,4),(-7,3,8)],233:[(-5,1,-2),(-5,2,3),(-6,5,8)],234:[(-5,1,1),(-5,2,5),(-6,5,9)],136:[(-5,1,-1),(-5,2,3),(-8,6,8)],139:[(-6,0,-2),(-6,1,3),(-9,5,8)],158:[(-4,3,-12),(-4,4,-6),(-7,7,1)],174:[(-6,-1,0),(-6,1,5),(-9,5,10)],100:[(-1,5,8),(-1,5,12),(-4,6,16)]})

def mask_for(n):
 points=REGIONS[n];poly=[(l+160,y+160) for l,r,y in points]+[(r+160,y+160) for l,r,y in points[::-1]]
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon(poly,fill=255)
 return np.array(im)>0

def main():
 a=Archive((H/'PL02_U.ARC').read_bytes());out=H/'candidate';out.mkdir(exist_ok=True)
 rgb=np.array([[(int(w)>>s&31)*255//31 for s in (0,5,10)] for w in a.words[:16]],np.int32)
 rows=[];results={};masks={};pics=[]
 for page in range(4):
  meta=json.loads((H/f'edit_{page}.json').read_text('utf8'));gen=Image.open(H/f'generated_{page}.png').convert('RGBA').resize((meta['grid'][0]*64,meta['grid'][1]*64),Image.Resampling.NEAREST)
  for i,n in enumerate(meta['refs']):
   sample=np.array(gen.crop((i%4*64,i//4*64,i%4*64+64,i//4*64+64)))
   ind=(1+((sample[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);ind[sample[:,:,3]<128]=0
   generated=np.zeros((384,384),np.uint8);generated[128:192,128:192]=ind
   old=np.array(a.composite(n,15 if n>=217 and n<=230 else 0)[0]);oldind=a.layer(n)[0].copy()
   # Hover body is held in layer 5 in the costume-swap implementation.
   if 217<=n<=230:
    for pb in (8,5,7,6):
     v=a.layer(n,pb)[0];oldind[v>0]=v[v>0]
   region=mask_for(n)
   # Register output to the unchanged source head+legs; only translation is permitted.
   anchor=(oldind>0)&~region
   best=None
   for dy in range(-2,3):
    for dx in range(-2,3):
     trial=np.roll(generated,(dy,dx),(0,1));score=int(((oldind==trial)&anchor).sum())-abs(dx)-abs(dy)
     if best is None or score>best[0]:best=(score,dx,dy,trial)
   score,dx,dy,g=best
   # Preserve arms and torso skin. The short garment hem may cover its original
   # top-of-thigh area; all legs below that hem and all other body pixels stay.
   hem=np.indices(oldind.shape)[0]>=160+REGIONS[n][-1][2]-2
   allowed=region&(g>0)&~np.isin(g,[12,13,7])&(~np.isin(oldind,[10,11,12,13])|hem)
   new=oldind.copy();new[allowed]=g[allowed]
   results[n]=new;masks[n]=allowed
   Image.fromarray(allowed.astype('uint8')*255).save(out/f'mask_{n:03}.png');Image.fromarray(new).save(out/f'body_{n:03}.png')
   im=a.rgba(new);pics.extend([(f'{n} old',Image.fromarray(old)),(f'{n} new',im)])
   rows.append({'ref':n,'source_page':page,'translation':[dx,dy],'changed_pixels':int((new!=oldind).sum()),'protected_outside':True})
 for start in range(0,len(pics),16):board(pics[start:start+16],out/f'compare_{start//16:02}.png',cols=4)
 write(out/'registration.json',rows)
 print('Registered',len(rows),'costume patches;',sum(r['changed_pixels'] for r in rows),'pixels')
if __name__=='__main__':main()
