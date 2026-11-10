"""새승리 첫2키의 새머리/사지와 국소204팔만 정합. 구형그림 복사 없음."""
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
 o=H/'ultimate_victory_common_probe01';need(not o.exists(),'Fresh common candidate');o.mkdir();s=H/'ultimate_victory_native01';a=Archive((H/'prepared_ultimate_hurt02/PL02_U.ARC').read_bytes());rgb=np.array([[(int(w)>>z&31)*255//31 for z in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);inverse=np.r_[0,1+((rgb[1:16,None]-rgb[None,17:32])**2).sum(2).argmin(1)].astype(np.uint8);rows=[];pics={'before':[],'after':[]};yy,xx=np.indices((384,384));yy-=160;xx-=160
 for n in(204,205):
  b=np.array(Image.open(s/f'before_{n:03}_indices.png'));old=np.array(Image.open(s/f'after_{n:03}_indices.png'));v=old.copy();arm=np.zeros_like(b,bool)
  if n==204:
   donor=np.array(Image.open(H/'ultimate_victory204_arm_native01/after_204_indices.png'));arm=(xx>=-24)&(xx<=-5)&(yy>=-6)&(yy<=5);v[arm]=donor[arm];need(np.array_equal(v[~arm],old[~arm]),'Outside arm changed')
  # The small left braid newly visible beneath205's raised arm is common
  # hair, not fabric. Add only these source-existing hair cells to the
  # before silhouette rather than clipping the accepted bare-arm hair.
  addition=(b==0)&(v>0)&(xx>=-16)&(xx<=-12)&(yy>=1)&(yy<=6)if n==205 else np.zeros_like(b,bool)
  before=b.copy();before[addition]=inverse[v][addition]
  head=poly([(-16,-25),(8,-25),(10,-18),(8,-12),(9,-7),(6,-3),(2,-3),(-1,-4),(-7,-4),(-11,-5),(-15,-9),(-17,-13)])
  head|=poly([(6,-14),(12,-14),(12,-9),(15,-5),(12,-4),(13,-1),(16,1),(14,4),(15,8),(12,10),(11,14),(7,14),(8,10),(6,8),(8,5),(7,1),(7,-3),(5,-7)])
  if n==205:head[(xx<-8)&(yy>-16)]=False
  legs=poly([(-12,9),(-7,9),(-3,12),(-6,16),(-6,23),(-16,23),(-16,17),(-11,14)])|poly([(-1,9),(4,9),(5,11),(9,15),(9,18),(13,20),(13,23),(6,23),(3,18),(0,15),(-1,12)])
  hands=((xx>=-24)&(xx<=-18)&(yy>=-7)&(yy<=-2))if n==204 else((xx>=-13)&(xx<=-6)&(yy>=-18)&(yy<=-11))
  hands|=(xx>=-1)&(xx<=4)&(yy>=2)&(yy<=7);hands&=np.isin(before,[10,11,12,13]);common=head|legs|hands;v[common]=lut[before][common];outside=(v>0)&(before==0);y,x=np.nonzero(outside);lab,c=label(v>0,np.ones((3,3)))
  for form,val,pal,mask in(('before',before,16,15),('after',v,0,0)):
   Image.fromarray(val).save(o/f'{form}_{n:03}_indices.png');im=a.rgba(val,pal);im.save(o/f'{form}_{n:03}.png');pics[form].extend([(f'{n} old {form}',a.composite(n,mask)[0]),(f'{n} new common {form}',im)])
  for name,m in(('head',head),('legs',legs),('hands',hands),('common',common),('after_arm_donor',arm),('before_braid_addition',addition),('outside_before',outside)):Image.fromarray(m.astype(np.uint8)*255).save(o/f'{n:03}_{name}_mask.png')
  rows.append({'ref':n,'after_arm_donor_changed_pixels':int(((v!=old)&arm).sum()),'before_braid_new_source_cells_added':int(addition.sum()),'before_outside_addition_exact':bool(np.array_equal(before[~addition],b[~addition])),'outside_before':[[int(px)-160,int(py)-160,int(v[py,px])]for py,px in zip(y,x)],'after_components':sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True),'before_metrics':metrics(a.rgba(before,16)),'after_metrics':metrics(a.rgba(v))})
 for form,mask in(('before',15),('after',0)):page(pics[form],a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
 write(o/'report.json',{'rows':rows,'source_report_sha256':sha((s/'report.json').read_bytes()),'local_arm_source':{'path':'ultimate_victory204_arm_native01/after_204_indices.png','sha256':sha((H/'ultimate_victory204_arm_native01/after_204_indices.png').read_bytes())},'palette_before_to_after':lut.tolist(),'palette_after_to_before':inverse.tolist(),'old_art_copied':0,'global_body_resize':False,'arc_written':False,'source_existing_pixel_regions_only':True,'visual_review_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
