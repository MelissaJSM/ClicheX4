"""승리 양의상의 머리/목/팔/옷 경계 좌표를 읽기 전용으로 표시한다."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive
def source(form,n):return D/f'{"a"if n<206 else"b"}_registered_v1/{form}_{n:03}_indices.png'
def main():
 a=Archive((N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC').read_bytes());out=D/'semantic_grids_v1';out.mkdir(exist_ok=False)
 for n in(204,205,206,207):
  x0,y0,x1,y1=-18,-32 if n==207 else -21,18,8;s=22;w=(x1-x0)*s+50;h=(y1-y0)*s+55;board=Image.new('RGB',(w*2,h),'#b6c0c7');dr=ImageDraw.Draw(board)
  for i,(form,pal)in enumerate((('before',16),('after',0))):
   z=np.array(Image.open(source(form,n)));ox=i*w+38;oy=48;pic=a.rgba(z,pal).crop((160+x0,160+y0,160+x1,160+y1)).resize(((x1-x0)*s,(y1-y0)*s),Image.Resampling.NEAREST);board.paste(pic,(ox,oy),pic);dr.text((ox,3),f'{n} {form}',fill='black')
   for x in range(x0,x1):dr.text((ox+(x-x0)*s,28),str(x),fill='black')
   for y in range(y0,y1):dr.text((ox-32,oy+(y-y0)*s),str(y),fill='black')
   for x in range(x0,x1+1):dr.line((ox+(x-x0)*s,oy,ox+(x-x0)*s,oy+(y1-y0)*s),fill='#879099')
   for y in range(y0,y1+1):dr.line((ox,oy+(y-y0)*s,ox+(x1-x0)*s,oy+(y-y0)*s),fill='#879099')
  board.save(out/f'grid_{n}.png')
if __name__=='__main__':main()
