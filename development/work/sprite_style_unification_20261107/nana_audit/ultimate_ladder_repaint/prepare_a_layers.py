"""허용된 첫3 사다리만 실제 팔레트/32마스크의 목표층으로 검토한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
PBS=(0,5,6,7,8);REFS=(143,144,146)

def composite(a,layers,mask,arm):
 im=a.rgba(layers[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:im.alpha_composite(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16))
 return im

def bounds(z):
 y,x=np.nonzero(z)
 return [int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]

def main():
 parent=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC'
 a=Archive(parent.read_bytes());need(digest(parent)=='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29','부모 해시')
 src=D/'a_grip_probe_v1';out=D/'a_layers_probe_v1';out.mkdir(exist_ok=False)
 rows=[];partials=[];records=[]
 for n in REFS:
  b=np.array(Image.open(src/f'before_{n:03}_indices.png'));v=np.array(Image.open(src/f'after_{n:03}_indices.png'))
  need(np.all((v==0)|(b>0)),'후폼 알파가 재킷 밖으로 돌출')
  ls={0:v,5:np.where((b!=v)|(b==15),b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  for pb in (6,7,8):need(not a.layer(n,pb)[0].any(),'기존 비어 있는 아머층 보존')
  targets={}
  for pb,z in ls.items():
   Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png');targets[str(pb)]={'indexed_sha256':sha(z.tobytes()),'opaque_pixels':int((z>0).sum())}
  checks=[]
  for mask in range(32):
   for arm in (1,2):
    im=composite(a,ls,mask,arm);expected=a.rgba(b,16)if mask&1 else a.rgba(v)
    need(im.tobytes()==expected.tobytes(),'32마스크의 정확 전후 합성')
    checks.append({'mask':mask,'arm':arm,'rgba_sha256':sha(im.tobytes())})
  old_full=a.layer(n)[0].copy()
  for pb in (8,5,7,6):z=a.layer(n,pb)[0];old_full[z>0]=z[z>0]
  old_bbox=bounds(old_full);new_bbox=bounds(b)
  need(old_bbox[3]==new_bbox[3],'첫3 원 발바닥 높이')
  rows.append((str(n),[('idle before',a.composite(0,15)[0]),('new before',composite(a,ls,15,2)),('idle after',a.composite(0)[0]),('new after',composite(a,ls,0,2))]))
  partials.append((str(n),[('mask0 / bare',composite(a,ls,0,2)),('mask1 / jacket',composite(a,ls,1,2)),('mask14 / no jacket',composite(a,ls,14,2)),('mask15 / jacket',composite(a,ls,15,2))]))
  records.append({'ref':n,'source_before_sha256':digest(src/f'before_{n:03}_indices.png'),'source_after_sha256':digest(src/f'after_{n:03}_indices.png'),'targets':targets,'old_before_bbox':old_bbox,'new_before_bbox':new_bbox,'floor_y_exact':True,'components8':{k:int(label(z>0,np.ones((3,3)))[1])for k,z in(('before',b),('after',v))},'rgba_checks':checks})
 helper.grid(rows,out/'comparison.png',6);helper.grid(partials,out/'partial.png',6)
 write(out/'manifest.json',{'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':digest(parent),'source_manifest':(src/'manifest.json').relative_to(ROOT).as_posix(),'source_manifest_sha256':digest(src/'manifest.json'),'refs':list(REFS),'frames':records,'target_layers':15,'direct_rgba_combinations':192,'scope':'허용된 첫3 원화와 손 공유의 목표층 진단. 몸/다리/팔 크기 변경 없음. 149/151/153 의상 교정거부와 별개이며 그 후보에는 쓰지 않는다. 최종 ARC에 쓰거나 동결하지 않았고 원사다리 손접점/반전 관계는 별도 읽기 확인 중.','native_packed':False,'runtime_verified':False})
 print(json.dumps({'layers':15,'rgba_combinations':192,'floor_exact':3,'manifest_sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
