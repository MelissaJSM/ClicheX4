"""신규 두 의상 등록의 좌표/재질 경계를 검토하는 읽기 전용 표."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,write,helper
from make_body_cycle import source
def after(n):
 f='first'if n in(33,39,47,51)else'second'if n in(35,37,41,43)else'last'
 return D/f'after_{f}_registered_v1/after_{n:03}.png'
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());o=D/'costume_boundary_grids_v1';o.mkdir(exist_ok=False)
 font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13)
 for n in range(33,55,2):
  ims=[]
  for name,path,off in [('before',source(n),16),('after',after(n),0)]:
   v=np.array(Image.open(path));im=Image.new('RGB',(760,800),'#bec6cc');d=ImageDraw.Draw(im);d.text((5,2),f'{n} {name}',font=font,fill='black');pal=np.array(a.rgba(v,off))
   for x in range(-16,22):d.text(((x+16)*19+35,22),str(x),font=font,fill='black')
   for y in range(-24,14):
    d.text((2,(y+24)*19+45),str(y),font=font,fill='black')
    for x in range(-16,22):
     idx=int(v[y+160,x+160]);px,py=(x+16)*19+35,(y+24)*19+45
     if idx:d.rectangle((px,py,px+18,py+18),fill=tuple(pal[y+160,x+160,:3]));d.text((px+4,py+1),hex(idx)[2:].upper(),font=font,fill='white'if idx in(1,2,5,6)else'black')
     d.rectangle((px,py,px+18,py+18),outline='#84949d',width=1)
   ims.append(im)
  out=Image.new('RGB',(1520,800));out.paste(ims[0],(0,0));out.paste(ims[1],(760,0));out.save(o/f'{n:03}.png')
 print(o)
if __name__=='__main__':main()
