"""후면 재생성 원화를 전체 캔버스 비율 그대로 등록하고 조종석에서 대조한다."""
from pathlib import Path
import sys,hashlib,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';S=D/'ride_head_rear_fix01';O=D/'ride_head_registered_v2';O.mkdir(exist_ok=True)
j=json.loads((D/'ride_head01/inputs.json').read_text('utf8'));arc=(ROOT/j['source_arc']).read_bytes();pal=j['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32)
p=S/'generated.png';im=Image.open(p).convert('RGBA');assert im.size==(1774,887) and hashlib.sha256(p.read_bytes()).hexdigest()=='df5cf4752b9f80509b977a8014a1843b175592cc5c6a8ff5175bf23103497c6e'
colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);a=quantize(im,colors,32/887);assert a.shape==(32,64)
rec=[];masters={};targets={}
for m in j['masters']:
 n=m['ref']
 if n in (75,77):
  ix=(75,77).index(n);v=a[:,ix*32:(ix+1)*32].copy();outside=v.copy();outside[8:24,8:24]=0;assert not outside.any();tile=v[8:24,8:24].copy();kind='new_rear_source_fixed_full_canvas'
 else:tile=np.array(Image.open(D/'ride_head_registered_v1'/f'head_{n}_indices16.png'));kind='previous_candidate_exact'
 assert not tile[:,0].any();ys,xs=np.nonzero(tile);bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];masters[n]=tile;Image.fromarray(tile).save(O/f'head_{n}_indices16.png')
 for ref in m['aliases']:
  x,y,r,b=j['frames'][str(ref)]['world_bounds'];world=np.zeros((384,384),np.uint8);world[y:b,x:r]=tile;targets[ref]=world;Image.fromarray(world).save(O/f'b1_{ref:03}_indices.png')
 rec.append({'ref':n,'aliases':m['aliases'],'kind':kind,'bbox_in16tile':bbox,'height':bbox[3]-bbox[1],'components':[len(q)for q in connected_groups(tile>0)],'crop_or_scale_to_bbox':False,'whole_translation':[0,0]})
body=Image.open(D/'ride_cockpit_review01/native_body.png').convert('RGBA')
for form,words in [('normal',pal),('black',black)]:
 sheet=Image.new('RGB',(1400,800),(25,30,40));dr=ImageDraw.Draw(sheet)
 for row,n in enumerate((75,77)):
  old=render(arc,1,5,n)[0];v1=np.array(Image.open(D/'ride_head_registered_v1'/f'b1_{n:03}_indices.png'))
  for col,z in enumerate((old,v1,targets[n])):
   h=rgba(z,words).crop((96,96,224,224));comp=Image.alpha_composite(body,h);shown=comp.crop((36,16,92,66)).resize((392,350),Image.Resampling.NEAREST);sheet.paste(shown,(col*460+12,row*400+30),shown)
   dr.text((col*460+12,row*400+6),f'{n} '+('ORIGINAL','CANDIDATE1 small','REAR FIX2')[col],fill='white')
 sheet.save(O/f'{form}_cockpit_comparison.png')
 # Full five-master tile comparison, with source/current-native palettes.
 sh=Image.new('RGB',(1600,660),(25,30,40));dr=ImageDraw.Draw(sh)
 for k,m in enumerate(j['masters']):
  n=m['ref'];x,y,r,b=j['frames'][str(n)]['world_bounds'];old=render(arc,1,5,n)[0][y:b,x:r]
  for row,z in enumerate((old,masters[n])):
   pic=rgba(z,words).resize((256,256),Image.Resampling.NEAREST);sh.paste(pic,(k*320+24,row*330+30),pic)
  dr.text((k*320+10,4),f'{n} old / new2',fill='white')
 sh.save(O/f'{form}_comparison.png')
out={'source_arc_sha256':j['source_sha256'],'first_candidate_sha256':hashlib.sha256((D/'prepared_ride_heads01/PL01_U.ARC').read_bytes()).hexdigest(),'new_source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'fixed_canvas_scale':32/887,'native_canvas':[64,32],'records':rec,'registered_refs':[{'key':f'b1_{n:03}','sha256':hashlib.sha256((O/f'b1_{n:03}_indices.png').read_bytes()).hexdigest()}for n in targets],'scope':'75/77만 새 후면 원화를 재등록하고 다른 세 각도는 첫 후보와 완전 동일합니다. 몸체는 이전 실제 저장 화면에서 정확 복원한 조종석이며,75/77 원동작의 몸체 쌍 재생은 아닙니다.','root_review_pending':True,'runtime_verified':False,'user_accepted':False}
(O/'registration.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rec))
