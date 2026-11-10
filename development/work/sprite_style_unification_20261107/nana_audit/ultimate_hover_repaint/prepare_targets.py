"""새 호버10의 상체/하체 소유를 원래0/5층 경계에 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
PBS=(0,5,6,7,8);KEYS=(221,223,225,227,229);REFS=tuple(range(221,231));CUTS={221:5,223:6,225:5,227:7,229:5}
PARENT=N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';BEFORE='94326933d0dd62ccd7a5904019cae9fd36fc068a6acde8941d6bf8ff363666ca'
def comp(a,l,mask,arm=2):
 im=a.rgba(l[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:im.alpha_composite(a.rgba(l[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 need(digest(PARENT)==BEFORE,'차량 동결 부모');a=Archive(PARENT.read_bytes());out=D/'targets_preview_v3';out.mkdir(exist_ok=False);targets={};frames=[];rows=[];rgba=0
 for key in KEYS:
  cut=CUTS[key];pair=[]
  for n in(key,key+1):
   src=D/(f'canonical_cases_probe_v4/body_{n:03}_indices.png'if n==key else f'muzzle_joint_probe_v1/body_{n:03}_indices.png');z=np.array(Image.open(src));need(label(z>0,np.ones((3,3)))[1]==1,'전체 몸체 연결');need(not np.any(z==15),'다른15색 없음');up=z.copy();up[160+cut:]=0;down=z.copy();down[:160+cut]=0;layers={0:up,5:down,6:np.zeros_like(z),7:np.zeros_like(z),8:np.zeros_like(z)};pair.append(down);targets[str(n)]={str(pb):sha(v.tobytes())for pb,v in layers.items()}
   for pb,v in layers.items():Image.fromarray(v).save(out/f'layer{pb}_{n:03}.png')
   for mask in range(32):
    for arm in(1,2):
     expect=z if mask&1 else up;need(comp(a,layers,mask,arm).tobytes()==a.rgba(expect).tobytes(),'원상체/하체 의미조립');rgba+=1
   frames.append({'ref':n,'source':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'upper_layer':0,'lower_layer':5,'cut_world_y':cut,'empty_layers':[6,7,8],'layer_hashes':targets[str(n)]});rows.append((str(n),[('old actual mask15',a.composite(n,15)[0]),('new actual mask15',comp(a,layers,15)),('new upper0',a.rgba(up)),('new lower5',a.rgba(down,16))]))
  need(np.array_equal(*pair),'사격짝 하체 exact')
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',5)
 ep=N.parent/'zero_audit/nana_ultimate_hover_relations01/conclusions.json';write(out/'manifest.json',{'parent_arc':PARENT.relative_to(ROOT).as_posix(),'parent_arc_sha256':BEFORE,'refs':list(REFS),'new_authored_body_refs':list(KEYS),'new_firing_arms':[n+1 for n in KEYS],'frames':frames,'targets':targets,'direct_rgba_combinations':rgba,'source_relations':{'path':ep.relative_to(ROOT).as_posix(),'sha256':digest(ep)},'policy':'원래 상체layer0/하체layer5 및 빈6/7/8 유지. 실제217..230 mask15 강제 원코드는 변경하지 않는다. mask0 상체만의 기술조합을 완성후폼이라고 부르지 않는다.','native_packed':False,'runtime_verified':False,'art_final':False});print(json.dumps({'layers':50,'rgba':rgba,'sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
