"""낙봉파 신규 원화를 고정 전체캔버스 배율로 등록한다. bbox fitting/구형 머리 복사 없음."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
R=D/'rin_extension';A=R/sys.argv[1];O=A/'native_fixed';O.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
info=read(A/'inputs.json');arc=(ROOT/info['source_arc']).read_bytes();assert hashlib.sha256(arc).hexdigest()==info['source_arc_sha256'];pal=struct.unpack_from('<16H',entry(arc,9));im=Image.open(A/'generated.png').convert('RGBA');assert im.width*2==im.height*3
colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);z=quantize(im,colors,192/im.width);assert z.shape==(128,192);alpha=np.array(im.getchannel('A').resize((192,128),Image.Resampling.BOX));Image.fromarray(alpha).save(O/'native_alpha.png');records=[];targets={}
def metrics(a):
 yy,xx=np.nonzero(a);eye=np.argwhere((a==15)&(np.indices(a.shape)[0]<165));floor=int(yy.max());groups=connected_groups(a>0)
 return {'bbox':rgba(a,pal).getbbox(),'eye_candidates_xy':eye[:,::-1].tolist(),'floor_y':floor,'floor_x':np.where(a[floor]>0)[0].tolist(),'component_sizes':[len(g)for g in groups],'pixels':len(yy)}
for rec in info['masters']:
 n=rec['ref'];cx,cy=rec['cell'];x,y,r,b=rec['world_crop'];a=np.zeros((384,384),np.uint8);a[y:b,x:r]=z[cy*64:cy*64+64,cx*96:cx*96+96];old=np.array(Image.open(A/f'b1_{n:03}_body_indices.png'));targets[n]=a;p=O/f'b1_{n:03}_indices.png';Image.fromarray(a).save(p);records.append({'ref':n,'old':metrics(old),'new':metrics(a),'target_path':rel(p),'sha256':sha(p),'whole_body_shift':[0,0],'old_head_override':False})
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(arc,9),row*32);sh=Image.new('RGB',(1440,len(records)*400),'#263142');dr=ImageDraw.Draw(sh)
 for iy,rec in enumerate(records):
  n=rec['ref']
  for ix,(tag,a)in enumerate([('idle147',render(arc,0,0,147)[0]),('old body',np.array(Image.open(A/f'b1_{n:03}_body_indices.png'))),('new body fixed1/8',targets[n])]):
   pic=rgba(a,words).crop((112,112,208,188)).resize((480,380),Image.Resampling.NEAREST);sh.paste(pic,(ix*480,iy*400+20),pic);dr.text((ix*480+4,iy*400+4),f'{n} {tag}',fill='white')
 sh.save(O/f'{form}_comparison.png')
j={'source_sha256':info['source_arc_sha256'],'generated_sha256':sha(A/'generated.png'),'source_size':im.size,'fixed_whole_canvas_scale':192/im.width,'alpha_threshold':128,'records':records,'effects_excluded':True,'runtime_verified':False,'user_accepted':False};(O/'registration.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j,ensure_ascii=False))
