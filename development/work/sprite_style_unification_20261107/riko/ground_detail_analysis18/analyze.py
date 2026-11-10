"""Read-only sprite sharing/contact study. Outputs contain no replacement art."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent;W=D.parent
source=W/'prepared_spin_clothes_v1/PL01_U.ARC';arc=source.read_bytes();sha=lambda x:hashlib.sha256(x).hexdigest()
assert sha(arc)=='c68ef84d524a16062937359c52f9d640213b250ea2b679a673046f977d997e42'
keys=[(0,n)for n in(61,62,63,65,67,71,75,77,79,82,83,85,87,89,91,93,95,97,99,101,105,107,109,130,131,155,156,160)]+[(1,n)for n in(87,101,105,130,131)]
label=lambda k:f'b{k[0]}_{k[1]:03}'
data={k:render(arc,k[0],k[0]*5,k[1])[0]for k in keys}
pal=struct.unpack_from('<16H',entry(arc,9));idle=render(arc,0,0,147)[0]
for k,a in data.items():Image.fromarray(a).save(D/f'{label(k)}_indices.png')
def bbox(a):
 y,x=np.nonzero(a);return[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x)else None
def norm(a):
 bb=bbox(a)
 return (a[bb[1]:bb[3],bb[0]:bb[2]],bb)if bb else(np.zeros((0,0),np.uint8),None)
def groups(arrays,lower_y=None):
 grouped=collections.defaultdict(list)
 for k,a in arrays.items():
  if lower_y is None:z,bb=norm(a);anchor=bb[:2]
  else:
   z=a[lower_y:192];y,x=np.nonzero(z);assert len(x)>0
   xx=int(x.min());z=z[:,xx:int(x.max()+1)];anchor=[xx,lower_y]
  grouped[(z.shape,sha(z.tobytes()))].append((k,anchor,int(np.count_nonzero(z))))
 result=[]
 for _,rows in grouped.items():
  master,xy,_=rows[0]
  result.append({'master':label(master),'pixels':rows[0][2],'members':[{'key':label(k),'translation_from_master':[p[0]-xy[0],p[1]-xy[1]]}for k,p,_ in rows]})
 return result
frontpath=ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'
front=np.array(Image.open(frontpath))[:19,12:35];opaque=front>0;inside=np.zeros_like(opaque)
for y,r in enumerate(opaque):
 x=np.where(r)[0]
 if len(x):inside[y,x.min():x.max()+1]=True
headrows=[]
for k,a in data.items():
 options=[]
 for y in range(120,158):
  for x in range(120,181):
   q=a[y:y+19,x:x+23];mismatch=int(np.count_nonzero(q[opaque]!=front[opaque]));options.append((mismatch,x,y))
 mis,x,y=min(options);inner=int(np.count_nonzero(a[y:y+19,x:x+23][inside]!=front[inside]))
 mask=np.zeros_like(a,bool)
 if mis==0:mask[y:y+19,x:x+23]=inside;Image.fromarray(mask.astype(np.uint8)*255).save(D/f'{label(k)}_protect_head_mask.png')
 headrows.append({'key':label(k),'reference':'accepted_idle147_head23x19','opaque_pixels':int(opaque.sum()),'row_interior_mask_pixels':int(inside.sum()),'opaque_mismatches':mis,'row_interior_mismatches':inner,'anchor_world':[x-160,y-160]if mis==0 else None,'exact_head_and_negative_spaces':mis==inner==0,'mask_saved':mis==0})
rows=[]
for k,a in data.items():
 b,n=k;bank=graphics_bank(entry(arc,2),b);f=bank['frames'][n];foot={str(y-160):[int(x-160)for x in np.where(a[y]>0)[0]]for y in range(180,185)}
 rows.append({'key':label(k),'bbox':bbox(a),'pixels':int(np.count_nonzero(a)),'source_indexed_sha256':sha(a.tobytes()),'tile_count':f['tile_count'],'parts':composition_frame(entry(arc,3),b*5,n)['parts'],'shared_stream_refs':[g['index']for g in bank['frames']if g['offset']==f['offset']],'bottom_rows_world':foot})
pages=[]
for start in range(0,len(keys),4):
 subset=keys[start:start+4];sheet=Image.new('RGB',(2000,440),'#64717b');d=ImageDraw.Draw(sheet)
 for i,(title,a)in enumerate([('idle147',idle)]+[(label(k),data[k])for k in subset]):
  im=rgba(a,pal).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);sheet.paste(im,(i*400+8,60),im);d.text((i*400+8,10),title,fill='white')
  d.line((i*400+8,60+(169-112)*4,i*400+392,60+(169-112)*4),fill='#b96666')
  d.text((i*400+8,405),'red line: y169/world+9',fill='white')
 file=D/f'compare_{start//4:02}.png';sheet.save(file);pages.append({'path':str(file.relative_to(ROOT)),'sha256':sha(file.read_bytes()),'keys':[label(k)for k in subset],'actually_viewed':False})
report={'source':str(source.relative_to(ROOT)),'source_sha256':sha(arc),'count':len(keys),'world_origin':[160,160],'full_translation_groups':groups(data),'lower_groups':{str(y):groups(data,y)for y in(164,166,169,172)},'head_protection':headrows,'frames':rows,'pages':pages,'lower_limitations':'고정 y 아래의 모든 픽셀이 x 평행이동으로 정확히 일치한다는 뜻이다. 행보다 위의 무릎·허벅지·허리와 연결까지 같다는 의미는 아니다. 자동 분리·아트 수정은 하지 않는다.','source_unchanged':source.read_bytes()==arc,'game_data_written':False,'full_visual_review_completed':False}
(D/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'source':sha(arc),'count':len(keys),'full_groups':report['full_translation_groups'],'lower169':report['lower_groups']['169'],'head_exact':sum(r['exact_head_and_negative_spaces']for r in headrows)},ensure_ascii=False))
