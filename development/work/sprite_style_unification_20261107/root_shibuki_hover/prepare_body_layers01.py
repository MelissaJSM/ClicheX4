"""단일 새 하체와 공통 얼굴/손을 배정하는 진단. 게임 자원 미수정."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from scripts.export_x_consistency import Archive
from preview_restore import helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
Y,X=np.indices((384,384));Y-=160;X-=160
def box(v):
 x0,y0,x1,y1=v;return(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def comp(a,ls,m,arm=1):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if m&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';assert sha(p)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(p.read_bytes());out=D/'body_layers_probe01';out.mkdir(exist_ok=False);records=[]
 faces={221:[-10,-17,1,-6],223:[-10,-15,2,-3],225:[-9,-15,1,-5],227:[-9,-16,1,-5],229:[-10,-17,1,-6]}
 palms={221:[[-14,-25,-8,-18],[-1,-27,5,-20]],223:[[-17,-16,-10,-10],[-7,-6,-2,0]],225:[[-16,-10,-10,-4],[2,-9,9,-3]],227:[[-13,-6,-7,0],[-2,-5,5,1]],229:[[-18,-28,-8,-21],[1,-28,10,-21]]}
 cuts={221:4,223:7,225:6,227:6,229:5}
 for n in(221,223,225,227,229):
  page=1 if n<225 else 2
  bp=D/(f'registered_neutral{page:02}/base_legs_{n:03}_nearest_indices.png'if n!=229 else'reach229_registered01/base_legs_local_indices.png')
  fp=D/(f'registered_neutral{page:02}/fourth_{n:03}_nearest_indices.png'if n!=229 else'reach229_registered01/fourth_local_indices.png')
  b=np.array(Image.open(bp));f=np.array(Image.open(fp));lower_source=f.copy();foot_shift=None
  if n==223:
   # 발목 아래 오른신발의 등록만 한 행 올린다. 전신/효과는 이동하지 않는다.
   foot=(X>=7)&(Y>=18);v=np.where(foot,f,0).astype(np.uint8);lower_source[foot]=0;shift=np.zeros_like(v);shift[:-1]=v[1:];lower_source[shift>0]=shift[shift>0];foot_shift={'world_box':[7,18,224,224],'translation':[0,-1],'source_opaque_pixels':int((v>0).sum())}
  legs=(Y>=cuts[n])&~((X>=10)&(Y<8));common=box(faces[n]);hand=np.zeros_like(common)
  for r in palms[n]:hand|=box(r)
  # 손 주변 의미창은 초안이며 최종 수용 전 각 손목/커프 판을 별도 검토한다.
  common|=hand
  oldhead=a.layer(n,5)[0]>0;oldtorso=a.layer(n,6)[0]>0;oldarm=a.layer(n,7)[0]>0
  head=binary_dilation(oldhead,iterations=1)&~common&~legs
  arm=binary_dilation(oldarm,iterations=2)&~common&~legs&~head
  torso=binary_dilation(oldtorso,iterations=2)&~common&~legs&~head&~arm
  base=np.where(legs,0,b).astype(np.uint8)
  ls={0:base,8:np.where(legs,lower_source,0).astype(np.uint8),5:np.where(head,f,0).astype(np.uint8),6:np.where(torso,f,0).astype(np.uint8),7:np.where(arm,f,0).astype(np.uint8)}
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  owner=np.zeros_like(b);owner[legs]=8;owner[head]=5;owner[torso]=6;owner[arm]=7;Image.fromarray(owner).save(out/f'owner_{n:03}.png')
  helper.grid([(f'hover {n}',[('idle base',a.composite(0,8)[0]),('new basic common legs',comp(a,ls,8)),('idle Fourth',a.composite(0,15)[0]),('new Fourth',comp(a,ls,15))])],out/f'comparison_{n}.png',6)
  helper.grid([(f'hover {n}',[(f'mask{m}',comp(a,ls,m))for m in(8,9,10,12,13,14,15)])],out/f'partial_{n}.png',5)
  stats=[{'mask':m,'components8':int(label(np.array(comp(a,ls,m))[:,:,3]>0,np.ones((3,3)))[1])}for m in range(8,16)]
  records.append({'ref':n,'base_source_sha256':sha(bp),'fourth_source_sha256':sha(fp),'shared_face':faces[n],'shared_hand_windows':palms[n],'leg_cut_y':cuts[n],'leg_source':'fourth CLUT16','right_shoe_registration':foot_shift,'layer_hashes':{str(pb):hashlib.sha256(z.tobytes()).hexdigest()for pb,z in ls.items()},'partial_components':stats})
 (out/'manifest.json').write_text(json.dumps({'parent_sha256':sha(p),'frames':records,'scope':'새 하체를CLUT16 공통8로,새 얼굴/손을공통0로 배정한 진단. 기본/포스의 기존 아머 의미영역에서만 새의상층을 선택한다. 최종아트 수용/게임패킹 전이다.','native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps([{'ref':r['ref'],'components':[x['components8']for x in r['partial_components']]}for r in records]))
if __name__=='__main__':main()
