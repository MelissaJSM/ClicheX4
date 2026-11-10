"""215 새 맨팔의 손목을 의상 전후 공통 접점에 강체 등록한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,helper
s=importlib.util.spec_from_file_location('nova_common_util',N/'ultimate_standing_repaint/prepare_common.py');u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
ARM=[(6,-8),(10,-8),(13,-6),(16,-4),(18,-1),(18,2),(13,2),(11,-1),(9,-3),(7,-4),(6,-5)]
def main():
 out=D/'contacts_probe_v1';out.mkdir(exist_ok=False);meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());b=np.array(Image.open(D/'semantic_samples_v1/before_215_indices.png'));src=np.array(Image.open(D/'semantic_samples_v1/after_215_indices.png'));m=u.poly(ARM);rows=[];proof=[]
 for dy in(1,2):
  z=src.copy();part=np.where(m,src,0);z[m]=0;dest=np.roll(np.roll(part,dy,0),-1,1);overlap=int(((dest>0)&(z>0)).sum());z[dest>0]=dest[dest>0]
  Image.fromarray(z).save(out/f'after_215_shift_m1_p{dy}_indices.png');rows.append((f'arm -1,+{dy}',[('old pose',a.composite(215)[0]),('new jacket',a.rgba(b,16)),('new bare source',a.rgba(src)),('rigid arm candidate',a.rgba(z))]));proof.append({'translation':[-1,dy],'polygon':ARM,'source_cells':[[int(x-160),int(y-160),int(src[y,x])]for y,x in np.argwhere(m&(src>0))],'overlap':overlap,'component_count':int(label(z>0,np.ones((3,3)))[1]),'target_sha256':sha(z.tobytes())})
 helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'source_sha256':sha(src.tobytes()),'candidates':proof,'scope':'이동 전후 새 맨팔 표본의 단일 강체 등록 진단. 색을 그리거나 팔 길이를 늘리지 않았다. 새 손/어깨 접점과 의상 공통 실루엣은 시각 검토 전이며 최종 채택 아님.','native_packed':False});print(json.dumps([{k:q[k]for k in('translation','overlap','component_count')}for q in proof]))
if __name__=='__main__':main()
