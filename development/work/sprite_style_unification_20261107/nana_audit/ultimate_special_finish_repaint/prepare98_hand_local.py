"""새손 국소 원화와 정본20texel을 합치고 새몸체의 나머지를 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper,sha,write
Y,X=np.indices((384,384));Y-=160;X-=160
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'hand98_local_probe_v1';out.mkdir(exist_ok=False);c=a.layer(85)[0];gm=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(c,range(1,10));gun=np.where(gm,c,0);assert np.count_nonzero(gun)==20;case=np.roll(np.roll(gun,-3,1),1,0);box=(X>=-23)&(X<=-12)&(Y>=-7)&(Y<=2);rows=[];proof=[]
 for form,start,mask in(('before',16,15),('after',0,0)):
  z=np.array(Image.open(D/f'contacts_probe_v1/{form}_098_indices.png'));old=z.copy();src=np.array(Image.open(D/f'hand98_registered_v1/{form}_098_indices.png'));z[box]=src[box];skin=box&np.isin(src,(10,11,12,13));visible=(case>0)&~skin;z[visible]=case[visible];assert np.array_equal(z[~(box|(case>0))],old[~(box|(case>0))]);Image.fromarray(z).save(out/f'{form}_098_indices.png');lab,ct=label(z>0,np.ones((3,3)));sizes=np.bincount(lab.flat)[1:];proof.append({'form':form,'edit_world_box':[-23,-7,-11,3],'source_cells':[[int(x-160),int(y-160),int(src[y,x])]for y,x in np.argwhere(box)],'canonical85_translation':[-3,1],'canonical_texels':20,'canonical_visible':int(visible.sum()),'skin_occluded':int(((case>0)&skin).sum()),'contact8':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum()),'components8':int(ct),'component_sizes':sizes.tolist(),'unchanged_outside_hand_and_module':True,'target_sha256':sha(z.tobytes())});rows.append((form,[('old pose',a.composite(98,mask)[0]),('gap diagnostic',a.rgba(old,start)),('new hand source',a.rgba(src,start)),('local only',a.rgba(z,start))]))
 helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'scope':'손국소 후보. 생성 전체몸/얼굴을 복사하지 않고 박스와 정본총만 결합. 양폼공통화/미술최종/패킹은 별도.','frames':proof,'native_packed':False});print(json.dumps([{k:q[k]for k in('form','canonical_visible','contact8','component_sizes')}for q in proof]))
if __name__=='__main__':main()
