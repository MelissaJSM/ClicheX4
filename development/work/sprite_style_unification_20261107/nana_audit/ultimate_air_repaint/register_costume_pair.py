"""획득 후 새 의상만 분리하는 의미영역 초안. 미술/손목 정합 전 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from inspect_costume_layers import after
Y,X=np.indices((384,384));Y=Y-160;X=X-160
POLYS={
33:[(-5,-9),(2,-9),(7,-8),(8,-6),(10,-3),(10,2),(7,3),(-3,3),(-5,1)],
35:[(-5,-10),(2,-10),(7,-8),(10,-4),(13,-2),(13,1),(9,2),(7,0),(-3,0),(-5,-1)],
37:[(-5,-9),(3,-9),(8,-12),(12,-17),(17,-17),(17,-12),(9,-7),(7,-4),(7,4),(-3,4),(-5,2)],
39:[(-5,-10),(1,-10),(4,-12),(4,-28),(12,-28),(12,-20),(10,-14),(8,-7),(8,1),(6,2),(-3,2),(-5,0)],
41:[(-5,-10),(1,-10),(2,-27),(8,-29),(10,-28),(10,-20),(7,-13),(6,-6),(6,2),(-3,2),(-5,0)],
43:[(-5,-9),(2,-9),(8,-7),(13,-6),(16,-3),(16,0),(13,1),(8,-2),(5,-2),(5,2),(-3,2),(-5,0)],
45:[(-5,-9),(2,-9),(7,-7),(9,-3),(11,-1),(11,3),(7,4),(5,2),(-3,2),(-5,1)],
47:[(-5,-9),(2,-9),(7,-7),(9,-4),(12,-1),(12,2),(9,3),(6,2),(-3,2),(-5,0)],
49:[(-5,-5),(2,-5),(7,-3),(10,0),(13,2),(13,6),(9,7),(6,5),(-3,5),(-5,3)],
51:[(-5,0),(3,0),(7,2),(10,5),(13,7),(13,10),(9,10),(6,9),(-3,9),(-5,7)],
53:[(-5,-8),(2,-8),(6,-5),(8,-2),(11,2),(11,6),(7,6),(5,5),(-4,5),(-5,2)]}
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'costume_pair_probe_v2';out.mkdir(exist_ok=False);rows=[];records=[]
 # Only palette15 differs; source RGB555 is requantized to the fixed post row.
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words]);idx=int(np.argmin(np.sum((pal[:16].astype(float)-pal[31])**2,axis=1)));need(idx!=0,'No opaque mapping')
 for n in range(33,55,2):
  bp=D/'canonical_cases_probe_v1'/f'before_{n:03}.png';b=np.array(Image.open(bp));p=np.array(Image.open(after(n)));maskim=Image.new('1',(384,384));ImageDraw.Draw(maskim).polygon([(x+160,y+160)for x,y in POLYS[n]],fill=1);mask=np.array(maskim).astype(bool);p_original=p.copy();source_map=np.arange(p.size,dtype=np.int32).reshape(p.shape)
  # 39's same authored arm is registered as a rigid local module at the
  # accepted wrist (+2,-1), not a horizontally stretched arm strip.
  if n==39:
   gate=(X>=3)&(X<=14)&(Y>=-30)&(Y<=-9);p[gate]=0;yy,xx=np.nonzero(gate);p[yy-1,xx+2]=p_original[yy,xx];source_map[yy-1,xx+2]=(yy*p.shape[1]+xx)
   mask|=(X>=12)&(X<=15)&(Y>=-27)&(Y<=-19)
  if n in(49,51):
   gate=(X>=6)&(X<=14)&(Y>=(-2 if n==49 else 3))&(Y<=12);p[gate]=0;yy,xx=np.nonzero(gate);p[yy,xx-1]=p_original[yy,xx];source_map[yy,xx-1]=(yy*p.shape[1]+xx)
  target=b.copy();target[b==15]=idx;target[mask]=p[mask]
  # Never replace the newly authored near hand or the exact accepted gun.
  case=np.array(Image.open(D/'canonical_cases_probe_v1'/f'case_{n:03}.png'));protected=(case>0)
  rec=next(v for v in json.loads((D/'canonical_cases_probe_v1/registration.json').read_text('utf8'))['frames']if v['ref']==n);hx,hy,hx1,hy1=rec['new_hand_bbox'];protected|=np.isin(b,(10,11,12))&(X>=hx)&(X<hx1)&(Y>=hy)&(Y<hy1)
  # The farther hand is fixed to the already accepted NEW body, including
  # the dark hand outline. The generated sleeveless wrist meets that hand.
  if n==37:hgate=(X>=12)&(Y>=-17)&(Y<=-11)
  elif n==39:hgate=(X>=3)&(Y<=-27)
  elif n==41:hgate=(X>=1)&(Y<=-27)
  else:
   hands={33:(4,1,9,4),35:(8,0,13,3),43:(9,-5,16,0),45:(7,0,11,4),47:(8,0,12,4),49:(7,3,12,7),51:(8,7,13,11),53:(7,4,11,8)}
   x0,y0,x1,y1=hands.get(n,(0,0,0,0));hgate=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
  handskin=hgate&np.isin(b,(10,11,12));handshape=binary_dilation(handskin,np.ones((3,3)))&hgate&((b==1)|np.isin(b,(10,11,12)));protected|=handshape
  target[protected]=b[protected]
  # A local garment must fit beneath the accepted new jacket envelope.
  # This applies only to this small costume domain; the new head/legs are
  # never intersected with the old game silhouette.
  envelope_clip=(target>0)&(b==0)&mask;clip_values=target[envelope_clip].tolist();target[envelope_clip]=0
  if n==37:target[(X==17)&(Y==-12)]=0 # isolated black quantization speck
  added=(target>0)&(b==0);removed=(b>0)&(target==0)
  Image.fromarray(b).save(out/f'before_{n:03}.png');Image.fromarray(target).save(out/f'after_{n:03}.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/f'costume_mask_{n:03}.png')
  Image.fromarray(protected.astype(np.uint8)*255).save(out/f'protected_hand_gun_{n:03}.png');np.save(out/f'after_source_map_{n:03}.npy',source_map)
  records.append({'ref':n,'before_sha256':digest(bp),'after_source_sha256':digest(after(n)),'costume_polygon':POLYS[n],'palette15_target_index':idx,'changed_pixels':int(np.count_nonzero(target!=b)),'outside_before_alpha':int(added.sum()),'costume_envelope_clip_values':clip_values,'removed_jacket_alpha':int(removed.sum()),'components_8':label(target>0,np.ones((3,3)))[1],'body_source_unmodified_outside_mask_except_palette15':True,'native_packed':False})
  rows.append((f'pair {n}',[('accepted after idle',a.composite(0,0)[0]),('new before',a.rgba(b,16)),('raw new after source',a.rgba(p,0)),('same new body / costume probe',a.rgba(target,0))]))
 for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
 write(out/'registration.json',{'frames':records,'source_only':True,'art_review_pending':True,'native_packed':False,'runtime_verified':False,'warning':'Semantic region draft; raised/free hand seams and alpha subset are not passed.'});print(json.dumps(records))
if __name__=='__main__':main()
