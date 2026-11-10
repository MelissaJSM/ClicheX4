"""귀환 새 원화의 전체1536×1024를 고정96×128 두 셀로 등록한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
spec=importlib.util.spec_from_file_location('base_registration',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
spec=importlib.util.spec_from_file_location('victory_register',N/'ultimate_victory_repaint/register_page.py');vreg=importlib.util.module_from_spec(spec);spec.loader.exec_module(vreg)

def main():
 meta=json.loads((D/'body_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['parent_arc'];need(digest(p)==meta['parent_arc_sha256'],'부모해시');a=Archive(p.read_bytes())
 art=D/'body_v1/generated.png';gen=json.loads((art.parent/'generation.json').read_text('utf8'));need(digest(art)==gen['sha256'],'원화 해시');im=Image.open(art).convert('RGBA')
 out=D/'body_registered_v1';out.mkdir(exist_ok=False);records=[];rows=[]
 for q in meta['frames']:
  col,mask,form=q['cell'],q['mask'],q['form'];start=16 if mask else 0
  crop=(round(col*im.width/2),0,round((col+1)*im.width/2),im.height);cell=im.crop(crop);arr=np.array(cell)
  labels,count=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labels.flat);sizes[0]=0;need(sum(sizes>1000)==1,'단일 원화 몸체')
  pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[96:224,112:208]=reg.register(cell,(96,128),pal,'area_vote');old=vreg.full(a,156,mask)
  Image.fromarray(z).save(out/f'{form}_156_indices.png');a.rgba(z,start).save(out/f'{form}_156_rgba.png')
  aa,cc=np.unique(arr[:,:,3],return_counts=True);oldbb,newbb=vreg.bbox(old),vreg.bbox(z)
  records.append({'ref':156,'form':form,'mask':mask,'source_crop':list(crop),'old_bbox_world':oldbb,'new_bbox_world':newbb,'old_eye_world':vreg.eye(old),'new_eye_world':vreg.eye(z),'translation':[0,0],'floor_delta':newbb[3]-oldbb[3],'source_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},'native_components_8':int(label(z>0,np.ones((3,3)))[1]),'native_sha256':sha(z.tobytes()),'old_pixels_copied':0})
  rows.append((f'{form}156',[('idle',a.composite(0,mask)[0]),('previous',a.composite(156,mask)[0]),('new fixed',a.rgba(z,start)),('new207',a.composite(207,mask)[0])]))
 helper.grid(rows,out/'comparison.png',7)
 write(out/'registration.json',{'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_size':list(im.size),'parent_arc_sha256':digest(p),'method':'전체768×1024 셀을96×128로 고정 면적투표. bbox재축척/부분이동/옛머리덮기 없음.','frames':records,'costume_after_accepted':False,'issue':'후폼에 생성된 흰 반바지는 수용 의상과 달라 별도 국소 원화 교정 전 미채택.','native_packed':False,'runtime_verified':False})
 print(json.dumps([{k:q[k]for k in('ref','form','floor_delta','native_components_8','old_bbox_world','new_bbox_world','old_eye_world','new_eye_world')}for q in records]))
if __name__=='__main__':main()
