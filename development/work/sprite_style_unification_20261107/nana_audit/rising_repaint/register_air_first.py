"""공중103/104 새 전신을 전체 셀 고정배율로 등록한다. 옛 몸체 덮기 없음."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,helper
from register_page import register
sha=lambda b:hashlib.sha256(b).hexdigest()
def bbox(z):
 yy,xx=np.nonzero(z);return [int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159] if len(xx) else None
def pupil(z):
 y,x=np.nonzero((z==14)&(np.indices(z.shape)[0]<160));assert len(x)
 top=y.min();return int(np.median(x[y==top])),int(top)
def main():
 src=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';arc=src.read_bytes();assert sha(arc)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa';a=Archive(arc)
 art=D/'air_v1/generated.png';data=art.read_bytes();assert sha(data)=='f14e0f396d56c89e5fa5c85df7ccaa0eb092dada6e2a3495ef8fdf86fbf87601';im=Image.open(art).convert('RGBA')
 out=D/'air_registered_v1';assert not out.exists();out.mkdir();meta=json.loads((D/'air_inputs_v1/manifest.json').read_text('utf8'));rows=[];contacts=[];records=[]
 for q in meta['frames']:
  i,n,form=q['cell'],q['ref'],q['form'];mask=15 if form=='fourth' else 0;start=16 if mask else 0
  box=tuple(round(v) for v in(i%2*im.width/2,i//2*im.height/2,(i%2+1)*im.width/2,(i//2+1)*im.height/2));cell=im.crop(box);arr=np.array(cell)
  labs,_=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;assert sum(sizes>1000)==1
  pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(cell,(96,96),pal,'area_vote')
  old=a.layer(n)[0].copy()
  if mask:
   for pb in (8,5,7,6):
    layer=a.layer(n,pb)[0];old[layer>0]=layer[layer>0]
  ex,ey=pupil(old);nx,ny=pupil(z);dx,dy=ex-nx,ey-ny;assert abs(dx)<=4 and abs(dy)<=4
  target=np.roll(z,(dy,dx),(0,1));assert not target[:80].any() and not target[-80:].any()
  Image.fromarray(z).save(out/f'{form}_{n:03}_fixed_indices.png');Image.fromarray(target).save(out/f'{form}_{n:03}_indices.png');a.rgba(target,start).save(out/f'{form}_{n:03}_rgba.png')
  rb=bbox(target>0);ob=bbox(old>0);Y,X=np.indices(target.shape);topmask=(target>0)&(Y<ey-5)&(X>ex+5);gunbbox=bbox(topmask)
  records.append({'form':form,'ref':n,'cell_crop':box,'native_size':[96,96],'old_eye_world':[ex-160,ey-160],'source_fixed_eye_world':[nx-160,ny-160],
   'whole_translation':[dx,dy],'original_bbox_world':ob,'new_bbox_world':rb,'sole_delta':rb[3]-ob[3],
   'upper_right_occupancy_bbox_world':gunbbox,'upper_right_is_not_semantic_gun_mask':True,'connected_components_8':int(label(target>0,np.ones((3,3)))[1]),
   'source_fixed_index_sha256':sha(z.tobytes()),'target_index_sha256':sha(target.tobytes()),'old_pixels_copied':0,'per_body_part_scale_changes':False})
  rows.append((f'{form} {n}',[('accepted idle',a.composite(0,mask)[0]),('old',a.composite(n,mask)[0]),('new fixed cell',a.rgba(z,start)),('eye aligned',a.rgba(target,start))]))
  if n==104:
   fx=np.array(Image.open(D/'native_contacts_v1/effect_anim1_005.png'));eff=np.zeros_like(fx);yy,xx=np.nonzero(fx);eff[yy-12,xx+6]=fx[yy,xx]
   vis=a.rgba(target,start);colors=np.zeros((384,384,4),np.uint8);colors[eff>0]=[25,205,220,155];vis.alpha_composite(Image.fromarray(colors))
   contacts.append((f'{form}104 / static native spawn',[('new',a.rgba(target,start)),('actual effect occupancy only',vis)]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 helper.grid(contacts,out/'effect_contact.png',6)
 j={'source_art_sha256':sha(data),'source_arc_sha256':sha(arc),'source_size':list(im.size),'frames':records,
  'method':'전체1254캔버스의 각627셀→96 고정면적투표. 기존 눈에 맞춘 전체 평행이동만; 옛 머리/몸/알파 덮기 없음.',
  'pending':['사랑이 총열/그립 의미분리와 원불꽃 접점','팔/총구 가림·발 크기와 두의상공통부품','네이티브 패킹·부분아머 회귀'],
  'native_packed':False,'runtime_verified':False,'candidate_art_accepted':False}
 (out/'registration.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
 generation={'tool':'builtin image_gen edit','source_generated_path':'<LOCAL_PATH>',
  'workspace_path':art.relative_to(ROOT).as_posix(),'workspace_sha256':sha(data),'original_file_unmodified':True,'image_size':list(im.size),
  'prompt_path':(D/'air_inputs_v1/prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':sha((D/'air_inputs_v1/prompt.txt').read_bytes()),'input_manifest':(D/'air_inputs_v1/manifest.json').relative_to(ROOT).as_posix()}
 (art.parent/'generation.json').write_text(json.dumps(generation,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'registered':len(records),'frames':records}))
if __name__=='__main__':main()
