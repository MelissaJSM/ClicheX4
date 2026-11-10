"""생성 원화→작은 머리38층만 독립 재구성한다. 제작 모듈·패커 미호출."""
from pathlib import Path
import hashlib,io,json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
OUT=Path(__file__).resolve().parent
H=ROOT/'work/sprite_style_unification_20261107/shibuki_audit'
assert not (OUT/'report.json').exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
tracked={}
def rel(p):return p.relative_to(ROOT).as_posix()
def read(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
def indexed(p):return np.array(Image.open(io.BytesIO(read(p))))
def same(a,b,why):assert np.array_equal(a,b),why
def coords(m):
 yy,xx=np.nonzero(m)
 return [[int(x)-160,int(y)-160]for y,x in zip(yy,xx)]
def bbox(z):
 yy,xx=np.nonzero(z)
 return [int(xx.min())-160,int(yy.min())-160,int(xx.max())+1-160,int(yy.max())+1-160]
lp=H/'prepared_vehicle_head_ultimate01/INPUT_LOCK.json'
lb=read(lp);assert sha(lb)=='9af12e9e1af6150475331e930ef7d5c3aec2dc2d36876558dd710788a8418a8f'
lock=json.loads(lb);assert len(lock['files'])==188
for path,h in lock['files'].items():assert sha(read(ROOT/path))==h,path
candidate=H/'prepared_vehicle_head_ultimate01/PL02_U.ARC'
assert sha(read(candidate))=='a0629d169d6b5a0d88f31faa5dc4866c7fef99245b278caedc92f523acb3f024'
parent=H/'prepared_hover_ultimate01/PL02_U.ARC'
pb=read(parent);assert sha(pb)=='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba'
a=Archive(pb)
src=H/'vehicle_head_ultimate_inputs01/generated_v1.png'
sb=read(src);assert sha(sb)=='77ceacf1088d549ede260c8cddb10cfcd9f39f1d823dea1692e651445c405d1b'
im=Image.open(io.BytesIO(sb)).convert('RGBA');assert im.size==(1254,1254)
rgba=np.array(im.resize((64,64),Image.Resampling.NEAREST))
rgb=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],dtype=np.int32)
pix=rgba[:,:,:3].astype(np.int32)
distances=np.stack([((pix-rgb[k])**2).sum(axis=2)for k in range(1,16)],axis=2)
idx=(np.argmin(distances,axis=2)+1).astype(np.uint8)
idx[rgba[:,:,3]<128]=0
same(rgba,indexed(H/'vehicle_head_ultimate_native01/whole64_rgba.png'),'fixed64 RGBA')
same(idx,indexed(H/'vehicle_head_ultimate_native01/whole64_indices.png'),'direct 15-color quantization')
master1=np.zeros((384,384),np.uint8);master1[101:165,125:189]=idx
same(master1,indexed(H/'vehicle_head_ultimate_native01/184_bank0_indices.png'),'first master0')
oldhead=a.layer(184,5)[0]
side=(oldhead>0)&(master1==2)
assert side.sum()==8 and ((oldhead>0)&~side).sum()==1
head=np.zeros_like(master1);head[side]=4
same(head,indexed(H/'vehicle_head_ultimate_native01/184_bank5_indices.png'),'first master5')
# HSV를 색상환 공식으로 직접 계산한다. 제작 함수/colorsys 호출 없이 실제 RGB 표본만 선택.
gold=[];final_idx=idx.copy()
for y in range(28,30):
 for x in range(27,36):
  red,green,blue=rgba[y,x,:3].astype(float)/255
  high=max(red,green,blue);low=min(red,green,blue);delta=high-low
  saturation=0.0 if high==0 else delta/high
  hue=0.0 if delta==0 else (60*((green-blue)/delta)%360 if high==red else 60*((blue-red)/delta+2) if high==green else 60*((red-green)/delta+4))
  if 28<=hue<=50 and saturation>=0.25 and high>=0.55:
   gold.append({'logical':[x,y],'world':[x-35,y-59],'RGB':list(map(int,rgba[y,x,:3])),'nearest':int(idx[y,x]),'gold':7,'hue':hue,'saturation':saturation,'value':high})
   final_idx[y,x]=7
assert len(gold)==10 and sum(r['nearest']!=7 for r in gold)==5
master=np.zeros((384,384),np.uint8);master[101:165,125:189]=final_idx
same(final_idx,indexed(H/'vehicle_head_ultimate_native02/whole64_indices.png'),'gold64')
same(master,indexed(H/'vehicle_head_ultimate_native02/184_bank0_indices.png'),'gold master0')
same(head,indexed(H/'vehicle_head_ultimate_native02/184_bank5_indices.png'),'gold master5')
same(master>0,master1>0,'gold alpha preservation')
assert bbox(master)==[-10,-37,3,-22] and (master>0).sum()==144
assert master[135,156]==7 and (master==7).sum()==11
oldalpha=a.layer(184,0)[0]>0
alpha_added=coords((master>0)&~oldalpha);alpha_removed=coords(oldalpha&~(master>0))
assert alpha_added==[[-5,-35]] and alpha_removed==[[-6,-36]]
td=H/'vehicle_head_ultimate_targets01'
manifest=json.loads(read(td/'manifest.json'));assert sha((td/'manifest.json').read_bytes())==lock['target_manifest_sha256']
master_old=a.composite(184,0)[0];oldbox=master_old.getbbox();source_before=a.composite(184,15)[0]
results=[]
for n in range(184,204):
 if n==198:continue
 after=a.composite(n,0)[0];before=a.composite(n,15)[0];nb=after.getbbox()
 assert after.crop(nb).tobytes()==master_old.crop(oldbox).tobytes()
 assert before.crop(nb).tobytes()==source_before.crop(oldbox).tobytes()
 dx,dy=nb[0]-oldbox[0],nb[1]-oldbox[1]
 layers={}
 for bank,data in((0,master),(5,head)):
  z=np.zeros_like(data);ys,xs=np.nonzero(data)
  assert min(xs+dx)>=0 and min(ys+dy)>=0 and max(xs+dx)<384 and max(ys+dy)<384
  z[ys+dy,xs+dx]=data[ys,xs]
  same(z,indexed(td/f'{n:03}_bank{bank}_indices.png'),f'target{n}/{bank}')
  assert sha(z.tobytes())==manifest['targets'][str(n)][str(bank)]
  layers[str(bank)]={'indexed_sha256':sha(z.tobytes()),'opaque':int((z>0).sum())}
 for bank in(6,7,8):
  target=indexed(td/f'{n:03}_bank{bank}_indices.png')
  assert not target.any()
  same(target,a.layer(n,bank)[0],f'empty source target{n}/{bank}')
 results.append({'ref':n,'translation':[dx,dy],'layers':layers})
Image.fromarray(master).save(OUT/'master184_bank0_indices.png')
Image.fromarray(head).save(OUT/'master184_bank5_indices.png')
for name in('register_vehicle_head_ultimate.py','register_vehicle_head_gold.py','prepare_vehicle_head_targets.py'):read(H/name)
for name in('register_vehicle_head_ultimate','register_vehicle_head_gold','prepare_vehicle_head_targets','native_pose_pack','prepare_lowhp_final'):assert name not in sys.modules
read(Path(__file__))
for path,h in lock['files'].items():assert sha((ROOT/path).read_bytes())==h,'input changed '+path
assert sha(candidate.read_bytes())==lock['candidate_sha256']
report={
 'scope':'작은 Ultimate 머리 원화1개 직접 고정64 양자화→금색10표본(변경5)→측면8소유→19원위치의38층 독립 재구성. ARC 디코딩/GPU/공유는HUD 담당.',
 'passed':True,'candidate_sha256':lock['candidate_sha256'],'parent_sha256':lock['parent_sha256'],
 'producer_input_lock_sha256':sha(lb),'producer_locked_input_count':188,
 'source':{'path':rel(src),'sha256':sha(sb),'actual_size':list(im.size),'sampling':'전체캔버스64×64 NEAREST,alpha128,실제CLUT0의15불투명색 최단RGB거리','individual_head_resize_or_old_overlay':False},
 'gold_samples':gold,'changed_from_nearest':5,'gold_total_including_iris':11,
 'head_geometry':{'bbox':bbox(master),'opaque':144,'iris_world':[-4,-25],'iris_index':7,'alpha_added':alpha_added,'alpha_removed':alpha_removed,'unchanged_outer_alpha_claimed':False},
 'before_side_ownership':{'parent_nonzero':int((oldhead>0).sum()),'new_side_cells':coords(side),'new_overlay_index':4,'removed_from_old_overlay':coords((oldhead>0)&~side),'policy':'기존측면9셀 중 새 보라색2인8셀만 파랑4. 나머지1셀 새고글은 공통0.'},
 'targets':results,'exact_owned_layers':38,'empty678_target_checks':57,
 'candidate_decoded':False,'new_MIPS_or_runtime':False,'producer_imported_or_called':False,'source_or_arc_changed':False,
 'limits':['최종ARC/비대상·물리공유/부분RGBA/GPU는본감사범위밖','별칭위치는현재부모19위치의실제표시에서읽음','198빈자원보존은HUD 별도검사','최종 조종석 표시·실기 수용은 별도'],
 'inputs':tracked}
p=OUT/'report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report_sha256':sha(p.read_bytes()),'passed':True,'owned_layers':38,'gold_samples':10,'gold_changed':5,'alpha_added':alpha_added,'alpha_removed':alpha_removed,'tracked':len(tracked)},ensure_ascii=False))
