"""Probe common new face, hand and legs for basic/Fourth modular hover art."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));Y,X=np.indices((384,384));Y-=160;X-=160
def comp(a,ls,m,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if m&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
m=read(D/'input_audit.json');parent=ROOT/m['input']['path'];assert sha(parent)==m['input']['sha256'];a=Archive(parent.read_bytes())
out=D/'body_layers_probe01';out.mkdir(exist_ok=False);records=[]
for n,cut in [(221,5),(223,6),(225,5),(227,7),(229,5)]:
 bp=D/f'body_alignment01/base_legs_{n:03}_indices.png';fp=D/f'body_alignment01/fourth_{n:03}_indices.png';b=np.array(Image.open(bp));f=np.array(Image.open(fp));prior=f.copy()
 top={221:-16,223:-15,225:-14,227:-14,229:-15}[n];face=(X>=-8)&(X<=1)&(Y>=top)&(Y<=top+9)
 palm=(X>=-14)&(X<=-5)&(Y>=-5)&(Y<=3)
 hair_tail=(X>=8)&(Y<=10);legs=(Y>=cut)&~hair_tail
 f[face|palm|legs]=b[face|palm|legs]
 full=np.where(f,f,b).astype(np.uint8);own=np.full(b.shape,6,np.uint8)
 own[(Y<=-6)&(X>=-10)]=5;own[(X>=5)&(Y<=10)]=5
 own[(X<=-4)&(Y>=-6)&(Y<=3)]=7
 if n in (221,229):own[(X>=1)&(Y<=-18)]=7
 if n==223:own[(X>=8)&(X<=15)&(Y>=-13)&(Y<=-7)]=7
 own[face]=5;own[palm]=7;own[legs]=8
 base=np.where(legs,0,b).astype(np.uint8)
 diff=((full!=b)|np.array([a.words[i]!=a.words[i+16]for i in range(16)])[full])&(full>0)&~legs
 ls={0:base,8:np.where(legs,b,0).astype(np.uint8),**{pb:np.where(diff&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7)}}
 assert comp(a,ls,8).tobytes()==a.rgba(b).tobytes()
 target=a.rgba(b);target.alpha_composite(a.rgba(full,16));assert comp(a,ls,15,1).tobytes()==target.tobytes()
 for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
 Image.fromarray(own).save(out/f'owner_{n:03}.png')
 stats=[{'mask':mask,'arm':arm,'components8':int(label(np.array(comp(a,ls,mask,arm))[:,:,3]>0,np.ones((3,3)))[1])}for mask in range(16)for arm in(1,2)]
 retained=(f==0)&(b>0);records.append({'ref':n,'source_basic_sha256':sha(bp),'source_fourth_sha256':sha(fp),'shared_face_box':[-8,top,2,top+10],'shared_palm_box':[-14,-5,-4,4],'lower_cut_world_y':cut,'head_tail_excluded_from_leg_mask':True,'base_retained_under_transparent_fourth_pixels':int(retained.sum()),'retained_coords':[[int(x)-160,int(y)-160,int(b[y,x])]for y,x in np.argwhere(retained)],'registered_fourth_changes':int((f!=prior).sum()),'layer_hashes':{str(pb):hashlib.sha256(z.tobytes()).hexdigest()for pb,z in ls.items()},'partial_components':stats})
 helper.grid([(f'hover {n}',[('base idle',a.composite(0)[0]),('new basic plus legs',comp(a,ls,8)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',comp(a,ls,15))])],out/f'comparison_{n}.png',6)
 helper.grid([(f'hover partial {n}',[(str(mask),comp(a,ls,mask))for mask in (8,9,10,12,13,14,15)])],out/f'partial_{n}.png',5)
(out/'manifest.json').write_text(json.dumps({'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':sha(parent),'refs':[221,223,225,227,229],'frames':records,'scope':'원래 호버의 기본 상체0·다리8 구조. 새 몸체에서 얼굴/앞손/하체를 공유하며 full 투명부 기본잔여는 별도기록·검수. 사격팔과패킹 전 진단.','native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps([{'ref':r['ref'],'retained':r['base_retained_under_transparent_fourth_pixels'],'valid_hover_component_counts':sorted({p['components8']for p in r['partial_components']if p['mask']&8})}for r in records]))
