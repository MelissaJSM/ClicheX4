"""별개154/183 전신4를 전체 출력캔버스 비율로64고정셀에 등록한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
reg=module('last_quantizer',N/'base_run_repaint/register_page.py');vr=module('last_metrics',N/'ultimate_victory_repaint/register_page.py')
def main():
 meta=json.loads((D/'c_inputs_v1/manifest.json').read_text('utf8'));parent=ROOT/meta['parent_arc'];need(digest(parent)==meta['parent_arc_sha256'],'부모');a=Archive(parent.read_bytes())
 art=D/'c_v1/generated.png';need(digest(art)=='aa7aa49d12931998e969689317333230e75bde9acffb94db6068672a81a7cb12','새원화');im=Image.open(art).convert('RGBA');need(im.size==(1254,1254),'실제전체캔버스')
 out=D/'c_registered_v1';out.mkdir(exist_ok=False);records=[];bodies={}
 x0,y0,x1,y1=meta['world_crop'];need((x1-x0,y1-y0)==tuple(meta['native_cell']),'고정원점창')
 for q in meta['frames']:
  n,form,i,mask=q['ref'],q['form'],q['cell'],q['mask'];start=16 if mask else 0;crop=(i%2*627,i//2*627,(i%2+1)*627,(i//2+1)*627);cell=im.crop(crop);arr=np.array(cell)
  lab,count=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(lab.flat);sizes[0]=0;need(sum(sizes>1000)==1,'단일 큰 몸체');pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[y0+160:y1+160,x0+160:x1+160]=reg.register(cell,(64,64),pal,'area_vote');old=vr.full(a,n,mask);bodies[form,n]=z
  Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');a.rgba(z,start).save(out/f'{form}_{n:03}_rgba.png')
  records.append({'ref':n,'form':form,'source_crop':list(crop),'world_crop':meta['world_crop'],'source_scale_to_native':[64,627],'per_body_auto_fit':False,'translation':[0,0],'old_bbox_world':vr.bbox(old),'new_bbox_world':vr.bbox(z),'old_eye_world':vr.eye(old),'new_eye_world':vr.eye(z),'floor_delta':vr.bbox(z)[3]-vr.bbox(old)[3],'components8':int(label(z>0,np.ones((3,3)))[1]),'native_sha256':sha(z.tobytes()),'source_pixels_alpha_below128':int((arr[:,:,3]<128).sum()),'source_components_ge128':int(count),'old_body_copied':False})
 for n in meta['refs']:
  helper.grid([(f'{form} {n}',[('idle',a.composite(0,mask)[0]),('old',a.composite(n,mask)[0]),('new fixed',a.rgba(bodies[form,n],16 if mask else 0))])for form,mask in(('before',15),('after',0))],out/f'comparison_{n}.png',7)
 write(art.parent/'generation.json',{'tool':'builtin image_gen','source_path':'<LOCAL_PATH>','sha256':digest(art),'requested_size':[1024,1024],'actual_size':list(im.size),'prompt':'../c_inputs_v1/prompt.txt','scope':'서로 다른 미제작154/183 네 전신. 거부된149151153 수정이나 재요청 아님.','native_packed':False,'runtime_verified':False})
 write(out/'registration.json',{'parent_sha256':digest(parent),'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_size':list(im.size),'method':'출력1254전체 2x2의 각627셀을64native로 고정면적투표. world[-32,-28,32,36]. 전신별bbox맞춤/이동/옛몸복사 없음.','frames':records,'native_packed':False,'runtime_verified':False});print(json.dumps([{k:q[k]for k in('ref','form','new_bbox_world','old_eye_world','new_eye_world','floor_delta','components8')}for q in records]))
if __name__=='__main__':main()
