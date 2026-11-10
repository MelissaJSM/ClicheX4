"""새 벽팔의 의미영역을 강체 정합한다. 기존 팔/몸 도트는 이식하지 않는다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def muzzle(v):
 y,x=np.nonzero(v);return int(x.min())-160,float(np.median(y[x==x.min()]))-160
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',choices=['a','b'],required=True);p.add_argument('--form',choices=['before','after'],default='before');p.add_argument('--out');p.add_argument('--registered');v=p.parse_args();page=v.page;form=v.form;offset=16 if form=='before'else 0;refs=(56,58,60)if page=='a'else(62,64,66)
 a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());out=D/(v.out or f'firing_{page}_{form}_joint_probe_v4');need(out.resolve().is_relative_to(D.resolve()),'Output scope');out.mkdir(exist_ok=False);rows=[];recs=[];hands={q['ref']:q['new_hand_bbox']for q in json.loads((D/'canonical_cases_probe_v2/registration.json').read_text('utf8'))['frames']}
 for n in refs:
  bp=D/('canonical_cases_probe_v2'if form=='before'else'costume_pair_probe_v2')/f'{form}_{n-1:03}.png';sp=D/(v.registered or f'firing_{page}_{form}_registered_v1')/f'{form}_{n:03}.png';b=np.array(Image.open(bp));s=np.array(Image.open(sp));bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'));tmx,tmy=muzzle(bar);smx,smy=muzzle(s);dx=tmx-smx;dy=round(tmy-smy);ey,ex=np.nonzero((b==14)&(Y<0));ey=int(np.median(ey))-160;ex=int(np.median(ex))-160
  poly=[(-45,smy-3),(-12,smy-3),(-7,smy),(2,smy-1),(5,smy+2),(5,smy+5),(-5,smy+5),(-45,smy+5)];m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon([(round(x+160),round(y+160))for x,y in poly],fill=1);mask=np.array(m).astype(bool)&(s>0);mask&=~((Y<=ey+4)&(X>=ex-8));mask&=Y<1
  place=np.zeros_like(s);yy,xx=np.nonzero(mask);place[yy+dy,xx+dx]=s[mask];source_map=np.full(s.shape,-1,np.int32);source_map[yy+dy,xx+dx]=yy*384+xx;place[(X>=tmx)&(X<tmx+8)]=0
  case=np.array(Image.open(D/'canonical_cases_probe_v2'/f'case_{n-1:03}.png'));hx,hy,hx1,hy1=hands[n-1];near=np.isin(b,(10,11,12))&(X>=hx)&(X<hx1)&(Y>=hy)&(Y<hy1);gate=(X>=hx-1)&(X<=hx1)&(Y>=hy-1)&(Y<=hy1)&(Y<1);held=(case>0)|(binary_dilation(near,np.ones((3,3)))&gate&np.isin(b,(1,2,3,4,10,11,12,13)))
  t=b.copy();t[held]=0;protect=(((Y<=ey+4)&(X>=ex-8))|(Y>=1))&(b>0);use=(place>0)&~protect;t[use]=place[use];t[protect]=b[protect]
  cleanup=[]
  if form=='before'and page=='a':
   # Trace only the former folded wrist/cuff below the new sleeve. The
   # corresponding same-pose firing source is actually transparent.
   points={56:[(-3,-2),(-3,-1),(-2,-1),(-1,-1),(-3,0),(-2,0)],58:[(-2,-3),(-5,-2),(-4,-2),(-3,-2)],60:[(-1,-3),(-1,-2),(-3,-1)]}[n]
   for x,y in points:
    yy,xx=y+160,x+160;need(not protect[yy,xx] and s[yy-dy,xx-dx]==0,'Folded cuff source alpha');cleanup.append({'world':[x,y],'removed_index':int(t[yy,xx]),'source_world':[x-dx,y-dy],'source_index':0});t[yy,xx]=s[yy-dy,xx-dx]
  if form=='before'and page=='b':
   points={62:[(-2,-3),(-1,-3),(-2,-2),(-1,-2),(-4,-1),(-3,-1),(-2,-1),(-1,-1)],64:[(-2,-1),(-2,0),(-1,0),(0,0),(1,0),(-1,1),(0,1),(1,1)],66:[(0,-2),(-1,-1),(0,-1),(1,-1),(-1,0),(0,0),(1,0)]}[n]
   for x,y in points:
    yy,xx=y+160,x+160;sv=int(s[yy-dy,xx-dx]);need(sv in(0,1,6)and t[yy,xx]in(1,5,6,7,8),'Folded sleeve source semantics');cleanup.append({'world':[x,y],'removed_index':int(t[yy,xx]),'source_world':[x-dx,y-dy],'source_index':sv});t[yy,xx]=sv;protect[yy,xx]=False
  if form=='after'and page=='a':
   # The new sleeveless source has empty space here: only the old folded
   # grip/cuff remnants are removed, never the connected dark sports top.
   points={56:[(-3,-3),(-3,-2),(-2,-2),(-3,-1),(-2,-1)],58:[(-2,-3),(-5,-2),(-4,-2),(-3,-2)],60:[]}[n]
   for x,y in points:
    yy,xx=y+160,x+160;need(not protect[yy,xx]and s[yy-dy,xx-dx]==0,'Sleeveless folded-hand source alpha');cleanup.append({'world':[x,y],'removed_index':int(t[yy,xx]),'source_world':[x-dx,y-dy],'source_index':0});t[yy,xx]=0
  if form=='after'and page=='b':
   points={62:[(-2,-3),(-1,-3),(0,-3),(-2,-2),(-1,-2),(-4,-1),(-3,-1),(-2,-1)],64:[(-2,-1),(-2,0),(1,0),(-1,1),(0,1),(1,1)],66:[(1,-1)]}[n]
   for x,y in points:
    yy,xx=y+160,x+160;sv=int(s[yy-dy,xx-dx]);need(sv in(0,1,2),'Sleeveless source folded hand');cleanup.append({'world':[x,y],'removed_index':int(t[yy,xx]),'source_world':[x-dx,y-dy],'source_index':sv});t[yy,xx]=sv;protect[yy,xx]=False
  window=(X>=tmx)&(X<tmx+8)&(Y>=tmy-3)&(Y<=tmy+5);t[window]=bar[window];need(np.array_equal(t[window],bar[window]),'Original gun');need(np.array_equal(t[protect&~window],b[protect&~window]),'New head/lower body exact');labs,count=label(t>0,np.ones((3,3)));sizes=np.bincount(labs.flat);small=[{'pixels':int(sizes[k]),'xy':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(labs==k))]}for k in range(1,count+1)if sizes[k]<20]
  for name,z in [(form,t),('new_arm',place),('source_arm_mask',mask.astype(np.uint8)*255),('new_hand_removal',held.astype(np.uint8)*255),('protected',protect.astype(np.uint8)*255),('used_arm',use.astype(np.uint8)*255)]:Image.fromarray(z).save(out/f'{name}_{n:03}.png')
  np.save(out/f'arm_source_map_{n:03}.npy',source_map);recs.append({'ref':n,'body_source':str(bp.relative_to(ROOT)),'body_sha256':digest(bp),'arm_source':str(sp.relative_to(ROOT)),'arm_sha256':digest(sp),'arm_polygon':poly,'source_muzzle':[smx,smy],'target_muzzle':[tmx,tmy],'rigid_arm_translation':[dx,dy],'source_arm_texels':int(mask.sum()),'used_arm_texels':int(use.sum()),'new_folded_cuff_alpha_from_firing_source':cleanup,'head_and_non_arm_body_exact':True,'original_muzzle8_exact':True,'components8':int(count),'small_components':small,'index_sha256':sha(t.tobytes()),'old_arm_pixels_used':0})
  rows.append((f'wall firing {n} {form}',[('new body fixed',a.rgba(b,offset)),('whole new arm source',a.rgba(s,offset)),('arm candidate / original gun',a.rgba(t,offset))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'frames':recs,'native_packed':False,'runtime_verified':False,'art_review_pending':True,'horizontal_arm_scale':False});print(json.dumps(recs))
if __name__=='__main__':main()
