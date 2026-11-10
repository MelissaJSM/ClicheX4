"""새 팔 편집의 작은 접점 잔차를 강체 이동으로 비교. 아직 패킹하지 않는다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash
from prepare_wall_contact_edit import hand

def move(a,dx,dy):
 out=np.zeros_like(a);y,x=np.nonzero(a);out[y+dy,x+dx]=a[y,x];return out

def arm_mask(n):
 yy,xx=np.indices((384,384));x=xx-160;y=yy-160
 if n==61:cut=np.where(y<=-13,10,np.where(y<=-10,8,9));return(y>=-25)&(y<=-8)&(x>=cut)&(x<=18)
 if n==63:cut=np.where(y<=-19,12,np.where(y<=-14,12,np.where(y<=-10,12,13)));return(y>=-25)&(y<=-7)&(x>=cut)&(x<=21)
 if n==65:cut=np.where(y<=-19,11,np.where(y<=-13,10,np.where(y<=-10,9,10)));return(y>=-25)&(y<=-7)&(x>=cut)&(x<=22)
 raise ValueError(n)

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);oldart=H/'wall_detail_native01';edit=H/'wall_contact_edit01/native01';out=H/'wall_contact_native03';need(not out.exists(),'Output exists');out.mkdir()
 dxs={55:-1,57:0,59:0,61:2,63:5,65:2};deltas={61:(2,-3),63:(1,-1),65:(0,-1)};report=[]
 for mask,label,start in((0,'base',0),(15,'fourth',16)):
  items=[]
  for n in range(55,67,2):
   before=np.array(Image.open(oldart/f'{label}_{n:03}_indices.png'));v=move(before,dxs[n],0)
   if n>=61:
    changed=np.array(Image.open(edit/f'{label}_{n:03}_indices.png'));region=arm_mask(n)
    # Both are NEW same-pose artwork. No current/legacy head or torso is pasted.
    arm=np.where(region,changed,0).astype(np.uint8);delta=deltas[n];shifted=move(arm,*delta)
    v[region]=0
    # Keep the same newly drawn lower elbow/shoulder arc at its original joint.
    # The upper arm is rigidly registered; no sleeve raster is stretched.
    yy,_=np.indices(v.shape);joint=region&(yy>=160+(-12 if n==61 else -10))
    v[joint]=changed[joint];v[shifted>0]=shifted[shifted>0]
    Image.fromarray(region.astype(np.uint8)*255).save(out/f'{label}_{n:03}_source_arm_mask.png')
   Image.fromarray(v).save(out/f'{label}_{n:03}_indices.png');pic=a.rgba(v,start);pic.save(out/f'{label}_{n:03}.png');items.extend([(f'{label} current {n}',a.composite(n,mask)[0]),(f'{label} new candidate {n}',pic)])
   if n>=61 and mask==0:report.append({'ref':n,'target_skin_palm':hand(a.layer(n)[0]),'candidate_skin_palm':hand(v),'whole_new_body_translation':[dxs[n],0],'new_arm_rigid_translation':list(deltas[n]),'arm_resized':False,'original_new_elbow_arc_preserved_below_world_y':-12 if n==61 else -10})
  page(items,a.composite(0,mask)[0],out/f'{label}_comparison.png',cols=2,scale=4)
 write(out/'registration.json',{'source_bin_sha256':SOURCE_SHA,'arm_source_sha256':sha((H/'wall_contact_edit01/generated.png').read_bytes()),'body_source':'wall_detail_native01 new generated poses','records':report,'only_native_registration_candidate':True,'art_or_joint_validation_pending':True,'not_packed':True})
 print(json.dumps(report))

if __name__=='__main__':main()
