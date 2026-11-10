"""승리 후보의 새 원화 부위만 좌표 격자로 열람한다. 이미지 수정 없음."""
from pathlib import Path
import sys, json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent; ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,write,sha
from scripts.export_x_consistency import Archive
def main():
 d=H/'ultimate_victory_regions01';need(not d.exists(),'Fresh inspection');d.mkdir()
 a=Archive((H/'prepared_ultimate_hurt02/PL02_U.ARC').read_bytes());rows=[]
 for ref,src,box in [(204,'ultimate_victory_common_probe01',(-25,-10,-4,9)),(206,'ultimate_victory_native02',(-5,-26,14,-2)),(207,'ultimate_victory_native02',(-17,9,14,24))]:
  x0,y0,x1,y1=box;scale=24;w=(x1-x0)*scale;h=(y1-y0)*scale;out=Image.new('RGB',(w*2+80,h+70),(30,34,41));draw=ImageDraw.Draw(out)
  vals={}
  for col,(form,pal) in enumerate([('before',16),('after',0)]):
   p=H/src/f'{form}_{ref:03}_indices.png';v=np.array(Image.open(p));vals[form]=v[y0+160:y1+160,x0+160:x1+160].tolist();im=a.rgba(v,pal).crop((x0+160,y0+160,x1+160,y1+160)).resize((w,h),Image.Resampling.NEAREST);ox=col*(w+40)+30;oy=35;out.paste(im,(ox,oy),im);draw.text((ox,5),f'{ref} {form}',fill='white')
   for x in range(x0,x1):
    xx=ox+(x-x0)*scale;draw.line((xx,oy,xx,oy+h),fill=(75,75,75));draw.text((xx,oy+h+4),str(x),fill='white')
   for y in range(y0,y1):
    yy=oy+(y-y0)*scale;draw.line((ox,yy,ox+w,yy),fill=(75,75,75));draw.text((ox-28,yy+5),str(y),fill='white')
  out.save(d/f'{ref:03}_grid.png');rows.append({'ref':ref,'source':src,'box':box,'indices':vals})
 write(d/'report.json',{'rows':rows,'pixels_modified':False});print(d)
if __name__=='__main__':main()
