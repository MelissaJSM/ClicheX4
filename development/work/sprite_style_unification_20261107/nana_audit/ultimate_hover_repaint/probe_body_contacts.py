"""새 호버5의 손/신발을 좌표 격자로 읽는다. 원화는 변경하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,helper
def source(n):return D/(f'last_registered_v1/body_{n:03}_indices.png'if n==229 else f'semantic_samples_v1/body_{n:03}_indices.png')
def grid(z,pal,box,path):
 x0,y0,x1,y1=box;s=22;im=Image.new('RGB',((x1-x0)*s+40,(y1-y0)*s+26),'#b9c1c7');d=ImageDraw.Draw(im)
 for y in range(y0,y1):
  d.text((0,26+(y-y0)*s),str(y),fill='black')
  for x in range(x0,x1):
   px,py=40+(x-x0)*s,26+(y-y0)*s;i=int(z[y+160,x+160]);
   if y==y0:d.text((px,0),str(x),fill='black')
   if i:d.rectangle((px,py,px+s-1,py+s-1),fill=tuple(pal[i]));d.text((px+6,py+4),hex(i)[2:].upper(),fill='white'if i<7 else'black')
 im.save(path)
def main():
 out=D/'contact_grids_v1';out.mkdir(exist_ok=False);a=Archive((N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC').read_bytes());pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.uint8);proof=[];rows=[]
 for n in(221,223,225,227,229):
  z=np.array(Image.open(source(n)));old=a.layer(n)[0];legs=a.layer(n,5)[0];old[legs>0]=legs[legs>0]
  for tag,box in(('hands',(-18,-14,10,5)),('feet',(-17,5,24,32))):
   grid(z,pal,box,out/f'new_{n}_{tag}.png');grid(old,pal,box,out/f'old_{n}_{tag}.png')
  proof.append({'ref':n,'source':source(n).relative_to(ROOT).as_posix(),'source_sha256':digest(source(n)),'palette15_cells':[[int(x-160),int(y-160)]for y,x in np.argwhere(z==15)],'iris_cells':[[int(x-160),int(y-160)]for y,x in np.argwhere((z==14)&(np.indices(z.shape)[0]<160))]});rows.append((str(n),[('old hover',a.composite(n,15)[0]),('new fixed candidate',a.rgba(z)),('idle detail',a.composite(0)[0])]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'report.json',{'frames':proof,'scope':'좌표 격자 읽기 전용. 손/총·추진접점 채택/패킹 전.'});print(json.dumps(proof))
if __name__=='__main__':main()
