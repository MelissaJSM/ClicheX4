"""라이징 신규 6자세의 총·손·발 색인 좌표를 변형 없이 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need,sha
REFS=(100,101,102,103,104,231)
Y,X=np.indices((384,384));Y-=160;X-=160
def path(form,n):
 page='charge' if n in(100,101) else 'air' if n in(103,104) else 'recovery_ground'
 return D/f'{page}_registered_v1/{form}_{n:03}_indices.png'
def merged(a,n,mask):
 z=a.layer(n)[0].copy()
 if mask:
  for pb in(8,5,7,6):
   v=a.layer(n,pb)[0];z[v>0]=v[v>0]
 return z
def main():
 src=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';need(digest(src)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','Source');a=Archive(src.read_bytes())
 out=D/'contact_grids_v1';out.mkdir(exist_ok=False);records=[];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',11)
 for n in REFS:
  for kind,roi in [('gun',(-18,-43,16,-16)),('feet',(-19,0,22,27))]:
   w,h=roi[2]-roi[0],roi[3]-roi[1];scale=20;cv=Image.new('RGB',(w*scale*2,h*scale*2+80),'#bec9d0');dr=ImageDraw.Draw(cv)
   for j,(form,mask) in enumerate([('base',0),('fourth',15)]):
    old=merged(a,n,mask);p=path(form,n);new=np.array(Image.open(p));start=16 if mask else 0
    for k,(label,z) in enumerate([('parent',old),('new',new)]):
     left=k*w*scale;top=j*(h*scale+40)+40
     im=a.rgba(z,start).crop(tuple(v+160 for v in roi)).resize((w*scale,h*scale),Image.Resampling.NEAREST);cv.paste(im,(left,top),im);dr.text((left+3,top-37),f'{form} {n} / {label}',fill='black')
     for yy in range(h):
      for xx in range(w):
       v=int(z[roi[1]+yy+160,roi[0]+xx+160]);px=left+xx*scale;py=top+yy*scale
       dr.rectangle((px,py,px+scale-1,py+scale-1),outline='#84939b')
       if v:dr.text((px+3,py+2),format(v,'X'),font=font,fill='white' if v in(1,2,3,5,6,7) else 'black')
     for xx in range(0,w,2):dr.text((left+xx*scale,top-16),str(roi[0]+xx),font=font,fill='black')
     for yy in range(0,h,2):dr.text((left+1,top+yy*scale),str(roi[1]+yy),font=font,fill='#a00000')
    if kind=='feet':records.append({'ref':n,'form':form,'source':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'old_lower_rows':[[yy-160,np.flatnonzero(old[yy]).tolist()]for yy in range(170,187)],'new_lower_rows':[[yy-160,np.flatnonzero(new[yy]).tolist()]for yy in range(170,187)]})
   cv.save(out/f'{n:03}_{kind}.png')
 palettes=[]
 for start in(0,16):palettes.append({'start':start,'words':[int(v)for v in a.words[start:start+16]],'rgb':[[int(w)>>s&31 for s in(0,5,10)]for w in a.words[start:start+16]]})
 write(out/'manifest.json',{'source_arc_sha256':digest(src),'frames':records,'palettes':palettes,'source_pixels_modified':False,'native_packed':False,'runtime_verified':False})
 print(out)
if __name__=='__main__':main()
