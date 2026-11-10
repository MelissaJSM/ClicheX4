"""승리206/207 새머리·사지 공통화와 원접점1px 강체 모듈 정합 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def poly(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def main():
 o=H/'ultimate_victory_late_common01';need(not o.exists(),'Fresh candidate');o.mkdir();s=H/'ultimate_victory_native02';a=Archive((H/'prepared_ultimate_arrival_partial01/PL02_U.ARC').read_bytes());rgb=np.array([[(int(w)>>z&31)*255//31 for z in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);rows=[];pics={'before':[],'after':[]};yy,xx=np.indices((384,384));yy-=160;xx-=160
 for n in(206,207):
  original={f:np.array(Image.open(s/f'{f}_{n:03}_indices.png'))for f in('before','after')};before=original['before'].copy();v=original['after'].copy();arm=np.zeros_like(v,bool)
  if n==206:
   donor=np.array(Image.open(H/'ultimate_victory206_arm_native01/after_206_indices.png'));arm=poly([(4,-18),(9,-18),(10,-13),(7,-11),(6,-7),(3,-2),(-1,-2),(1,-6),(2,-10),(2,-13)]);v[arm]=donor[arm];need(np.array_equal(v[~arm],original['after'][~arm]),'Arm outside changed')
  head=poly([(-17,-26),(4,-26),(6,-20),(5,-16),(4,-14),(3,-11),(2,-8),(-1,-5),(-4,-3),(-8,-5),(-13,-8),(-17,-13)])
  head|=poly([(10,-10),(13,-8),(14,-1),(13,4),(14,8),(9,13),(7,14),(6,11),(7,8),(6,4),(7,0),(5,-3),(7,-5),(9,-4)])
  legs=poly([(-11,9),(-6,9),(-4,10),(-5,13),(-8,16),(-8,18),(-5,20),(-5,24),(-16,24),(-16,19),(-12,16),(-11,13)])|poly([(-1,9),(4,9),(5,12),(7,15),(7,18),(10,19),(10,24),(2,24),(1,18),(-2,15),(-2,11)])
  hands=((xx>=4)&(xx<=9)&(yy>=-18)&(yy<=-14))if n==206 else((xx>=1)&(xx<=10)&(yy>=-29)&(yy<=-22))
  hands|=(xx>=-15)&(xx<=-9)&(yy>=-3)&(yy<=1)
  # 새 샌들/발목은 전체 몸을 늘리지 않고 1px 아래로 강체 등록한다.
  # y16 접속행은 원위치에도 남기고 모듈의 모든 원시셀을 +1 위치에 보존.
  foot=((xx>=-16)&(xx<=-4))|((xx>=0)&(xx<=10));foot&=yy>=16
  shifted=np.roll(before,1,axis=0);destination=np.roll(foot,1,axis=0);before[foot&(yy>16)]=0;before[destination]=shifted[destination]
  # 207의 맨 위 주먹/손목도 새 원화 그대로 1px 위에 등록한다.
  raised=np.zeros_like(v,bool)
  if n==207:
   raised=(xx>=0)&(xx<=11)&(yy<=-21);src=before.copy();before[raised&(yy<-21)]=0;dest=np.roll(raised,-1,axis=0);before[dest]=np.roll(src,-1,axis=0)[dest]
  common=head|legs|hands|foot|np.roll(foot,1,axis=0)|raised|np.roll(raised,-1,axis=0);v[common]=lut[before][common]
  outside=(v>0)&(before==0);y,x=np.nonzero(outside);lab,c=label(v>0,np.ones((3,3)))
  for form,val,pal,mask in(('before',before,16,15),('after',v,0,0)):
   Image.fromarray(val).save(o/f'{form}_{n:03}_indices.png');im=a.rgba(val,pal);im.save(o/f'{form}_{n:03}.png');pics[form].extend([(f'{n} old {form}',a.composite(n,mask)[0]),(f'{n} new common {form}',im)])
  for name,m in(('head',head),('legs',legs),('hands',hands),('common',common),('after_arm_donor',arm),('foot_source',foot),('raised_hand_source',raised),('outside_before',outside)):Image.fromarray(m.astype(np.uint8)*255).save(o/f'{n:03}_{name}_mask.png')
  rows.append({'ref':n,'outside_before':[[int(px)-160,int(py)-160,int(v[py,px])]for py,px in zip(y,x)],'after_components':sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True),'before_metrics':metrics(a.rgba(before,16)),'after_metrics':metrics(a.rgba(v)),'foot_registration_delta':[0,1],'raised_hand_registration_delta':[0,-1]if n==207 else[0,0],'contact_seam_rows_preserved':[16]+([-21]if n==207 else[]),'body_resize':False,'old_art_copied':False})
 for form,mask in(('before',15),('after',0)):page(pics[form],a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
 write(o/'report.json',{'rows':rows,'source_report_sha256':sha((s/'report.json').read_bytes()),'local_arm_report_sha256':sha((H/'ultimate_victory206_arm_native01/report.json').read_bytes()),'palette_before_to_after':lut.tolist(),'arc_written':False,'source_existing_pixel_regions_only':True,'visual_review_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
