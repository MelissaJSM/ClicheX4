"""호버 첫4 원화를 보존하고 고정 전체격자에 등록한다."""
from pathlib import Path
import sys,json,shutil,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
reg=module('hover_quantizer',N/'base_run_repaint/register_page.py');metric=module('hover_metric',N/'ultimate_victory_repaint/register_page.py')
def main():
 src=Path(sys.argv[1]);m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));parent=ROOT/m['parent_arc'];need(digest(parent)==m['parent_arc_sha256'],'부모');a=Archive(parent.read_bytes());out=D/'a_v1';out.mkdir(exist_ok=False);art=out/'generated.png';shutil.copyfile(src,art);need(digest(src)==digest(art),'원본복사');im=Image.open(art).convert('RGBA');need(im.width==im.height and im.width%2==0,'전체2x2');size=im.width//2;dest=D/'first_registered_v1';dest.mkdir(exist_ok=False);pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32);rows=[];proof=[]
 for q in m['frames']:
  n,i=q['ref'],q['cell'];crop=(i%2*size,i//2*size,(i%2+1)*size,(i//2+1)*size);cell=im.crop(crop);arr=np.array(cell);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pal,'area_vote');Image.fromarray(z).save(dest/f'body_{n:03}_indices.png');old=np.array(Image.open(D/f'existing_v1/layer0_{n:03}.png'));leg=np.array(Image.open(D/f'existing_v1/layer5_{n:03}.png'));old[leg>0]=leg[leg>0];red=(arr[:,:,0]>180)&(arr[:,:,1]<60)&(arr[:,:,2]<70);aa,cc=np.unique(arr[:,:,3][red],return_counts=True);proof.append({'ref':n,'crop':crop,'source_native_scale':[96,size],'old_bbox':metric.bbox(old),'new_bbox':metric.bbox(z),'old_eye':metric.eye(old),'new_eye':metric.eye(z),'components8':int(label(z>0,np.ones((3,3)))[1]),'red_fringe_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},'target_sha256':sha(z.tobytes())});rows.append((str(n),[('idle',a.composite(0)[0]),('old hover mask15',a.composite(n,15)[0]),('new fixed source',a.rgba(z))]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],dest/f'comparison_{i//2+1}.png',7)
 write(out/'generation.json',{'source_path':str(src),'workspace_path':art.relative_to(ROOT).as_posix(),'sha256':digest(art),'size':list(im.size),'input_manifest_sha256':digest(D/'a_inputs_v1/manifest.json'),'tool':'builtin_imagegen','native_packed':False,'runtime_verified':False});write(dest/'manifest.json',{'parent_sha256':digest(parent),'source_art_sha256':digest(art),'source_art':art.relative_to(ROOT).as_posix(),'frames':proof,'scope':'전체캔버스 고정격자 후보. 얼굴·권총/손목·추진신발/발목과 부분층은 후속 검토이며 아직 미채택.','runtime_verified':False});print(json.dumps({'sha256':digest(art),'size':list(im.size),'frames':[{k:q[k]for k in('ref','old_bbox','new_bbox','old_eye','new_eye','components8')}for q in proof]}))
if __name__=='__main__':main()
