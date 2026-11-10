"""지상 발 모듈1px 정합과 순정 초기불꽃/고정 총열 비교. 패킹·게임 쓰기 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,distance_transform_edt
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N.parent/'shibuki_audit')]
from preview_restore import Archive,digest,write,need,sha,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def translate(a,dx,dy,flip=False):
 # Same native texture reflection (-world_x-1) as audit_cyclone_contact.
 b=np.zeros_like(a);yy,xx=np.nonzero(a);wx=xx-160
 if flip:wx=-wx-1
 nx=160+wx+dx;ny=yy+dy;need((nx>=0).all()and(nx<384).all()and(ny>=0).all()and(ny<384).all(),'Canvas');b[ny,nx]=a[yy,xx];return b
def merged(a,n,mask):
 z=a.layer(n)[0].copy()
 if mask:
  for pb in(8,5,7,6):
   v=a.layer(n,pb)[0];z[v>0]=v[v>0]
 return z
def main():
 a=Archive((N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC').read_bytes());out=D/'body_contacts_probe_v1';out.mkdir(exist_ok=False);source=D/'canonical_weapon_probe_v2';meta=json.loads((source/'manifest.json').read_text('utf8'));native=json.loads((D/'native_contacts_v1/manifest.json').read_text('utf8'));records=[];feet=[]
 for n in(100,101,102,103,104,231):
  for form in('base','fourth'):
   p=source/f'{form}_{n:03}_indices.png';old=np.array(Image.open(p));new=old.copy();links=[];start=16 if form=='fourth'else 0;parent=merged(a,n,15 if start else 0)
   if n==231:
    # Both new native soles are one pixel below the original grounded plane.
    # Translate the existing ankle/shoe module; no row interpolation/fill.
    need(np.nonzero(old)[0].max()==np.nonzero(parent)[0].max()+1,'Expected grounded difference')
    module=(Y>=19)&(old>0);new[module]=0
    for y,x in np.argwhere(module):new[y-1,x]=old[y,x];links.append({'world':[int(x-160),int(y-161)],'source_world':[int(x-160),int(y-160)],'index':int(old[y,x])})
    need(np.nonzero(new)[0].max()==np.nonzero(parent)[0].max(),'Ground plane');need(np.array_equal(old[:178],new[:178]),'Upper body');need(label(new>0,np.ones((3,3)))[1]==1,'Foot continuity')
    feet.append((f'{form} grounded231',[('parent',a.composite(n,15 if start else 0)[0]),('new source / +1 sole',a.rgba(old,start)),('authored shoe translated up1',a.rgba(new,start))]))
   Image.fromarray(new).save(out/f'{form}_{n:03}_indices.png');a.rgba(new,start).save(out/f'{form}_{n:03}_rgba.png')
   if n==231:Image.fromarray(new).save(out/f'{form}_232_indices.png')
   records.append({'ref':n,'form':form,'source_path':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'source_native_sha256':sha(old.tobytes()),'target_native_sha256':sha(new.tobytes()),'source_links':links,'grounded_foot_shift':[0,-1]if n==231 else[0,0],'parent_floor':int(np.nonzero(parent)[0].max()-160),'new_floor':int(np.nonzero(new)[0].max()-160),'components_8':int(label(new>0,np.ones((3,3)))[1])})
 helper.grid(feet,out/'grounded_feet.png',7);effect_rows=[];effect_records=[]
 for st,n in((1,104),(0,232)):
  for form,start in(('base',0),('fourth',16)):
   body=np.array(Image.open(out/f'{form}_{n:03}_indices.png'));case=np.array(Image.open(source/f'{form}_{231 if n==232 else n:03}_case.png'));row=[]
   for facing in(0,64):
    q=next(c for c in native['native_initializers']if not c['charged']and c['subtype']==st and c['facing']==facing);fx=np.array(Image.open(D/f'native_contacts_v1/effect_anim{q["animation"]}_{q["initial_ref"]:03}.png'));effect=translate(fx,*q['spawn_world'],q['flip_x']);vis=translate(body,0,0,bool(facing));weapon=translate(case,0,0,bool(facing));im=a.rgba(vis,start);cyan=np.zeros((384,384,4),np.uint8);cyan[effect>0]=[25,205,220,155];overlay=im.copy();overlay.alpha_composite(Image.fromarray(cyan));row.extend([(f'facing{facing} source body',im),(f'facing{facing} native initial occupancy',overlay)])
    dist=distance_transform_edt(effect==0);effect_records.append({'ref':n,'form':form,'facing':facing,'native_initializer':q,'weapon_min_distance_to_initial_effect':float(dist[weapon>0].min()),'weapon_occupancy_overlapping_initial_effect':int(np.count_nonzero((weapon>0)&(effect>0))),'weapon_pixels':int(np.count_nonzero(weapon)),'not_muzzle_or_projectile_origin_assertion':True})
   effect_rows.append((f'{form} {n}',row))
 for i in range(0,len(effect_rows),2):helper.grid(effect_rows[i:i+2],out/f'effect_contact_{i//2+1}.png',7)
 write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'canonical_case_manifest_sha256':digest(source/'manifest.json'),'native_initializer_evidence_sha256':digest(D/'native_contacts_v1/manifest.json'),'frames':records,'effect_spatial_checks':effect_records,'body231_equals232':True,'scope':'지상231/232 발바닥 모듈만 새 원화에서1px 위로 강체 정합. 공중 몸체 바닥을 지상처럼 강제하지 않는다. 순정 초기화 MIPS에서 확인한 효과 첫프레임 점유를 양방향으로 배치한 정적 진단이며 실제 CLUT/시간위상/실기가 아니다.','native_packed':False,'runtime_verified':False,'art_accepted':False});print(json.dumps({'frames':len(records),'spatial_checks':len(effect_records),'floors':[(q['form'],q['new_floor'])for q in records if q['ref']==231]}))
if __name__=='__main__':main()
