"""Ultimate89/97 네 전신을 고정96셀에 등록하고 원점 차이를 기록한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
reg=module('standing_quantizer',N/'base_run_repaint/register_page.py');vr=module('standing_metrics',N/'ultimate_victory_repaint/register_page.py')
def main():
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['parent_arc'];need(digest(p)==meta['parent_arc_sha256'],'부모');a=Archive(p.read_bytes())
 art=D/'a_v1/generated.png';need(digest(art)=='d4cf2d3b4059ff0189898c9283f71d336ff356c5f7f48d27bd10edfe7e6f6afd','새원화');im=Image.open(art).convert('RGBA');need(im.width==im.height and im.width%2==0,'전체2x2캔버스')
 out=D/'first_registered_v1';out.mkdir(exist_ok=False);records=[];rows=[];size=im.width//2
 for q in meta['frames']:
  n,form,i,mask=q['ref'],q['form'],q['cell'],q['mask'];start=16 if mask else 0;crop=(i%2*size,i//2*size,(i%2+1)*size,(i//2+1)*size);cell=im.crop(crop);arr=np.array(cell)
  lab,count=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(lab.flat);sizes[0]=0;need(sum(sizes>1000)==1,'단일큰몸');pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pal,'area_vote');old=vr.full(a,n,mask)
  Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');a.rgba(z,start).save(out/f'{form}_{n:03}_rgba.png')
  red=(arr[:,:,0]>180)&(arr[:,:,1]<60)&(arr[:,:,2]<70);aa,cc=np.unique(arr[:,:,3][red],return_counts=True)
  records.append({'ref':n,'form':form,'source_crop':list(crop),'source_scale_to_native':[96,size],'world_crop':[-48,-48,48,48],'per_body_auto_fit':False,'translation':[0,0],'old_bbox_world':vr.bbox(old),'new_bbox_world':vr.bbox(z),'old_eye_world':vr.eye(old),'new_eye_world':vr.eye(z),'floor_delta':vr.bbox(z)[3]-vr.bbox(old)[3],'components8':int(label(z>0,np.ones((3,3)))[1]),'native_sha256':sha(z.tobytes()),'source_red_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},'old_body_copied':False})
  rows.append((f'{form} {n}',[('idle',a.composite(0,mask)[0]),('previous',a.composite(n,mask)[0]),('new fixed',a.rgba(z,start)),('accepted85',a.composite(85,mask)[0])]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(art.parent/'generation.json',{'tool':'builtin image_gen','source_path':'<LOCAL_PATH>','sha256':digest(art),'requested_size':[1536,1536],'actual_size':list(im.size),'prompt':'../a_inputs_v1/prompt.txt','scope':'별개 특수89/97의 새 전신4. 사다리 보류/거부 참조와 무관.','native_packed':False,'runtime_verified':False})
 write(out/'registration.json',{'parent_sha256':digest(p),'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_size':list(im.size),'method':'전체 출력2x2 고정셀을96native로 면적투표. 원점/이동0,bbox맞춤/옛몸복사 없음.','frames':records,'native_packed':False,'runtime_verified':False});print(json.dumps([{k:q[k]for k in('ref','form','new_bbox_world','old_eye_world','new_eye_world','floor_delta','components8')}for q in records]))
if __name__=='__main__':main()
