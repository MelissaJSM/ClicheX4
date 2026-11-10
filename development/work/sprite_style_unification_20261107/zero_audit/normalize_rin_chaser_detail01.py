"""체이서4 원화를 고정1/8로 등록하고 원래 눈·손발 기준을 분리한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';A=D/'chaser_detail01';O=A/'native_fixed';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['source']).read_bytes();assert hashlib.sha256(arc).hexdigest()==info['source_sha256']
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
im=Image.open(A/'generated.png').convert('RGBA');assert im.size==(1536,1024)and sha(A/'generated.png')=='bc3858a5cabda3f8b8f58be6e2599f1a88538d4f05701761f9a0e47cae94ad86'
colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);z=quantize(im,colors,1/8);assert z.shape==(128,192)
records=[];bodies={};olds={}
for m in info['masters']:
 n=m['ref'];cx,cy=m['cell'];tile=z[cy*64:(cy+1)*64,cx*96:(cx+1)*96];a=np.zeros((384,384),np.uint8);a[120:184,112:208]=tile
 old=np.array(Image.open(A/f'b1_{n:03}_body_indices.png'));p=O/f'b1_{n:03}_indices.png';Image.fromarray(a).save(p);bodies[n]=a;olds[n]=old
 def metrics(v):
  yy,xx=np.nonzero(v);eye=np.argwhere((v==15)&(np.indices(v.shape)[0]<160));floor=int(yy.max());return {'bbox':rgba(v,pal).getbbox(),'eye_cells_world':eye[:,::-1].tolist(),'floor_y':floor,'floor_x':np.where(v[floor]>0)[0].tolist(),'component_sizes':[len(g)for g in connected_groups(v>0)],'opaque_pixels':len(yy)}
 records.append({'ref':n,'cell':[cx,cy],'fixed_world_crop':[112,120,208,184],'translation':[0,0],'old':metrics(old),'new':metrics(a),'output_sha256':sha(p),'old_head_override':False})
for form,words in [('normal',pal),('black',black)]:
 sh=Image.new('RGB',(1440,4*352),(28,34,45));dr=ImageDraw.Draw(sh);idle=render(arc,0,0,147)[0]
 for i,m in enumerate(info['masters']):
  n=m['ref']
  for col,(label,v)in enumerate([('idle147',idle),(f'{n} old body',olds[n]),(f'{n} new fixed',bodies[n])]):
   pic=rgba(v,words).crop((112,120,208,184)).resize((480,320),Image.Resampling.NEAREST);sh.paste(pic,(col*480,i*352+28),pic);dr.text((col*480+8,i*352+7),label,fill='white')
 sh.save(O/f'{form}_comparison.png')
generation={'tool':'builtin image_gen','saved_output':rel(A/'generated.png'),'output_sha256':sha(A/'generated.png'),'actual_size':im.size,'prompt':rel(A/'prompt.txt'),'prompt_sha256':sha(A/'prompt.txt'),'inputs':[{'path':rel(A/n),'sha256':sha(A/n),'actually_viewed_before_call':True}for n in('input.png','idle_full_reference.png','new_run8_detail_reference.png')],'original_output':'<LOCAL_PATH>','source_input_only_authored_mod_sprites':True,'source_game_original_sent':False,'scope':'체이서 몸체4만 새 원화. 리본/전체28파생·접점·패킹은 후속 검증.'}
(A/'generation.json').write_text(json.dumps(generation,ensure_ascii=False,indent=2)+'\n','utf8')
r={'source_sha256':info['source_sha256'],'generated_sha256':sha(A/'generated.png'),'scale':1/8,'alpha_threshold':128,'palette_words':pal,'old_art_override':False,'records':records,'runtime_verified':False,'user_accepted':False}
(O/'registration.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
