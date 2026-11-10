"""승리 원화 전체 셀을 고정96격자로 읽어 기존 실제 위치와 비교한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
import importlib.util
spec=importlib.util.spec_from_file_location('native_registration',N/'base_run_repaint/register_page.py');registration=importlib.util.module_from_spec(spec);spec.loader.exec_module(registration)
def bbox(z):
 y,x=np.nonzero(z);return [int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]
def full(a,n,mask):
 z=a.layer(n)[0].copy()
 if mask:
  for pb in(8,5,7,6):v=a.layer(n,pb)[0];z[v>0]=v[v>0]
 return z
def eye(z):
 y,x=np.indices(z.shape); yy,xx=np.nonzero((z%16==14)&(y<160)&(x>140)&(x<175))
 return [int(np.median(xx[yy==yy.min()]))-160,int(yy.min())-160] if len(xx) else None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('group',choices=['a','b']);args=ap.parse_args();g=args.group
 inputs=D/f'{g}_inputs_v1';meta=json.loads((inputs/'manifest.json').read_text('utf8'));src=ROOT/meta['parent_arc'];need(digest(src)==meta['parent_arc_sha256'],'부모해시');a=Archive(src.read_bytes())
 art=D/f'{g}_v1/generated.png';gen=json.loads((art.parent/'generation.json').read_text('utf8'));need(digest(art)==gen['sha256'],'생성물해시');im=Image.open(art).convert('RGBA')
 gen['status']='원화 저장. 고정 셀 등록과 실제 접점·양폼 공통층은 별도 검사.';write(art.parent/'generation.json',gen)
 out=D/f'{g}_registered_v1';out.mkdir(exist_ok=False);records=[];rows=[]
 for q in meta['frames']:
  i,n,mask=q['cell'],q['ref'],q['mask'];form=q['form'];start=16 if mask else 0
  crop=tuple(round(v)for v in(i%2*im.width/2,i//2*im.height/2,(i%2+1)*im.width/2,(i//2+1)*im.height/2));cell=im.crop(crop);arr=np.array(cell)
  labs,k=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;need(sum(sizes>1000)==1,'고정 셀 단일 전신')
  pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  fixed=np.zeros((384,384),np.uint8);fixed[112:208,112:208]=registration.register(cell,(96,96),pal,'area_vote');old=full(a,n,mask)
  Image.fromarray(fixed).save(out/f'{form}_{n:03}_indices.png');a.rgba(fixed,start).save(out/f'{form}_{n:03}_rgba.png')
  red=(arr[:,:,0]>180)&(arr[:,:,1]<60)&(arr[:,:,2]<70);aa,cc=np.unique(arr[:,:,3][red],return_counts=True)
  oldbb,newbb=bbox(old),bbox(fixed);record={'ref':n,'form':form,'mask':mask,'cell':i,'source_crop':list(crop),'old_bbox_world':oldbb,'new_bbox_world':newbb,'old_eye_world':eye(old),'new_eye_world':eye(fixed),'translation':[0,0],'floor_delta':newbb[3]-oldbb[3],'source_red_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},'native_components_8':int(label(fixed>0,np.ones((3,3)))[1]),'native_sha256':sha(fixed.tobytes()),'old_pixels_copied':0}
  records.append(record);rows.append((f'{form} {n}',[('idle',a.composite(0,mask)[0]),('previous',a.composite(n,mask)[0]),('new fixed',a.rgba(fixed,start)),('new138',a.composite(138,mask)[0])]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'registration.json',{'source_art_path':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_size':list(im.size),'parent_arc_sha256':digest(src),'method':'실제 전체627셀→96native 면적투표. 원점 고정/이동0. bbox자동축척·행삭제·옛머리덮기 없음.','frames':records,'native_packed':False,'runtime_verified':False})
 print(json.dumps([{k:q[k]for k in('ref','form','floor_delta','native_components_8','old_bbox_world','new_bbox_world','old_eye_world','new_eye_world')}for q in records]))
if __name__=='__main__':main()
