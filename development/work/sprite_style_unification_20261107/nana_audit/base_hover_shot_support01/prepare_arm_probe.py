"""새 팔을 의미영역만 강체정합하고 수용 정본 권총을 연결한 지원후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
MOVE={(222,'base_legs'):(-1,0),(222,'fourth'):(0,0),(224,'base_legs'):(-1,1),(224,'fourth'):(-1,1),(226,'base_legs'):(1,0),(226,'fourth'):(1,0),(228,'base_legs'):(1,-1),(228,'fourth'):(1,-1)}
def main():
 out=D/'arm_joint_probe_v2';out.mkdir(exist_ok=False);meta=json.loads((D/'registered_sources01/manifest.json').read_text('utf8'));imeta=json.loads((D/'inputs_a01/manifest.json').read_text('utf8'));a=Archive((ROOT/imeta['parent_arc']).read_bytes());frames=[];rows=[]
 for q in meta['frames']:
  n,form,start=q['ref'],q['form'],q['palette_start'];key=f'{form}_{n}';body=np.array(Image.open(ROOT/q['body_source']));donor=np.array(Image.open(D/'registered_sources01'/f'{key}_indices.png'));dx,dy=MOVE[(n,form)];shifted=np.roll(np.roll(donor,dy,axis=0),dx,axis=1)
  # Source shoulder/facial boundary stays on Root body. The rectangle is the
  # local forward sleeve/hand region, including transparency to clear old hand.
  edit=(X>=-35)&(X<=-4)&(Y>=-15)&(Y<=0)
  edit&=~((X>=-11)&(Y<=-9))
  edit|=(X>=-13)&(X<=-5)&(Y>=1)&(Y<=2)
  edit|=(X>=-3)&(X<=0)&(Y>=-6)&(Y<=-3)
  z=body.copy();z[edit]=shifted[edit]
  page='a'if n in (222,224)else'b';gun=np.array(Image.open(D/f'inputs_{page}01'/f'{key}_gun.png'));ox,oy=q['engine_origin'];top=oy-1
  # Replace generated barrel by accepted20 source cells. The generated skin
  # fingers remain in front of the grip; all other body parts stay protected.
  barrel=(X>=ox-2)&(X<=ox+9)&(Y>=top-2)&(Y<=oy+1)&edit;z[barrel]=0
  skin=edit&np.isin(shifted,(10,11,12,13))&(X<=ox+9)&(Y>=oy)&(Y<=oy+5)
  z[gun>0]=gun[gun>0];z[skin]=shifted[skin]
  allowed=edit|barrel|(gun>0);need(np.array_equal(z[~allowed],body[~allowed]),'팔 밖 몸체 변경')
  arms=np.zeros_like(z);arms[allowed]=z[allowed];changed=z!=body;skinhand=skin&(z>0);gunvis=(gun>0)&~skin;contact=int((binary_dilation(skinhand)&gunvis).sum());need(contact>0,f'{form} {n} 손-총 연결')
  for suffix,v in [('indices',z),('arm_indices',arms),('edit_mask',allowed.astype(np.uint8)*255),('skin_mask',skin.astype(np.uint8)*255),('gun_indices',gun),('changed_mask',changed.astype(np.uint8)*255)]:Image.fromarray(v).save(out/f'{key}_{suffix}.png')
  a.rgba(z,start).save(out/f'{key}_rgba.png');rows.append((f'{form} {n}',[('accepted 85',a.composite(85,0 if start==0 else 15)[0]),('root body',a.rgba(body,start)),('fixed donor',a.rgba(donor,start)),('arm-only + canonical candidate',a.rgba(z,start))]));frames.append(dict(q,arm_rigid_translation=[dx,dy],local_indices_sha256=sha(z.tobytes()),arm_indices_sha256=sha(arms.tobytes()),changed_pixels=int(changed.sum()),outside_mask_body_exact=True,canonical20=int((gun>0).sum()),canonical_visible=int(gunvis.sum()),skin_occludes_canonical=int(((gun>0)&skin).sum()),skin_gun_contacts4=contact,components8=int(label(z>0,np.ones((3,3)))[1]),root_source_unchanged=digest(ROOT/q['body_source'])==q['body_source_sha256']))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'manifest.json',{'scope':'222/224/226/228 기본·포스 새 사격팔만 등록한 지원후보; 230 제외. 루트 소유파일 무변경.','frames':frames,'canonical_source_texels':imeta['canonical_source_texels'],'native_packed':False,'runtime_verified':False,'final_art_accepted':False,'remaining':['팔 마스크/정본 접점 실제 열람','루트 최종 공통층/부분조건/패킹']})
 print(json.dumps([{k:q[k]for k in ('ref','form','changed_pixels','skin_gun_contacts4','components8')}for q in frames]))
if __name__=='__main__':main()
