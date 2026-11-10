"""분리 부츠 오류가 있는75 원화와 실제 원포즈를 편집 입력으로 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent');im=Image.open(D/'basic_second_v1/generated.png').convert('RGBA');cell=im.crop((im.width//2,0,im.width,im.height//2));ar=np.array(cell);labs,_=label(ar[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=np.isin(labs,np.flatnonzero(sizes>1000));ar[~keep,3]=0;yy,xx=np.nonzero(keep);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];Image.fromarray(ar).crop(box).save(D/'dash75_edit_target.png');a.composite(75)[0].crop((128,144,192,192)).resize((1024,768),Image.Resampling.NEAREST).save(D/'dash75_original_pose.png');write(D/'dash75_edit_inputs.json',{'source_sha256':digest(D/'basic_second_v1/generated.png'),'source_crop':[box[0]+im.width//2,box[1],box[2]+im.width//2,box[3]],'kept_component_sizes':sizes[sizes>1000].tolist(),'note':'대상75의본체와분리부츠를모두보존. 아래셀81의걸친모자211px는입력에포함하지않는다.'})
if __name__=='__main__':main()
