"""75 보닛 상단의 새 원화만 등록하고 나머지 수용 머리/턱을 보존한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.overhaul_sprites_audit import rgba,render
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';S=D/'ride_head75_crown_fix02';P=D/'ride_head_registered_v2';O=D/'ride_head_registered_v3';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=json.loads((D/'ride_head01/inputs.json').read_text('utf8'));pal=j['palette_words'];arc=(ROOT/j['source_arc']).read_bytes();black=struct.unpack_from('<16H',entry(arc,9),13*32)
assert sha(S/'generated.png')=='251194b9e4ab9f58983d41a1e81b3a1bd44978cff585e475c782c7e1764bfc7a'
im=Image.open(S/'generated.png').convert('RGBA');assert im.size==(1254,1254);colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);native=quantize(im,colors,32/1254);assert native.shape==(32,32);Image.fromarray(native).save(O/'source_native32.png')
masters={};targets={};records=[]
for m in j['masters']:
 n=m['ref'];old=np.array(Image.open(P/f'head_{n}_indices16.png'));z=old.copy();changes=[]
 if n==75:
  z[2:7,1:15]=native[10:15,9:23]
  yy,xx=np.nonzero(z!=old);changes=[{'tile_xy':[int(x),int(y)],'source_native_xy':[int(x+8),int(y+8)],'old':int(old[y,x]),'new':int(z[y,x])}for y,x in zip(yy,xx)]
  assert len(changes)>0 and np.array_equal(z[7:],old[7:])
 assert not z[:,0].any()and len(connected_groups(z>0))==1;masters[n]=z;Image.fromarray(z).save(O/f'head_{n}_indices16.png')
 for ref in m['aliases']:
  x,y,r,b=j['frames'][str(ref)]['world_bounds'];world=np.zeros((384,384),np.uint8);world[y:b,x:r]=z;targets[ref]=world;Image.fromarray(world).save(O/f'b1_{ref:03}_indices.png')
 yy,xx=np.nonzero(z);records.append({'ref':n,'aliases':m['aliases'],'v2_head_source_sha256':sha(P/f'head_{n}_indices16.png'),'output_sha256':sha(O/f'head_{n}_indices16.png'),'bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'semantic_source_changes':changes,'v2_lower_head_and_chin_exact':True})
body=Image.open(D/'ride_cockpit_review01/native_body.png').convert('RGBA')
for form,words in [('normal',pal),('black',black)]:
 sh=Image.new('RGB',(1400,800),(25,30,40));dr=ImageDraw.Draw(sh)
 for row,n in enumerate((75,77)):
  variants=(render(arc,1,5,n)[0],np.array(Image.open(P/f'b1_{n:03}_indices.png')),targets[n])
  for col,z in enumerate(variants):
   comp=Image.alpha_composite(body,rgba(z,words).crop((96,96,224,224)));pic=comp.crop((36,16,92,66)).resize((392,350),Image.Resampling.NEAREST);sh.paste(pic,(col*460+12,row*400+30),pic);dr.text((col*460+12,row*400+6),f'{n} '+('ORIGINAL','REAR FIX2','CROWN FIX3')[col],fill='white')
 sh.save(O/f'{form}_cockpit_comparison.png')
 reg=Image.new('RGB',(1600,660),(25,30,40));dr=ImageDraw.Draw(reg)
 for i,m in enumerate(j['masters']):
  n=m['ref'];x,y,r,b=j['frames'][str(n)]['world_bounds'];old=render(arc,1,5,n)[0][y:b,x:r]
  for row,z in enumerate((old,masters[n])):
   pic=rgba(z,words).resize((256,256),Image.Resampling.NEAREST);reg.paste(pic,(i*320+24,row*330+30),pic)
  dr.text((i*320+8,4),f'{n} old / new3',fill='white')
 reg.save(O/f'{form}_comparison.png')
r={'source_arc_sha256':j['source_sha256'],'generated_sha256':sha(S/'generated.png'),'generated_sources':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)}for p in (D/'ride_head01/generated.png',D/'ride_head_rear_fix01/generated.png',S/'generated.png')],'fixed_canvas_scale':32/1254,'records':records,'registered_refs':[{'key':f'b1_{n:03}','output_sha256':sha(O/f'b1_{n:03}_indices.png')}for n in targets],'scope':'75 상단14×5 격자에서 새 원화 표본만 채택합니다. 턱/아래 머리와77 및 다른세각도는 수용 후보 그대로입니다. 옛 단순 머리 덮기/늘리기/코드 색채움 없음.','root_review_pending':True,'runtime_verified':False,'user_accepted':False}
(O/'registration.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'changes75':len(records[1]['semantic_source_changes']),'records':[(x['ref'],x['bbox'])for x in records]}))
