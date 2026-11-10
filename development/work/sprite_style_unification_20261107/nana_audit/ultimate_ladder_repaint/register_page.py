"""Ultimate 사다리6표시를64고정셀로 읽어 손발·머리 크기 비교한다."""
from pathlib import Path
import sys,json,importlib.util,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
reg=module('fixed_quantizer',N/'base_run_repaint/register_page.py');vr=module('body_metrics',N/'ultimate_victory_repaint/register_page.py')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--page',choices=('a','b'),default='a');args=ap.parse_args();page=args.page
 source_hash={'a':'4052c6ab0ca0555234ee44f2258f92c7c29d05f69734b54ddc1dbe26fa1888ce','b':'3cff8603b891726357d167e1a7f1918991d9128b7bbe6c8a7c409c6cff1d81da'};source_file={'a':'exec-cc89f266-e607-45b8-b2e5-b54f990beaeb.png','b':'exec-411c2670-23c7-4018-8c8f-c5f9eb463329.png'}
 issue='후폼 높은팔의 분홍소매 미수용.'if page=='a'else'후폼 하의의 흰 반바지 표현 미수용. 대기 검정/분홍 의상으로 국소 교정 필요.'
 meta=json.loads((D/f'{page}_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['parent_arc'];need(digest(p)==meta['parent_arc_sha256'],'부모');a=Archive(p.read_bytes());art=D/f'{page}_v1/generated.png';need(digest(art)==source_hash[page],'원화');im=Image.open(art).convert('RGBA')
 write(art.parent/'generation.json',{'tool':'builtin image_gen','source_path':'<LOCAL_PATH>'+source_file[page],'sha256':digest(art),'size':list(im.size),'prompt':f'../{page}_inputs_v1/prompt.txt','issue':issue,'native_packed':False,'runtime_verified':False})
 out=D/f'{page}_registered_v1';out.mkdir(exist_ok=False);records=[];bodies={}
 for q in meta['frames']:
  n,form,mask,i=q['ref'],q['form'],q['mask'],q['cell'];start=16 if mask else 0;crop=tuple(round(v)for v in(i%3*im.width/3,i//3*im.height/2,(i%3+1)*im.width/3,(i//3+1)*im.height/2));cell=im.crop(crop);arr=np.array(cell)
  labs,k=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;need(sum(sizes>1000)==1,'단일전신');pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[124:188,128:192]=reg.register(cell,(64,64),pal,'area_vote');old=vr.full(a,n,mask);Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');a.rgba(z,start).save(out/f'{form}_{n:03}_rgba.png');bodies[form,n]=z
  aa,cc=np.unique(arr[:,:,3],return_counts=True);records.append({'ref':n,'form':form,'mask':mask,'source_crop':list(crop),'old_bbox_world':vr.bbox(old),'new_bbox_world':vr.bbox(z),'old_eye_world':vr.eye(old),'new_eye_world':vr.eye(z),'translation':[0,0],'floor_delta':vr.bbox(z)[3]-vr.bbox(old)[3],'native_components8':int(label(z>0,np.ones((3,3)))[1]),'source_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},'native_sha256':sha(z.tobytes()),'old_bitmap_copied':False})
 for n in meta['refs']:
  helper.grid([(f'{form} {n}',[('idle',a.composite(0,mask)[0]),('old',a.composite(n,mask)[0]),('new fixed',a.rgba(bodies[form,n],16 if mask else 0))])for form,mask in(('before',15),('after',0))],out/f'comparison_{n}.png',7)
 write(out/'registration.json',{'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_size':list(im.size),'parent_sha256':digest(p),'method':'전체512셀→64native고정 면적투표,원점/축척/전신이동0.','unaccepted_issue':issue,'frames':records,'native_packed':False,'runtime_verified':False});print(json.dumps([{k:q[k]for k in('ref','form','floor_delta','old_eye_world','new_eye_world','new_bbox_world','native_components8')}for q in records]))
if __name__=='__main__':main()
