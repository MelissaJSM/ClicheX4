"""새 벽 전신의 손발/머리를 유지하고 새 후폼 의상만 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
POLYS={
55:[(-3,-8),(2,-8),(7,-9),(10,-11),(11,-14),(17,-14),(17,-9),(13,-5),(8,-4),(8,-1),(11,1),(10,3),(-2,3),(-3,0)],
57:[(-3,-9),(2,-9),(7,-10),(12,-12),(16,-15),(21,-15),(21,-10),(16,-7),(10,-5),(7,-4),(7,0),(8,2),(-2,2),(-3,0)],
59:[(-2,-9),(2,-9),(7,-14),(10,-18),(16,-18),(16,-13),(11,-7),(7,-5),(7,-1),(8,2),(-2,3),(-3,0)],
61:[(-3,-9),(2,-9),(7,-12),(10,-15),(12,-16),(17,-16),(17,-12),(12,-7),(8,-5),(8,-1),(10,2),(-2,3),(-3,0)],
63:[(-1,-7),(3,-7),(7,-10),(10,-14),(12,-19),(18,-19),(18,-14),(14,-9),(10,-5),(10,0),(12,3),(1,3),(-1,0)],
65:[(-1,-9),(3,-9),(6,-13),(9,-18),(10,-21),(15,-21),(15,-17),(11,-11),(7,-7),(7,-2),(9,1),(9,3),(0,3),(-1,0)]}
HAND_TOP={55:-11,57:-13,59:-17,61:-14,63:-17,65:-20}
def main():
 a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());out=D/'costume_pair_probe_v2';out.mkdir(exist_ok=False);rows=[];recs=[]
 meta=json.loads((D/'canonical_cases_probe_v2/registration.json').read_text('utf8'))
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words]);mapped=int(np.argmin(np.sum((pal[:16].astype(float)-pal[31])**2,axis=1)));need(mapped==13,'Palette15 meaning')
 for n in range(55,66,2):
  bp=D/'canonical_cases_probe_v2'/f'before_{n:03}.png';ap=D/('after_a_registered_v1'if n<61 else'after_b_registered_v1')/f'after_{n:03}.png';b=np.array(Image.open(bp));p=np.array(Image.open(ap));maskim=Image.new('1',(384,384));ImageDraw.Draw(maskim).polygon([(x+160,y+160)for x,y in POLYS[n]],fill=1);mask=np.array(maskim).astype(bool)
  near=next(r for r in meta['frames']if r['ref']==n);x0,y0,x1,y1=near['new_hand_bbox'];case=np.array(Image.open(D/'canonical_cases_probe_v2'/f'case_{n:03}.png'));nearhand=np.isin(b,(10,11,12))&(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
  hgate=(X>=9)&(Y<=HAND_TOP[n]);handskin=np.isin(b,(10,11,12))&hgate;wallhand=binary_dilation(handskin,np.ones((3,3)))&hgate&np.isin(b,(1,2,3,10,11,12,13));protected=(case>0)|nearhand|wallhand
  # Keep source-authored head strands where both costume variants expose hair.
  samehair=np.isin(p,(5,6,7,8,9))&np.isin(b,(5,6,7,8,9))&(Y<-3)
  # Legs and shoes are common body assets; the local costume must never repaint skin below the hip.
  legskin=np.isin(b,(10,11,12))&(Y>=1)
  protected|=samehair|legskin
  t=b.copy();t[b==15]=mapped;t[mask]=p[mask];t[protected]=b[protected];t[protected&(b==15)]=mapped
  clip=(t>0)&(b==0)&mask;clipvals=t[clip].tolist();t[clip]=0
  local_cleanup=[]
  if n==61:
   # The outer tip of the removed pink-jacket cuff is one old-before
   # outline texel outside the first semantic polygon. The actual new
   # bare-arm art is transparent here, and the texel is now disconnected.
   yy,xx=151,175;labs,_=label(t>0,np.ones((3,3)));need(b[yy,xx]==1 and p[yy,xx]==0 and t[yy,xx]==1 and np.count_nonzero(labs==labs[yy,xx])==1,'Known sleeve edge');t[yy,xx]=p[yy,xx];local_cleanup.append({'world':[15,-9],'before_index':1,'source_after_index':0,'reason':'Removed jacket cuff outer outline; isolated after source sleeve removal'})
  Image.fromarray(t).save(out/f'after_{n:03}.png');Image.fromarray(b).save(out/f'before_{n:03}.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/f'costume_mask_{n:03}.png');Image.fromarray(protected.astype(np.uint8)*255).save(out/f'protected_{n:03}.png')
  need(np.array_equal(t[case>0],b[case>0]),'Pistol exact');need(np.array_equal(t[wallhand],b[wallhand]),'Wall palm exact');need(not np.any((t>0)&(b==0)),'After outside jacket envelope')
  need(label(t>0,np.ones((3,3)))[1]==1,'New body connected')
  recs.append({'ref':n,'before_path':str(bp.relative_to(ROOT)),'before_sha256':digest(bp),'after_art_registered_path':str(ap.relative_to(ROOT)),'after_art_registered_sha256':digest(ap),'polygon':POLYS[n],'palette15_to':mapped,'protected_hand_gun_hair_leg_pixels':int(protected.sum()),'new_after_source_pixels':int((mask&~protected&~clip).sum()),'clipped_values':clipvals,'source_alpha_cleanup':local_cleanup,'changed_pixels':int((t!=b).sum()),'removed_jacket_pixels':int(((b>0)&(t==0)).sum()),'after_components8':label(t>0,np.ones((3,3)))[1],'before_indexed_sha256':sha(b.tobytes()),'after_indexed_sha256':sha(t.tobytes())})
  rows.append((f'wall costume {n}',[('accepted after idle',a.composite(0,0)[0]),('new before body',a.rgba(b,16)),('raw new costume art',a.rgba(p)),('local costume / shared body',a.rgba(t))]))
 for i in range(0,6,3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',6)
 write(out/'registration.json',{'frames':recs,'art_review_pending':True,'native_packed':False,'runtime_verified':False,'source_policy':'새 원화 의상만 사용. 공유 새 머리/손발/권총 보존. 임의 새 색 또는 옛 몸체 사용 없음.'});print(json.dumps(recs))
if __name__=='__main__':main()
