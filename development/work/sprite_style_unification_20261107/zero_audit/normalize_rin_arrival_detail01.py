"""등장5 원화의 전체 캔버스 비율을 고정해 등록하며 포즈별 bbox축소는 하지 않는다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
R=Path(__file__).parent/'rin_extension';A=R/'arrival_detail01';O=A/'native_fixed';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();info=json.loads((A/'inputs.json').read_text('utf8'))
arc=(ROOT/info['source']).read_bytes();assert hashlib.sha256(arc).hexdigest()==info['source_sha256'];pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
im=Image.open(A/'generated.png').convert('RGBA');assert im.width==im.height and sha(A/'generated.png')=='bf30c20b17cb4002e980f8ef135ff96b0304adbd4a258f98bf9bdff16de89ac9'
colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);z=quantize(im,colors,192/im.width);assert z.shape==(192,192) and not np.any(z[128:,96:])
records=[];targets={}
def metrics(v):
 yy,xx=np.nonzero(v);eye=np.argwhere((v==15)&(np.indices(v.shape)[0]<160));floor=int(yy.max())
 return {'bbox':rgba(v,pal).getbbox(),'eye_cells_world':eye[:,::-1].tolist(),'floor_y':floor,'floor_x':np.where(v[floor]>0)[0].tolist(),'component_sizes':[len(g)for g in connected_groups(v>0)],'opaque_pixels':len(yy)}
for m in info['masters']:
 n=m['ref'];cx,cy=m['cell'];a=np.zeros((384,384),np.uint8);a[120:184,112:208]=z[cy*64:(cy+1)*64,cx*96:(cx+1)*96];p=O/f'b0_{n:03}_indices.png';Image.fromarray(a).save(p);targets[n]=a
 old=np.array(Image.open(A/f'b0_{n:03}_indices.png'));records.append({'ref':n,'old':metrics(old),'new':metrics(a),'path':rel(p),'sha256':sha(p),'whole_body_shift':[0,0],'old_head_override':False})
for form,words in [('normal',pal),('black',black)]:
 for page,ids in enumerate((list(range(249,252)),list(range(252,254)))):
  sh=Image.new('RGB',(1440,len(ids)*352),(28,34,45));dr=ImageDraw.Draw(sh)
  for i,n in enumerate(ids):
   for col,(label,v)in enumerate([('idle147',render(arc,0,0,147)[0]),(f'{n} old',render(arc,0,0,n)[0]),(f'{n} new fixed',targets[n])]):
    pic=rgba(v,words).crop((112,120,208,184)).resize((480,320),Image.Resampling.NEAREST);sh.paste(pic,(col*480,i*352+28),pic);dr.text((col*480+8,i*352+7),label,fill='white')
  sh.save(O/f'{form}_comparison_{page:02}.png')
generation={'tool':'builtin image_gen','path':rel(A/'generated.png'),'sha256':sha(A/'generated.png'),'actual_size':im.size,'requested_size':[1536,1536],'fixed_canvas_scale':192/im.width,'native_whole_sheet':[192,192],'bbox_fit_used':False,'prompt':rel(A/'prompt.txt'),'prompt_sha256':sha(A/'prompt.txt'),'references':[{'path':rel(A/n),'sha256':sha(A/n),'actually_viewed':True}for n in('input.png','idle_full_reference.png','new_victory6_detail_reference.png')],'source_game_original_sent':False,'default_path':'<LOCAL_PATH>'}
(A/'generation.json').write_text(json.dumps(generation,ensure_ascii=False,indent=2)+'\n','utf8')
(O/'registration.json').write_text(json.dumps({'source_sha256':info['source_sha256'],'generated_sha256':sha(A/'generated.png'),'scale':192/im.width,'alpha_threshold':128,'records':records,'runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'size':im.size,'records':records},ensure_ascii=False))
