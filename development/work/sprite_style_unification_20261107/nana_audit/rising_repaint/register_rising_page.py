"""라이징 후속페이지의 동일 셀 배율 등록. 새 원화 전체와 접점 차이를 기록한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register
def bounds(z):
 yy,xx=np.nonzero(z);return [int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159]
def pupil(z):
 y,x=np.nonzero((z==14)&(np.indices(z.shape)[0]<160));need(len(x)>0,'Pupil');top=y.min();return int(np.median(x[y==top])),int(top)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--page',required=True);ap.add_argument('--expected',required=True);ap.add_argument('--generated-path',required=True);args=ap.parse_args()
 ip=D/(args.page+'_inputs_v1');art=D/(args.page+'_v1')/'generated.png';out=D/(args.page+'_registered_v1');need(not out.exists(),'Fresh output');meta=json.loads((ip/'manifest.json').read_text('utf8'))
 need(digest(art)==args.expected,'Art');src=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';need(digest(src)==meta['source_arc_sha256'],'Source');a=Archive(src.read_bytes());im=Image.open(art).convert('RGBA');out.mkdir();rows=[];records=[]
 for q in meta['frames']:
  i,n,form=q['cell'],q['ref'],q['form'];mask=15 if form=='fourth' else 0;start=16 if mask else 0
  box=tuple(round(v)for v in(i%2*im.width/2,i//2*im.height/2,(i%2+1)*im.width/2,(i//2+1)*im.height/2));cell=im.crop(box);arr=np.array(cell);labs,_=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;need(sum(sizes>1000)==1,'One figure')
  pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(cell,(96,96),pal,'area_vote');old=a.layer(n)[0].copy()
  if mask:
   for pb in (8,5,7,6):
    layer=a.layer(n,pb)[0];old[layer>0]=layer[layer>0]
  ex,ey=pupil(old);nx,ny=pupil(z);dx,dy=ex-nx,ey-ny;need(abs(dx)<=4 and abs(dy)<=4,'Unexpected source drift');target=np.roll(z,(dy,dx),(0,1));need(not target[:80].any()and not target[-80:].any(),'Wrap')
  Image.fromarray(z).save(out/f'{form}_{n:03}_fixed_indices.png');Image.fromarray(target).save(out/f'{form}_{n:03}_indices.png');a.rgba(target,start).save(out/f'{form}_{n:03}_rgba.png')
  oldbox,newbox=bounds(old),bounds(target);records.append({'form':form,'ref':n,'cell_crop':box,'native_cell':[96,96],'old_eye_world':[ex-160,ey-160],'source_fixed_eye_world':[nx-160,ny-160],'whole_translation':[dx,dy],
   'old_bbox_world':oldbox,'new_bbox_world':newbox,'sole_delta':newbox[3]-oldbox[3],'connected_components_8':int(label(target>0,np.ones((3,3)))[1]),'old_pixels_copied':0,'native_sha256':sha(target.tobytes())})
  rows.append((f'{form} {n}',[('accepted idle',a.composite(0,mask)[0]),('old pose',a.composite(n,mask)[0]),('new fixed cell',a.rgba(z,start)),('eye aligned',a.rgba(target,start))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'registration.json',{'source_arc_sha256':digest(src),'source_art_sha256':digest(art),'source_size':list(im.size),'frames':records,'method':'각 셀 전체를 고정96px로 면적투표 등록한 뒤 눈 위치로 전체 평행이동. 낱부위 확대/축소·옛 몸체/머리/알파 덮기 없음.','native_packed':False,'runtime_verified':False,'candidate_art_accepted':False})
 write(art.parent/'generation.json',{'tool':'builtin image_gen edit','source_generated_path':args.generated_path,'workspace_path':art.relative_to(ROOT).as_posix(),'workspace_sha256':digest(art),'image_size':list(im.size),'prompt_path':(ip/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(ip/'prompt.txt'),'input_manifest_sha256':digest(ip/'manifest.json'),'original_file_unmodified':True})
 print(json.dumps({'page':args.page,'frames':records}))
if __name__=='__main__':main()
