"""현재303 후보에서 보존할 대기/전환10 및 파생정적2를 실제 재독출한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
R=D/'rin_extension';P=R/'prepared_burst_remaining02';O=R/'remaining303_review';O.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();arc=(P/'PL01_U.ARC').read_bytes();assert sha(arc)=='1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
refs=[(0,0),(0,1),(0,2),(0,146),(0,147),(0,148),(0,5),(0,6),(1,86),(1,0)];arrays={f'b{b}_{n:03}':render(arc,b,b*5,n)[0]for b,n in refs};idle=arrays['b0_147'];records=[];sheets=[]
for k,z in arrays.items():
 changed=z!=idle;y,x=np.nonzero(z);records.append({'ref':k,'pixels':int((z>0).sum()),'bbox':[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],'different_pixels_from_idle147':int(changed.sum()),'changed_bbox_from_idle':None if not changed.any() else[int(np.nonzero(changed)[1].min()),int(np.nonzero(changed)[0].min()),int(np.nonzero(changed)[1].max()+1),int(np.nonzero(changed)[0].max()+1)]})
for form,row in(('normal',0),('black',13)):
 pal=struct.unpack_from('<16H',entry(arc,9),row*32);sh=Image.new('RGB',(1536,1200),'#526274');dr=ImageDraw.Draw(sh)
 for i,(key,z)in enumerate(arrays.items()):
  out=z.copy();out[112:208,112:208]=0;assert not out.any();p=rgba(z,pal).crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST);x=i%4*384;y=i//4*400;sh.paste(p,(x,y+16),p);dr.text((x+3,y+2),key+(' = idle147'if np.array_equal(z,idle)else''),fill='white')
 path=O/f'baseline_{form}.png';sh.save(path);sheets.append({'path':rel(path),'sha256':sha(path.read_bytes()),'actually_viewed':False})
static=[];pal=struct.unpack('<16H',(P/'palette.bin').read_bytes())
for ref in(23,24):
 pix,size,bb,_=compose_static(entry(arc,0x10206),composition_frame(entry(arc,3),6,ref));z=np.zeros((384,384),np.uint8);z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);static.append((ref,z))
sh=Image.new('RGB',(1536,800),'#526274');dr=ImageDraw.Draw(sh)
for i,(ref,z)in enumerate(static):
 y,x=np.nonzero(z);crop=(int(x.min())-2,int(y.min())-2,int(x.max())+3,int(y.max())+3);p=rgba(z,pal).crop(crop);p=p.resize((p.width*4,p.height*4),Image.Resampling.NEAREST);assert p.width<=768 and p.height<780;sh.paste(p,(i*768,20),p);dr.text((i*768+3,3),f'static6_{ref:03} historical palette0x7803',fill='white')
path=O/'static_body_effects.png';sh.save(path);sheets.append({'path':rel(path),'sha256':sha(path.read_bytes()),'actually_viewed':False})
q={'candidate_sha256':sha(arc),'baseline_records':records,'static_refs':['static6_023','static6_024'],'sheets':sheets,'static_palette_status':'해시로 고정된 과거 CLUT0x7803이며 현재 실기 색 검증이 아니다. 일반/블랙 공통.','classification':'재작화303 외 대기/전환10 및 새몸체 파생정적2. 이 분류만으로 미술완료를 판정하지 않는다.','all_visually_reviewed':False,'runtime_verified':False,'user_accepted':False}
(O/'report.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
