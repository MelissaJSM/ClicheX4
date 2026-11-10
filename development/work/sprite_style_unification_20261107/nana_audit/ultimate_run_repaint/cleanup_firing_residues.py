"""기존 접힌 손/커프의 확인된 좌표만 새 원화 값으로 교체한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def main():
 out=D/'firing_after_cleanup_v1';out.mkdir(exist_ok=False);a=Archive((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes());r=json.loads((D/'firing_regions_v4.json').read_text('utf8'));rows=[];records=[]
 for page in'abcd':
  fld=f'firing_{page}_after_joint_probe_v1'if page=='b'else f'firing_{page}_after_arm_only_v2';ver='v1'if page=='b'else'v2'
  for n in range((ord(page)-97)*8+2,(ord(page)-97)*8+10,2):
   bp=D/f'{fld}/after_{n:03}.png';sp=D/f'firing_{page}_after_registered_{ver}/after_{n:03}.png';b=np.array(Image.open(bp));s=np.array(Image.open(sp));t=b.copy();v=r[str(n)];cells=v.get('source_cells',[])if isinstance(v,dict)else[];changes=[]
   for x,y,_,_ in cells:
    old,new=int(t[y+160,x+160]),int(s[y+160,x+160])
    if old and old!=new:
     # 동일 포즈의 재킷 후보에서 이미 접힌 커프로 분리한 좌표이다.
     need(new in(0,1),'Unexpected donor material at folded cuff');t[y+160,x+160]=new;changes.append([x,y,old,new])
   lab,num=label(t>0,np.ones((3,3)));sizes=np.bincount(lab.ravel());small=[{'size':int(sizes[k]),'coords':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(lab==k))]}for k in range(1,num+1)if sizes[k]<10]
   Image.fromarray(t).save(out/f'after_{n:03}.png');records.append({'ref':n,'base_path':bp.relative_to(ROOT).as_posix(),'base_sha256':digest(bp),'source_path':sp.relative_to(ROOT).as_posix(),'source_sha256':digest(sp),'exact_source_cells':changes,'index_sha256':sha(t.tobytes()),'components':int(num),'small_components':small})
   rows.append((f'run firing {n}',[('before local cleanup',a.rgba(b,0)),('after exact donor cells',a.rgba(t,0))]))
 for i in range(0,16,4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',5)
 write(out/'registration.json',{'scope':'앞서 분리한 동일 포즈의 기존 접힌 커프 좌표에서만 신규 원화의 투명/외곽 값을 가져온다. 임의 bbox 제거/채색 없음.','base_regions_sha256':digest(D/'firing_regions_v4.json'),'frames':records,'runtime_verified':False,'native_packed':False});print(json.dumps([{k:q[k]for k in('ref','exact_source_cells','components','small_components')}for q in records]))
if __name__=='__main__':main()
