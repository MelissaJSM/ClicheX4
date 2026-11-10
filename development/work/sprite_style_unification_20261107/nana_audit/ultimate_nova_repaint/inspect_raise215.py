"""새215 주먹/팔의 좌표와 등록 마스크를 읽는 확대판."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write
def grid(a,z,start,path,b=(-5,-27,24,8)):
 scale=20;pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[start:start+16]],int);board=Image.new('RGB',((b[2]-b[0])*scale+36,(b[3]-b[1])*scale+24),'#b9c1c7');dr=ImageDraw.Draw(board)
 for y in range(b[1],b[3]):
  dr.text((0,(y-b[1])*scale+24),str(y),fill='black')
  for x in range(b[0],b[2]):
   i=int(z[y+160,x+160]);px=(x-b[0])*scale+36;py=(y-b[1])*scale+24
   if y==b[1]:dr.text((px,0),str(x),fill='black')
   if i:dr.rectangle((px,py,px+scale-1,py+scale-1),fill=tuple(int(c)for c in pal[i]));dr.text((px+4,py+3),hex(i)[2:].upper(),fill='white'if i<7 else'black')
 board.save(path)
def main():
 out=D/'raise215_grid_v1';out.mkdir(exist_ok=False);meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());old=a.layer(215)[0].copy()
 for pb in(8,5,7,6):v=a.layer(215,pb)[0];old[v>0]=v[v>0]
 grid(a,old,16,out/'old_before.png')
 for form,start in(('before',16),('after',0)):grid(a,np.array(Image.open(D/f'raise215_fixed_v1/{form}_215_indices.png')),start,out/f'{form}.png')
 print('3 coordinate grids saved')
if __name__=='__main__':main()
