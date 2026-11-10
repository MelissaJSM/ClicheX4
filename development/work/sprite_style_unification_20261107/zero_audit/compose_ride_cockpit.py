"""실제 보존 상태의 조립/VRAM으로 조종석을 재구성하고 화면과 대조한다."""
from pathlib import Path
import sys,gzip,hashlib,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.epsxe_state import framebuffer
D=Path(__file__).parent/'rin_extension';O=D/'ride_cockpit_review01'
P=ROOT/'work/ver_rin_nana/checkpoints/ride_armor_accepted_20261029T005856936087Z/accepted_ride_armor/SLUS_005.61.000'
s=gzip.decompress(P.read_bytes());ram=s[442:442+2097152];vram=np.frombuffer(s,dtype='<u2',count=524288,offset=2569183).reshape(512,1024)
def pal(clut):
 w=vram[clut>>6,(clut&63)*16:(clut&63)*16+16].astype(np.uint32)
 return np.array([[(int(x)>>z&31)*255//31 for z in(0,5,10)]+[0 if i==0 else 255]for i,x in enumerate(w)],np.uint8)
def parts(n):
 p=0x1b9f78;h=struct.unpack_from('<I',ram,p+n*4)[0]
 return [struct.unpack_from('<BBbb',ram,p+(h>>16)*4+i*4)for i in range(h&65535)]
def draw(n,bx,by,pagedir,reverse,page1=None):
 a=np.zeros((128,128,4),np.uint8)
 for fl,t,x,y in (list(reversed(parts(n)))if reverse else parts(n)):
  if not (-64<=x<=48 and -64<=y<=48):return None
  page=fl&3;clut=0x7848+((fl>>2)&3);xx=bx+(page*64 if pagedir=='x'else 0)+(t%16)*4;yy=by+(page*256 if pagedir=='y'else 0)+(t//16)*16
  if page and page1:xx=page1[0]+(t%16)*4;yy=page1[1]+(t//16)*16
  if xx+4>1024 or yy+16>512:return None
  w=vram[yy:yy+16,xx:xx+4];ix=np.stack([(w>>z)&15 for z in (0,4,8,12)],axis=2).reshape(16,16);q=pal(clut)[ix]
  if fl&64:q=q[:,::-1]
  if fl&128:q=q[::-1]
  box=a[64+y:80+y,64+x:80+x];mask=q[:,:,3]>0;box[mask]=q[mask]
 return a
screen=np.array(framebuffer(s,2569183,0));crop=screen[83:211,96:224];scores=[]
for bx in range(0,1024,64):
 for by in(0,256):
  for pd in('x','y'):
   for rev in(False,True):
    a=draw(0,bx,by,pd,rev)
    if a is None:continue
    m=a[:,:,3]>0;good=np.all(a[:,:,:3]==crop,axis=2)&m
    scores.append({'bx':bx,'by':by,'page_direction':pd,'reverse':rev,'opaque':int(m.sum()),'matched':int(good.sum()),'ratio':float(good.sum()/max(1,m.sum()))})
scores.sort(key=lambda q:q['ratio'],reverse=True)
(O/'texture_layout_probe.json').write_text(json.dumps(scores[:12],indent=2)+'\n','utf8')
for i,c in enumerate(scores[:4]):Image.fromarray(draw(0,c['bx'],c['by'],c['page_direction'],c['reverse'])).resize((768,768),Image.Resampling.NEAREST).save(O/f'body_probe_{i}.png')
print(json.dumps(scores[:4]))
from src.epsxe_state import match_sprite
base=draw(0,384,0,'x',False);mask=base[:,:,3]>0;ys,xs=np.nonzero(mask);bb=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
matches=match_sprite(Image.fromarray(screen),Image.fromarray(base).crop(bb));print('matches',matches)
best=[]
for py in range(137,156):
 for px in range(150,171):
  for flip in(False,True):
   q=base[:,::-1]if flip else base;m=q[:,:,3]>0;c=screen[py-64:py+64,px-64:px+64];good=np.all(q[:,:,:3]==c,axis=2)&m;best.append((int(good.sum()),px,py,flip))
best.sort(reverse=True);print('offsets',best[:8]);(O/'scene_match_probe.json').write_text(json.dumps({'body_bounds':bb,'exact_matches':matches,'nearest':best[:8]},indent=2)+'\n','utf8')
frames=[]
for n in range(77):
 a=draw(n,384,0,'x',False)
 if a is None:continue
 m=a[:,:,3]>0;c=screen[85:213,96:224];good=np.all(a[:,:,:3]==c,axis=2)&m;frames.append((int(good.sum()),int(m.sum()),n))
frames.sort(reverse=True);print('frames',frames[:8]);(O/'body_frame_probe.json').write_text(json.dumps(frames[:12],indent=2)+'\n','utf8')
im=Image.new('RGB',(1536,768),(25,30,40));im.paste(Image.fromarray(screen[85:213,96:224]).resize((768,768),Image.Resampling.NEAREST),(0,0));b=Image.fromarray(base).resize((768,768),Image.Resampling.NEAREST);im.paste(b,(768,0),b);im.save(O/'body_scene_comparison.png')
diff=(base[:,:,3]>0)&np.any(base[:,:,:3]!=screen[85:213,96:224],axis=2);ys,xs=np.nonzero(diff);print('diffbbox', [int(xs.min()-64),int(ys.min()-64),int(xs.max()-63),int(ys.max()-63)])
alts=[]
for bx in range(0,1024,32):
 for by in (0,128,256,384):
  a=draw(0,384,0,'x',False,(bx,by));m=a[:,:,3]>0;good=np.all(a[:,:,:3]==screen[85:213,96:224],axis=2)&m;alts.append((int(good.sum()),int(m.sum()),bx,by))
alts.sort(reverse=True);print('page1',alts[:6]);(O/'page1_probe.json').write_text(json.dumps(alts[:12],indent=2)+'\n','utf8')
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
arc=(D/'prepared_bank1_recovery128/PL01_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9));head=rgba(render(arc,1,5,66)[0],words).crop((96,96,224,224));body=Image.fromarray(draw(0,384,0,'x',False,(576,128)));combined=Image.alpha_composite(body,head);z=np.array(combined);m=z[:,:,3]>0;eq=np.all(z[:,:,:3]==screen[85:213,96:224],axis=2)&m
proof={'body_origin_screen':[160,149],'body_frame':0,'resident_object':'0x80173a30','parts_address':'0x801b9f78','texture_page0_words':[384,0],'texture_page1_words':[576,128],'clut':'0x7848','head66_source':'prepared_bank1_recovery128','opaque_pixels':int(m.sum()),'exact_screen_pixels':int(eq.sum()),'whole_composite_exact':bool(np.all(eq[m])),'scene_is_old_saved_capture':True,'new_head_game_runtime_verified':False}
(O/'scene_composition_proof.json').write_text(json.dumps(proof,indent=2)+'\n','utf8');combined.resize((768,768),Image.Resampling.NEAREST).save(O/'actual_body_and_head66.png');print('complete',proof)
body.save(O/'native_body.png')
rows=[];sheet=Image.new('RGB',(1536,5*430),(25,30,40));dr=ImageDraw.Draw(sheet)
for i,n in enumerate((66,75,77,78,81)):
 old=rgba(render(arc,1,5,n)[0],words).crop((96,96,224,224));ni=np.array(Image.open(D/'ride_head_registered_v1'/f'b1_{n:03}_indices.png'));new=rgba(ni,words).crop((96,96,224,224))
 for k,h in enumerate((old,new)):
  comp=Image.alpha_composite(body,h);comp.save(O/f'context_{n}_{k}.png')
  pic=comp.crop((28,16,104,108)).resize((304,368),Image.Resampling.NEAREST);sheet.paste(pic,(k*330+12,i*430+35),pic)
  cp=comp.crop((42,20,86,52)).resize((352,256),Image.Resampling.NEAREST);sheet.paste(cp,(660+k*420,i*430+75),cp)
 dr.text((15,i*430+8),f'HEAD {n}: OLD / CANDIDATE | same captured mech frame0, origin fixed; pose-context preview',fill='white')
 rows.append({'head':n,'mech_frame':0,'head_world_origin':[160,160],'same_mech_body_rgba':True,'head_native_geometry':True,'exact_native_body_head_pair_verified':n==66,'limitation':'66 이외는 같은 실제 조종석에 각 머리를 원래 위치로 놓은 크기 비교이며 해당 동작의 실제 몸체 쌍을 재생한 것은 아닙니다.'})
sheet.save(O/'cockpit_old_new.png');(O/'context_manifest.json').write_text(json.dumps({'rows':rows,'source_state_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'body_source':'native_body.png','proof':'scene_composition_proof.json','candidate_frozen':False,'actual_view_pending':True},ensure_ascii=False,indent=2)+'\n','utf8')
