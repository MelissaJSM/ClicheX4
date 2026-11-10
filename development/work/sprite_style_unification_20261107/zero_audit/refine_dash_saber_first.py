"""첫4키의 실제 cyan 눈 표본과164 새 머리의 국소 원점만 등록한다."""
from pathlib import Path
import hashlib,json,struct,sys
from collections import Counter,deque
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
from scripts.prepare_rin_run import connected_groups
D=Path(__file__).parent/'rin_extension'/'dash_saber_followup01';O=D/'registered_probe_v2';assert not O.exists();O.mkdir()
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();assert hashlib.sha256(arc).hexdigest()==info['archive_sha256']
pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32);im=np.array(Image.open(D/'generated.png').convert('RGBA'));cw=im.shape[1]/2
items={k:[]for k in('normal','black')};records=[]
for i,f in enumerate(info['frames']):
 key=f['key'];n=f['ref'];a=np.array(Image.open(D/'anchor_probe'/(key+'_indices.png')));v=a.copy();ops=[]
 if n==164:
  src=im[round(cw):round(cw*2),round(cw):round(cw*2)];r,g,b,al=np.moveaxis(src.astype(float),-1,0)
  yy,xx=np.where((r<g*.6)&(g>90)&(g/(b+1)>.6)&(g/(b+1)<1.15)&(al>=128));ct=Counter((112+int(x*96/src.shape[1]),104+int(y*96/src.shape[0]))for x,y in zip(xx,yy));point,count=ct.most_common(1)[0]
  assert point==(160,145)and count==28;ex,ey=point;ey+=1;assert v[ey,ex]>0
  ops.append({'operation':'source_eye_sample','point':[ex,ey],'before':int(v[ey,ex]),'after':15,'actual_cyan_source_pixels':count});v[ey,ex]=15
  polygon=[(141,134),(167,134),(167,152),(153,152),(148,149),(147,147),(141,146)]
  m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon(polygon,fill=1);region=np.array(m,bool)
  mask=region&(v>0)
  # Protect enclosed negative spaces, not the large empty polygon outside the hair.
  outside=np.zeros_like(mask);outside[0,0]=True;q=deque([(0,0)])
  while q:
   yy,xx=q.popleft()
   for oy,ox in ((0,1),(0,-1),(1,0),(-1,0)):
    ny,nx=yy+oy,xx+ox
    if 0<=ny<384 and 0<=nx<384 and not mask[ny,nx]and not outside[ny,nx]:outside[ny,nx]=True;q.append((ny,nx))
  mask|=~outside
  head=np.where(mask,v,0);remain=np.where(mask,0,v);moved=np.roll(head,2,axis=0);move_mask=np.roll(mask,2,axis=0)
  v=remain.copy();v[move_mask]=moved[move_mask]
  # The new head including all internal transparent cells is copied exactly.
  assert np.array_equal(v[move_mask],moved[move_mask]);assert np.count_nonzero(head)>100
  Image.fromarray(mask.astype('uint8')*255).save(O/'b0_164_head_mask.png')
  ops.append({'operation':'new_head_rigid_translation','polygon':polygon,'translation':[0,2],'old_head_override':False,'internal_negative_space_preserved':True,'source_opaque_pixels':int(np.count_nonzero(head))})
 old=render(arc,0,0,n)[0];Image.fromarray(v).save(O/(key+'_indices.png'))
 for name,words in [('normal',pal),('black',black)]:
  rgba(v,words).save(O/(name+'_'+key+'.png'));items[name].extend([(key+' old',rgba(old,words)),(key+' detailed candidate',rgba(v,words))])
 records.append({'key':key,'operations':ops,'old_cyan':np.argwhere(old==15)[:,::-1].tolist(),'new_cyan':np.argwhere(v==15)[:,::-1].tolist(),'components':[len(x)for x in connected_groups(v>0)],'bbox':rgba(v,pal).getbbox(),'indices_sha256':hashlib.sha256((O/(key+'_indices.png')).read_bytes()).hexdigest()})
for name,words in [('normal',pal),('black',black)]:page(items[name],rgba(render(arc,0,0,147)[0],words),O/(name+'_comparison.png'),cols=2,scale=5)
(O/'registration.json').write_text(json.dumps({'source_art_sha256':hashlib.sha256((D/'generated.png').read_bytes()).hexdigest(),'records':records,'candidate_only':True,'root_review_pending':True,'game_changed':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
