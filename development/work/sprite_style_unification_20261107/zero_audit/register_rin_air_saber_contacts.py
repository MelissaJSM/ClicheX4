"""New authored air-saber contact registration; never paste an old face/body."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'air_saber01';O=D/'air_saber_registered_v1';assert not O.exists();O.mkdir()
arc=(D/'prepared_ground_remaining_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
assert sha(arc)=='a8a268fa92912678e70b01b776ffa477dd46c16e791f16f3346c76cd55016319'
assert sha((A/'generated.png').read_bytes())=='3e7180ca51695c2661de6136c226143367334b62b41841f57e4946bc60d4c379'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
whole={213:0,215:2,217:1,219:3}
hands={213:([(140,145),(149,145),(158,148),(158,152),(153,155),(140,155)],(0,1)),215:([(140,136),(148,136),(152,139),(154,142),(159,144),(159,147),(152,148),(140,145)],(1,1)),217:([(134,146),(143,146),(152,149),(156,149),(156,153),(151,156),(134,157)],(1,1)),219:([(135,140),(145,140),(152,142),(155,142),(155,146),(148,149),(135,149)],(1,0))}
items={k:[]for k in('normal','black')};records=[]
for n in whole:
 source=A/'native'/f'b0_{n:03}_indices.png';a=np.array(Image.open(source));z=np.roll(a,whole[n],axis=1);raw=z.copy();points,(dx,dy)=hands[n];im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon(points,fill=1);mask=np.array(im,bool)
 ys,xs=np.where(mask);z[mask]=0;z[ys+dy,xs+dx]=raw[ys,xs]
 changed=raw!=z;assert not np.any(changed[:135]);assert not np.any(changed[160:]);assert np.all(z<16)
 p=O/f'b0_{n:03}_indices.png';Image.fromarray(z).save(p);Image.fromarray(mask.astype(np.uint8)*255).save(O/f'b0_{n:03}_hand_scope.png');old=render(arc,0,0,n)[0]
 records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'source_native':rel(source),'source_native_sha256':sha(source.read_bytes()),'generated_sha256':sha((A/'generated.png').read_bytes()),'operations':[{'whole_translation':[whole[n],0]},{'new_hand_forearm_polygon':points,'translation':[dx,dy],'source_negative_cells_preserved':True,'changed_pixels':int(changed.sum())}],'output_sha256':sha(p.read_bytes()),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'old_head_or_body_override':False,'manually_invented_color':False})
 for form,words in [('normal',pal),('black',red)]:
  pic=rgba(z,words);pic.save(O/f'{form}_b0_{n:03}.png');items[form].extend([(f'{n} before',rgba(old,words)),(f'{n} source',rgba(a,words)),(f'{n} contacts',pic)])
for form,words in [('normal',pal),('black',red)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':sha(arc),'records':records,'candidate_only':True,'runtime_verified':False,'user_accepted':False,'scope':'새 원화 전신의 수평 정합 및 앞손·커프의 국소 강체 이동. 기존 머리·몸체를 덮지 않으며 검기는 바꾸지 않는다.'},ensure_ascii=False,indent=2)+'\n','utf8');print(O)
