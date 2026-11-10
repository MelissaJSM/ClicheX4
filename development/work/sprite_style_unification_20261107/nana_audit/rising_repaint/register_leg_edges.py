"""새 국소 원화의 그늘 경계 색만 기존 새 전신에 고정 좌표 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,write,need,sha,helper
from register_page import register
from register_rising_page import pupil
Y,X=np.indices((384,384));Y-=160;X-=160
def main():
 art=D/'leg_edges_v1/generated.png';expected='a528b8d27e87941c7306dc003b3541b6ad071d4be04971027da1efd3997654b3';need(digest(art)==expected,'Art hash');im=Image.open(art).convert('RGBA');out=D/'leg_edges_registered_v1';out.mkdir(exist_ok=False)
 src=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';a=Archive(src.read_bytes());need(digest(src)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','Parent');pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);rows=[];records=[]
 for i,(n,page,start)in enumerate([(101,'charge',3),(102,'recovery_ground',6),(231,'recovery_ground',7)]):
  p=D/f'{page}_registered_v1/fourth_{n:03}_indices.png';old=np.array(Image.open(p));box=tuple(round(v)for v in(i%2*im.width/2,i//2*im.height/2,(i%2+1)*im.width/2,(i//2+1)*im.height/2));crop=im.crop(box);idx=register(crop,(96,96),pal,'area_vote');auth=np.zeros((384,384),np.uint8);auth[112:208,112:208]=idx;ox,oy=pupil(old);nx,ny=pupil(auth);dx,dy=ox-nx,oy-ny;need(abs(dx)<=2 and abs(dy)<=2,'Source drift');auth=np.roll(auth,(dy,dx),(0,1))
  region=np.isin(old,(3,4))&binary_dilation(np.isin(old,(10,11,12)),np.ones((3,3)))&(Y>=start)&(Y<=20)&(X<16)
  permitted=region&np.isin(auth,(1,2));new=old.copy();new[permitted]=auth[permitted];changes=[]
  for y,x in np.argwhere(new!=old):
   lx,ly=x-112-dx,y-112-dy;changes.append({'world':[int(x-160),int(y-160)],'before':int(old[y,x]),'after':int(new[y,x]),'source_cell_native':[int(lx),int(ly)],'source_page_box':[box[0]+lx*crop.width/96,box[1]+ly*crop.height/96,box[0]+(lx+1)*crop.width/96,box[1]+(ly+1)*crop.height/96]})
  need(np.array_equal(old>0,new>0),'Alpha');need(np.array_equal(new[~permitted],old[~permitted]),'Other pixels');need(np.array_equal(new[np.isin(old,(10,11,12))],old[np.isin(old,(10,11,12))]),'Skin fill');need(np.array_equal(new[np.isin(old,(5,6))],old[np.isin(old,(5,6))]),'Shoes')
  Image.fromarray(new).save(out/f'fourth_{n:03}_indices.png');Image.fromarray(auth).save(out/f'new_source_{n:03}_indices.png');Image.fromarray(permitted.astype(np.uint8)*255).save(out/f'boundary_mask_{n:03}.png');a.rgba(new,16).save(out/f'fourth_{n:03}_rgba.png')
  rows.append((f'fourth {n}',[('accepted idle',a.composite(0,15)[0]),('previous new body',a.rgba(old,16)),('local authored shadow edge',a.rgba(new,16))]));records.append({'ref':n,'body_source':p.relative_to(ROOT).as_posix(),'body_source_sha256':digest(p),'source_cell':box,'whole_translation':[dx,dy],'changes':changes,'before_sha256':sha(old.tobytes()),'after_sha256':sha(new.tobytes()),'alpha_exact':True,'all_other_pixels_exact':True,'skin_interior_exact':True,'shoes_exact':True})
 helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'source_arc_sha256':digest(src),'source_art_sha256':expected,'source_image_size':list(im.size),'frames':records,'scope':'새 국소 원화의 실제 1/2색인만 기존 새 포스 맨다리의 회색3/4 경계에 등록. 기존 알파/두께/피부 내부/신발/나머지 몸체를 보존한다. 원래 밝았던 그림의 새 미술 보완이며 옛 그림 복원이 아니다.','native_packed':False,'runtime_verified':False,'art_accepted':False})
 inp=D/'leg_edges_inputs_v1';write(art.parent/'generation.json',{'tool':'builtin image_gen edit','source_generated_path':'<LOCAL_PATH>','workspace_path':art.relative_to(ROOT).as_posix(),'workspace_sha256':expected,'image_size':list(im.size),'prompt_path':(inp/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(inp/'prompt.txt'),'input_manifest_sha256':digest(inp/'manifest.json'),'original_file_unmodified':True})
 print(json.dumps({r['ref']:{'changes':len(r['changes']),'translation':r['whole_translation']}for r in records}))
if __name__=='__main__':main()
