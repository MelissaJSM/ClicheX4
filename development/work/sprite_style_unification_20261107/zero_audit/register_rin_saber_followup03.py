"""새 원화의 관절을 원래 세계 원점에 정합하고 고정 팔레트로 비교한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'saber_followup03';O=D/'saber_followup03_registered_v1';assert not O.exists();O.mkdir()
arc=(D/'prepared_air_saber02/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();assert sha(arc)=='9dc63497fbc367cd7330e0c4337bb208b75cee76f2ecbbf0faaaa72b73ee66a4'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
whole={229:(1,2),230:(6,0),232:(2,0),234:(6,0)}
parts={229:[([(166,168),(178,168),(178,182),(164,182),(164,174)],(0,-2))],230:[],232:[],234:[]}
records=[];items={k:[]for k in('normal','black')}
for n,(dx,dy)in whole.items():
 source=A/'native'/f'b0_{n:03}_indices.png';a=np.array(Image.open(source));z=np.roll(a,(dy,dx),(0,1));ops=[{'whole_translation':[dx,dy]}]
 for points,(mx,my)in parts[n]:
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(points,fill=1);m=np.array(mask,bool);v=z.copy();ys,xs=np.where(m);z[m]=0;z[ys+my,xs+mx]=v[ys,xs];ops.append({'polygon':points,'translation':[mx,my],'source_negative_cells_preserved':True,'changed_pixels':int((v!=z).sum())})
 p=O/f'b0_{n:03}_indices.png';Image.fromarray(z).save(p);old=render(arc,0,0,n)[0]
 records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'source_native':rel(source),'source_native_sha256':sha(source.read_bytes()),'generated_sha256':sha((A/'generated.png').read_bytes()),'operations':ops,'output_sha256':sha(p.read_bytes()),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'old_head_or_body_override':False,'manually_invented_color':False})
 for form,words in [('normal',pal),('black',red)]:
  pic=rgba(z,words);pic.save(O/f'{form}_b0_{n:03}.png');items[form].extend([(f'{n} before',rgba(old,words)),(f'{n} source',rgba(a,words)),(f'{n} contacts',pic)])
for form,words in [('normal',pal),('black',red)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':sha(arc),'records':records,'candidate_only':True,'runtime_verified':False,'user_accepted':False,'scope':'공중 마지막229 및 지상230/232/234. 새 원화의 전신 수평 위치와229의 목/손 높이·부츠 접점을 따로 정합했다. 옛 머리·몸체나 새 임의 색을 덮지 않았다.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(O)
