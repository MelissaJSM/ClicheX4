"""새승리204/205 의상 공통부의 좌표/알파 차이를 읽고 확대판을 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def main():
 d=H/'ultimate_victory_common_inspection01';need(not d.exists(),'Fresh inspection');d.mkdir();s=H/'ultimate_victory_native01';a=Archive((H/'prepared_ultimate_hurt02/PL02_U.ARC').read_bytes());rows=[]
 for n in(204,205):
  b=np.array(Image.open(s/f'before_{n:03}_indices.png'));v=np.array(Image.open(s/f'after_{n:03}_indices.png'));m=(v>0)&(b==0);y,x=np.nonzero(m);rows.append({'ref':n,'outside_before':[[int(xx)-160,int(yy)-160,int(v[yy,xx])]for yy,xx in zip(y,x)]})
  board=Image.new('RGB',(1080,1000),(27,31,39));dr=ImageDraw.Draw(board)
  for col,(name,im)in enumerate((('new before',a.rgba(b,16)),('new after',a.rgba(v,0)))):
   crop=im.crop((136,132,180,188)).resize((528,672),Image.Resampling.NEAREST);board.paste(crop,(col*540,35),crop);dr.text((col*540+8,8),f'{n} {name}',fill='white')
   for xx in range(-24,20,4):dr.text((col*540+(xx+24)*12,714),str(xx),fill='white')
   for yy in range(-28,28,4):dr.text((col*540+2,35+(yy+28)*12),str(yy),fill='#cccccc')
   if col==1:
    for yy,xx in zip(y,x):px=col*540+(xx-136)*12;py=35+(yy-132)*12;dr.rectangle((px,py,px+11,py+11),outline='#ff3333',width=2)
  board.save(d/f'{n:03}_body_grid.png')
 write(d/'report.json',{'source':str(s.relative_to(ROOT)),'source_report_sha256':sha((s/'report.json').read_bytes()),'rows':rows,'pixels_modified':False,'arc_written':False})
 print(json.dumps(rows))
if __name__=='__main__':main()
