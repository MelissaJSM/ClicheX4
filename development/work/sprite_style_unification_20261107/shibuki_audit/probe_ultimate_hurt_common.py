"""새 Ultimate 피격4의 공통 머리/사지와234 국소팔 후보. 기존아트 사용없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

HEAD={
106:[[(-18,-26),(18,-26),(18,-3),(12,-3),(8,-2),(5,0),(1,-1),(-4,-1),(-8,-2),(-12,-4),(-18,-4)],[(5,-3),(10,-2),(11,1),(15,4),(14,9),(11,12),(9,11),(8,8),(9,5),(7,2),(4,0)]],
110:[[(-9,-25),(21,-25),(21,-3),(14,0),(9,0),(7,1),(3,-1),(-1,-1),(-5,-2),(-7,-5),(-9,-7)],[(5,-2),(10,-1),(10,4),(13,9),(14,12),(11,16),(8,16),(7,12),(7,8),(5,4),(3,1)]],
233:[[(-16,-26),(17,-26),(17,-4),(11,-3),(7,-2),(3,-2),(0,-2),(-4,-2),(-7,-3),(-12,-4),(-16,-4)],[(4,-4),(10,-3),(11,-1),(15,3),(15,8),(12,10),(9,11),(8,9),(8,4),(6,1),(3,-2)]],
234:[[(-19,-26),(15,-26),(15,-3),(7,-3),(4,-2),(1,0),(-3,0),(-7,-1),(-9,-2),(-12,-3),(-16,-3),(-19,-4)],[(2,-4),(8,-3),(12,0),(14,4),(14,10),(11,14),(8,14),(8,10),(10,8),(9,4),(6,1),(2,-1)]]}
LEGS={
106:[[(-12,13),(-7,12),(-7,18),(-5,20),(-6,26),(-19,26),(-19,20),(-13,18)],[(0,14),(4,14),(8,19),(8,26),(-3,26),(-3,19)]],
110:[[(-17,7),(-13,6),(-10,8),(-10,11),(-7,14),(-7,19),(-12,19),(-14,13),(-17,12)],[(-8,13),(-3,13),(-1,16),(1,18),(1,24),(-5,24),(-5,19),(-9,18)]],
233:[[(-19,5),(-16,4),(-13,5),(-12,8),(-10,9),(-10,13),(-12,18),(-18,18),(-18,12),(-19,9)],[(-7,13),(-4,13),(-4,17),(-2,20),(0,21),(0,26),(-8,26),(-8,21)]],
234:[[(-16,9),(-12,8),(-8,10),(-9,13),(-12,15),(-15,13),(-17,12)],[(-7,15),(-3,14),(-3,16),(-6,19),(-9,21),(-10,25),(-18,25),(-18,20),(-14,18)]]}
HAND_RECTS={106:[(-18,8,-12,11),(3,9,8,12)],110:[(-12,-3,-7,1),(-1,1,3,5)],233:[(-20,2,-17,5),(3,9,7,12)],234:[(-15,-2,-10,3),(-2,1,2,5)]}
ARM234=[(-17,-3),(-10,-4),(-9,-2),(-7,-1),(-5,0),(-4,3),(-3,4),(-3,7),(-7,8),(-12,8),(-14,4),(-17,3)]
ARM234_RIGHT=[(-3,1),(2,0),(5,3),(6,7),(3,9),(0,8),(-2,5)]

def poly(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def regions(polygons):
 r=np.zeros((384,384),bool)
 for p in polygons:r|=poly(p)
 return r
def main():
 o=H/'ultimate_hurt_common_probe02';need(not o.exists(),'Fresh common');o.mkdir();p=H/'prepared_ultimate_ladder01/PL02_U.ARC';a=Archive(p.read_bytes());rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);rows=[];pics={'before':[],'after':[]}
 for n in(106,110,233,234):
  folder=H/('ultimate_hurt_native01'if n<200 else'ultimate_hurt_native02');before=np.array(Image.open(folder/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(folder/f'after_{n:03}_indices.png'));after=fresh.copy();arm=np.zeros_like(before,bool)
  if n==234:
   donor=np.array(Image.open(H/'ultimate_hurt_common_inspection01/after_234_arm_donor_indices.png'));arm=poly(ARM234)|poly(ARM234_RIGHT);after[arm]=donor[arm]
  head=regions(HEAD[n]);legs=regions(LEGS[n]);hands=np.zeros_like(before,bool)
  for x0,y0,x1,y1 in HAND_RECTS[n]:hands[y0+160:y1+160,x0+160:x1+160]=True
  # Only the skin samples in these small rectangles are common, so a jacket
  # cuff in the neighbouring pixels cannot leak into the bare arm.
  hands&=np.isin(before,[10,11,12,13])
  # The right closed fist of106 is shared with its complete new outline,
  # including the one transparent cell between fist and trailing hair.
  if n==106:hands[169:172,163:168]=True
  # This one cell is the tip of the newly generated trailing hair, not skin
  # or costume: use the same new-before contour as the rest of the common hair.
  if n==110:head[173,163]=True
  common=head|legs|hands;after[common]=lut[before][common];outside=(after>0)&(before==0)
  for f,v,pal,mask in(('before',before,16,15),('after',after,0,0)):
   Image.fromarray(v).save(o/f'{f}_{n:03}_indices.png');im=a.rgba(v,pal);im.save(o/f'{f}_{n:03}.png');pics[f].extend([(f'{n} old {f}',a.composite(n,mask)[0]),(f'{n} new common {f}',im)])
  for name,v in(('head',head),('legs',legs),('hands',hands),('common',common),('local_arm',arm),('outside',outside)):Image.fromarray(v.astype(np.uint8)*255).save(o/f'{n:03}_{name}_mask.png')
  rows.append({'ref':n,'source':folder.relative_to(ROOT).as_posix(),'source_files':{f'{f}_{n:03}_indices.png':sha((folder/f'{f}_{n:03}_indices.png').read_bytes())for f in('before','after')},'head_polygons':HEAD[n],'leg_polygons':LEGS[n],'hand_skin_rectangles':HAND_RECTS[n],'local_arm_source':('ultimate_hurt_common_inspection01/after_234_arm_donor_indices.png'if n==234 else None),'arm_polygons':[ARM234,ARM234_RIGHT]if n==234 else[],'common_changed':int((after!=fresh).sum()),'outside_before':[[int(x-160),int(y-160),int(after[y,x])]for y,x in zip(*np.nonzero(outside))],'before_pixels_exact':True,'after_noncommon_nonarm_exact':bool(np.array_equal(after[~(common|arm)],fresh[~(common|arm)])),'wholebody_resized':False,'old_art_copied':0,'before_metrics':metrics(a.rgba(before,16)),'after_metrics':metrics(a.rgba(after))})
 for f,mask in(('before',15),('after',0)):
  for start in(0,4):page(pics[f][start:start+4],a.composite(0,mask)[0],o/f'{f}_comparison_{start//4:02}.png',cols=2,scale=5)
 write(o/'report.json',{'scope':'새 원화 공통부 및234팔 국소 후보.106주먹은새before외곽/투명1칸을포함해공유하며110뒷머리끝1칸도같은새before윤곽에정합한다.범용clip/단색채움없음.','parent_sha256':sha(a.data),'palette_map':lut.tolist(),'rows':rows,'visual_review_pending':True,'arc_written':False,'effects_pending':True});print(json.dumps([{'ref':r['ref'],'outside':r['outside_before']}for r in rows]))
if __name__=='__main__':main()
