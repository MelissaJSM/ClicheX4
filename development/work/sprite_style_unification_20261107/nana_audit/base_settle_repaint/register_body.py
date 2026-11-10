"""기본/포스138 새 원화를 고정96×128으로 등록하고 원점과 비교한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
reg=module('base_registration',N/'base_run_repaint/register_page.py')
vreg=module('victory_register',N/'ultimate_victory_repaint/register_page.py')

def main():
 meta=json.loads((D/'body_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['art_parent_arc'];need(digest(p)==meta['art_parent_arc_sha256'],'부모 해시');a=Archive(p.read_bytes())
 art=D/'body_v1/generated.png';need(digest(art)=='56ebfae01777cf9588174e9724cefaf13455cc1b752c1deb7d626f96eaa248fc','원화 해시');im=Image.open(art).convert('RGBA')
 write(art.parent/'generation.json',{'tool':'builtin image_gen','sha256':digest(art),'source_path':'<LOCAL_PATH>','prompt':'../body_inputs_v1/prompt.txt','size':list(im.size),'scope':'기본/포스138 한 자세 두 의상.139 파생은 등록 후 별도.','native_packed':False})
 out=D/'body_registered_v1';out.mkdir(exist_ok=False);records=[];rows=[]
 for q in meta['frames']:
  col,mask,form=q['cell'],q['mask'],q['form'];start=16 if mask else 0
  crop=(round(col*im.width/2),0,round((col+1)*im.width/2),im.height);cell=im.crop(crop);arr=np.array(cell)
  labels,count=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labels.flat);sizes[0]=0;need(sum(sizes>1000)==1,'단일 원화 몸체')
  pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[96:224,112:208]=reg.register(cell,(96,128),pal,'area_vote');old=vreg.full(a,138,mask)
  Image.fromarray(z).save(out/f'{form}_138_indices.png');a.rgba(z,start).save(out/f'{form}_138_rgba.png')
  aa,cc=np.unique(arr[:,:,3],return_counts=True);oldbb,newbb=vreg.bbox(old),vreg.bbox(z)
  records.append({'ref':138,'form':form,'mask':mask,'source_crop':list(crop),'old_bbox_world':oldbb,'new_bbox_world':newbb,'old_eye_world':vreg.eye(old),'new_eye_world':vreg.eye(z),'translation':[0,0],'floor_delta':newbb[3]-oldbb[3],'source_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},'native_components_8':int(label(z>0,np.ones((3,3)))[1]),'native_sha256':sha(z.tobytes()),'old_pixels_copied':0})
  rows.append((f'{form}138',[('idle',a.composite(0,mask)[0]),('previous',a.composite(138,mask)[0]),('new fixed',a.rgba(z,start)),('new100',a.composite(100,mask)[0])]))
 helper.grid(rows,out/'comparison.png',7)
 write(out/'registration.json',{'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_size':list(im.size),'parent_arc_sha256':digest(p),'method':'전체768×1024 셀을96×128로 고정 면적투표. bbox재축척/부분이동/옛머리덮기 없음.','frames':records,'native_packed':False,'runtime_verified':False})
 print(json.dumps([{k:q[k]for k in('ref','form','floor_delta','native_components_8','old_bbox_world','new_bbox_world','old_eye_world','new_eye_world')}for q in records]))
if __name__=='__main__':main()
