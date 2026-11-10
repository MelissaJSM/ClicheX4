"""수용 정면156와 새원화의 손/다리 배치를 좌표판으로 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
def main():
 o=H/'ultimate_return_pose_inspection01';need(not o.exists(),'Fresh inspection');o.mkdir();b=Archive((H/'prepared_hurt_base01/PL00_U.ARC').read_bytes());images=[('accepted new base156',b.composite(156,0)[0]),('new before156',Image.open(H/'ultimate_return_native01/before_156.png').convert('RGBA')),('new after156',Image.open(H/'ultimate_return_native01/after_156.png').convert('RGBA'))];x0,y0,x1,y1=-21,-26,22,25;scale=12;w=(x1-x0)*scale;h=(y1-y0)*scale;out=Image.new('RGB',((w+30)*3,h+65),(29,33,40));dr=ImageDraw.Draw(out);rows=[]
 for col,(name,im)in enumerate(images):
  cut=im.crop((x0+160,y0+160,x1+160,y1+160)).resize((w,h),Image.Resampling.NEAREST);ox=col*(w+30)+26;oy=28;out.paste(cut,(ox,oy),cut);dr.text((ox,7),name,fill='white')
  for x in range(x0,x1):
   xx=ox+(x-x0)*scale;dr.line((xx,oy,xx,oy+h),fill=(65,65,65))
   if x%4==0:dr.text((xx,oy+h+5),str(x),fill='white')
  for y in range(y0,y1):
   yy=oy+(y-y0)*scale;dr.line((ox,yy,ox+w,yy),fill=(65,65,65))
   if y%4==0:dr.text((ox-24,yy),str(y),fill='white')
  rows.append({'name':name,'metrics':metrics(im)})
 out.save(o/'pose_grid.png');write(o/'report.json',{'rows':rows,'wholebody_resize_allowed':False,'art_updated':False,'findings':['新 원화는 양발이 같은 높이로 나란히 놓였지만 수용기본156은 발이 앞뒤로 어긋난 자세다.','새 손끝도 양쪽3px 안쪽으로 이동했다.이 판은bbox만으로 미술실패를 판단하는 것이 아니라 실제손/발 관절을 확인하기 위한 증거다.']});print(o)
if __name__=='__main__':main()
