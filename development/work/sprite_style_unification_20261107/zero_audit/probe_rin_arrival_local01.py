"""등장 신발/목의 새 원화 부위만 정수이동해 원접점과 나란히 비교한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.prepare_rin_run import connected_groups
R=Path(__file__).parent/'rin_extension';A=R/'arrival_detail01';P=R/'arrival_contacts_probe_v1';O=R/'arrival_contacts_probe_v3';O.mkdir(exist_ok=False)
info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['source']).read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
# Whole boot/lower shin, not old imagery or newly filled colors. Main knee is protected.
polys={249:[('right_leg_from_thigh',[(158,166),(164,166),(166,184),(157,184),(157,180),(158,176),(158,170),(157,167)],(2,0))],250:[('right_leg_from_thigh',[(158,166),(164,166),(166,184),(157,184),(157,180),(158,176),(158,170),(157,167)],(2,0))],253:[('head_bonnet',[(144,137),(166,137),(168,148),(162,151),(161,155),(154,157),(145,155)],(0,-1))]}
targets={};records=[]
for n in range(249,254):
 a=np.array(Image.open(P/f'b0_{n:03}_indices.png'));ops=[]
 for name,poly,(dx,dy)in polys.get(n,[]):
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(poly,fill=1);mask=np.array(mask)&(a>0);source=np.where(mask,a,0).astype(np.uint8);a[mask]=0;move=np.roll(np.roll(source,dy,0),dx,1);overlap=int(np.count_nonzero((move>0)&(a>0)));a[move>0]=move[move>0];ops.append({'region':name,'polygon':poly,'translation':[dx,dy],'source_pixels':int(mask.sum()),'new_source_overlap':overlap})
 p=O/f'b0_{n:03}_indices.png';Image.fromarray(a).save(p);targets[n]=a;eye=np.argwhere((a==15)&(np.indices(a.shape)[0]<160))[:,::-1];records.append({'ref':n,'source_sha256':sha(P/f'b0_{n:03}_indices.png'),'operations':ops,'output_sha256':sha(p),'components':[len(g)for g in connected_groups(a>0)],'eye_world':eye.tolist(),'floor_x':np.where(a[183]>0)[0].tolist(),'floor_y':int(np.where(a>0)[0].max())})
for form,words in [('normal',pal),('black',black)]:
 for page,ids in enumerate((list(range(249,252)),list(range(252,254)))):
  sh=Image.new('RGB',(1920,len(ids)*352),(28,34,45));dr=ImageDraw.Draw(sh)
  for i,n in enumerate(ids):
   for col,(label,v)in enumerate([('idle147',render(arc,0,0,147)[0]),(f'{n} old',render(arc,0,0,n)[0]),(f'{n} floor only',np.array(Image.open(P/f'b0_{n:03}_indices.png'))),(f'{n} local',targets[n])]):
    pic=rgba(v,words).crop((112,120,208,184)).resize((480,320),Image.Resampling.NEAREST);sh.paste(pic,(col*480,i*352+28),pic);dr.text((col*480+8,i*352+7),label,fill='white')
  sh.save(O/f'{form}_comparison_{page:02}.png')
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':info['source_sha256'],'generated_sha256':sha(A/'generated.png'),'source_registration':rel(P/'registration.json'),'source_registration_sha256':sha(P/'registration.json'),'records':records,'scope':'249/250 허벅지부터 오른다리 새원화 x+2,253새머리/보닛 y-1 국소 정합 시험. v2 종아리만 이동 시 무릎 경계가 굽어보여 배제. 원래머리/색채움/늘리기 없음. 시각검토 전.'},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
