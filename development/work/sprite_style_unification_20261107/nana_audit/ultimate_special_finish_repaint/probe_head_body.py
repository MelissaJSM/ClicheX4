"""95의 첫 새 머리와 두 번째 새 몸체를 국소 강체등록해 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,helper,sha
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'head_body95_probe_v1';out.mkdir(exist_ok=False);rows=[];proof=[];Y,X=np.indices((384,384));Y-=160;X-=160
 for form,start,mask in(('before',16,15),('after',0,0)):
  h=np.array(Image.open(D/f'first_registered_v1/{form}_095_indices.png'));z=np.array(Image.open(D/f'geometry_registered_v1/{form}_095_indices.png'));head_dy=-1 if form=='before'else 0;h=np.roll(h,head_dy,0);v=np.roll(z,-4,0);head=(Y<=-15);v[head]=h[head]
  Image.fromarray(v).save(out/f'{form}_095_indices.png');proof.append({'form':form,'body_source':'geometry_registered_v1','body_translation':[0,-4],'head_source':'first_registered_v1','head_translation':[0,head_dy],'head_selection':'world y<=-15','body_scale':1,'components8':int(label(v>0,np.ones((3,3)))[1]),'target_sha256':sha(v.tobytes()),'candidate_only':True})
  rows.append((f'{form}95',[('idle',a.composite(0,mask)[0]),('original',a.composite(95,mask)[0]),('first long source',a.rgba(np.array(Image.open(D/f'first_registered_v1/{form}_095_indices.png')),start)),('head plus new body',a.rgba(v,start))]))
 helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'scope':'95 첫원화 머리와 새국소 몸체의 원점정합 진단. 새원화끼리만 선택하며 옛그림 덮기 없음. 총/손 최종 정합은 별도.','records':proof,'native_packed':False});print(json.dumps(proof))
if __name__=='__main__':main()
