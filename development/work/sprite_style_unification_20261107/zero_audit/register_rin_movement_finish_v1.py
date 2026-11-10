"""Register only the new art at existing eye and floor anchors, no old pixels."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';S=D/'movement_finish01';O=D/'movement_finish_registered_v1';assert not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();arc=(D/'prepared_wall_followup_v2/PL01_U.ARC').read_bytes()
assert sha(arc)=='289370272eb51e377435e3fea0591921f4497fe3774d1f41e1d15d4d76d22ca2'
assert sha((S/'generated.png').read_bytes())=='f5567cc3bc73e52cf1de0d66a5f98a9cafbc0e4efcc8d39e2b1bdac7ce2bfc75'
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
polys={45:[(139,144),(159,144),(160,145),(166,145),(166,153),(161,156),(158,158),(151,159),(147,159),(140,157)],193:[(142,134),(158,134),(159,136),(166,136),(167,143),(164,146),(159,147),(157,151),(149,151),(145,149),(142,146)]}
shifts={45:(0,1),193:(1,1)};whole={37:(0,0),45:(0,0),193:(3,0)};records=[];targets={}
for n in(37,45,193):
 p=S/'native'/f'b0_{n:03}_indices.png';a=np.array(Image.open(p));old=render(arc,0,0,n)[0];b=a.copy()
 if n in polys:
  m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon(polys[n],fill=1);m=np.array(m,dtype=bool);dx,dy=shifts[n];b[m]=0
  y,x=np.where(m);yy,xx=y+dy,x+dx;assert np.all((xx>=0)&(xx<384)&(yy>=0)&(yy<384));b[yy,xx]=a[y,x]
  # No zero old-body paste: translated head includes its negative spaces.
  assert np.array_equal(b[yy,xx],a[y,x])
 dx,dy=whole[n];b=np.roll(np.roll(b,dx,axis=1),dy,axis=0)
 assert b.max()<=15;before_floor=int(np.where(old>0)[0].max());after_floor=int(np.where(b>0)[0].max());assert before_floor==after_floor
 Image.fromarray(b).save(O/f'b0_{n:03}_indices.png');targets[n]=b
 def eyes(z):
  yy,xx=np.where((z==15)&(np.indices(z.shape)[0]<165));return list(map(list,zip(xx.tolist(),yy.tolist())))
 records.append({'key':f'b0_{n:03}','generic_path':str(p.relative_to(ROOT)),'generic_sha256':sha(p.read_bytes()),'head_polygon':polys.get(n),'head_translation':shifts.get(n,[0,0]),'whole_translation':whole[n],'old_eye_pixels':eyes(old),'new_eye_pixels':eyes(b),'floor_before':before_floor,'floor_after':after_floor,'old_toe_row_x':np.where(old[before_floor]>0)[0].tolist(),'new_toe_row_x':np.where(b[after_floor]>0)[0].tolist(),'native_sha256':sha((O/f'b0_{n:03}_indices.png').read_bytes()),'old_body_pixels_pasted':0})
for name,words in [('normal',pal),('black',black)]:
 items=[]
 for n in(37,45,193):
  im=rgba(targets[n],words);im.save(O/f'{name}_b0_{n:03}.png');items.extend([(f'{n} before',rgba(render(arc,0,0,n)[0],words)),(f'{n} registered',im)])
 page(items,rgba(render(arc,0,0,147)[0],words),O/f'{name}_comparison.png',cols=2,scale=5)
report={'source_arc_sha256':sha(arc),'source_art_sha256':sha((S/'generated.png').read_bytes()),'generic_registration_sha256':sha((S/'native/registration.json').read_bytes()),'scope':'193 새 전신을x+3,193 머리만(+1,+1),45 머리만y+1 정합. 원점/타이밍/판정은 아직 변경하지 않은 작업 원화다.','records':records,'palette_changed':False,'per_pose_scaling':False,'old_body_pixels_pasted':0,'root_review_pending':True,'user_accepted':False,'game_changed':False}
(O/'registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'out':str(O),'records':records}))
