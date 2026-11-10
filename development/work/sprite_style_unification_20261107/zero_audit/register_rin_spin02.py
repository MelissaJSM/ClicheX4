"""빙열참 준비와 회전 원화의 국소 접점 정합. 옛 몸체 덮기 없음."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'ice_spin02';O=D/'ice_spin_registered_v1'
assert not O.exists();O.mkdir();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
arc=(D/'prepared_ice01/PL01_U.ARC').read_bytes();assert sha(arc)=='70b483ba78dedefa9c4af45c9b4c5fe4fb8ef915290a4c92c1dd5dea6b0b01d8'
assert sha((A/'generated.png').read_bytes())=='ad1bde14dfc0979dbeab30f6534e50935d8182356d61b2b331c68539a8b1b035'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
parts={144:[([(133,177),(140,176),(143,177),(143,184),(133,184)],(0,-1),'left_new_boot_contact')],161:[],
       163:[([(141,153),(148,153),(151,155),(156,155),(158,161),(157,167),(152,168),(141,166)],(3,0),'new_head_to_original_eye_x')]}
rows=[];items={k:[]for k in('normal','black')}
for n in (144,161,163):
 p=A/'native'/f'b1_{n:03}_indices.png';a=np.array(Image.open(p));z=a.copy();ops=[]
 for poly,(dx,dy),purpose in parts[n]:
  m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon(poly,fill=1);m=np.array(m,bool);v=z.copy();ys,xs=np.where(m);z[m]=0;z[ys+dy,xs+dx]=v[ys,xs]
  ops.append({'polygon':poly,'translation':[dx,dy],'purpose':purpose,'source_negative_cells_preserved':True,'changed_pixels':int((v!=z).sum())})
 out=O/f'b1_{n:03}_indices.png';Image.fromarray(z).save(out);old=render(arc,1,5,n)[0]
 rows.append({'key':f'b1_{n:03}','bank':1,'ref':n,'source_native':rel(p),'source_native_sha256':sha(p.read_bytes()),'operations':ops,'output_sha256':sha(out.read_bytes()),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'old_head_or_body_override':False,'manually_invented_color':False})
 for form,words in [('normal',pal),('black',red)]:
  pic=rgba(z,words);pic.save(O/f'{form}_b1_{n:03}.png');items[form].extend([(f'{n} before',rgba(old,words)),(f'{n} source',rgba(a,words)),(f'{n} contacts',pic)])
for form,words in [('normal',pal),('black',red)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':sha(arc),'source_generated_sha256':sha((A/'generated.png').read_bytes()),'records':rows,'candidate_only':True,'runtime_verified':False,'user_accepted':False,'scope':'빙열참 준비144 왼발1px 위 정합; 회전161 유지,163 새 머리만x+3 정합. 회전중심·타이밍·기존 신체 그림을 덮지 않는 새 원화의 국소 등록.'},ensure_ascii=False,indent=2)+'\n','utf8');print(O)
