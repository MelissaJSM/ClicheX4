"""Integer translation only; match foot height without warping drawn body parts."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
m=read(D/'input_audit.json');src=ROOT/m['input']['path'];assert sha(src)==m['input']['sha256'];a=Archive(src.read_bytes())
translations={221:((1,-2),(2,-2)),223:((1,-1),(2,-1)),225:((2,3),(2,3)),227:((3,3),(3,3)),229:((1,0),(1,0))}
out=D/'body_alignment01';out.mkdir(exist_ok=False);records=[]
for n in translations:
 rows=[]
 folder='registered01' if n<225 else 'registered02' if n<229 else 'registered03_fit01'
 for fi,(form,mask,start)in enumerate([('base_legs',8,0),('fourth',15,16)]):
  p=D/f'{folder}/{form}_{n:03}_indices.png';before=np.array(Image.open(p));dx,dy=translations[n][fi];after=np.zeros_like(before);ys,xs=np.nonzero(before);assert min(xs+dx)>=0 and min(ys+dy)>=0 and max(xs+dx)<384 and max(ys+dy)<384;after[ys+dy,xs+dx]=before[ys,xs]
  assert np.array_equal(np.bincount(before.flat,minlength=16),np.bincount(after.flat,minlength=16))
  pic=a.rgba(after,start);old=a.composite(n,mask)[0];assert pic.getbbox()[3]==old.getbbox()[3],(n,form,pic.getbbox(),old.getbbox())
  Image.fromarray(after).save(out/f'{form}_{n:03}_indices.png');pic.save(out/f'{form}_{n:03}_rgba.png')
  rows.append((f'{form} hover {n}',[('approved idle',a.composite(0,0 if mask==8 else 15)[0]),('current game',old),('new rigid registration',pic)]))
  ey,ex=np.nonzero(after==14);records.append({'ref':n,'form':form,'source':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p),'translation':[dx,dy],'color_counts_exact':True,'no_part_warping':True,'bbox':pic.getbbox(),'old_bbox':old.getbbox(),'lowest_foot_y_exact':True,'eye_world':[[int(x)-160,int(y)-160]for y,x in zip(ey,ex)],'eye_y_not_forced':True})
 helper.grid(rows,out/f'comparison_{n}.png',6)
(out/'manifest.json').write_text(json.dumps({'parent_sha256':sha(src),'frames':records,'scope':'새 원화 10몸체의 정수 평행이동만 수행. 동일그림 전체 픽셀/팔레트 개수 보존. 낮은발 기준 높이 정합; 얼굴각도에 따른 눈Y는 임의로 한점에 강제하지 않음.','final_art_accepted':False,'common_layers_verified':False,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print('10 whole-figure rigid registrations, all old lowest-foot heights exact')
