"""지상 검격 새 원화의 원점·손목을 정합한다. 옛 몸체 덮기 없음."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'saber_followup05';O=D/'saber_followup05_registered_v1';assert not O.exists();O.mkdir()
arc=(D/'prepared_saber_followup04/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();assert sha(arc)=='8bfbf74ea8b14478d5b34906bbedf0e73d7a17689031c804545fb0a4ebac9c54'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
whole={244:(0,0),246:(0,0)}
parts={244:[],246:[]}
records=[];items={k:[]for k in('normal','black')}
for n,(dx,dy)in whole.items():
 source=A/'native'/f'b0_{n:03}_indices.png';a=np.array(Image.open(source));z=np.roll(a,(dy,dx),(0,1));ops=[{'whole_translation':[dx,dy]}]
 for points,(mx,my)in parts[n]:
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(points,fill=1);m=np.array(mask,bool);v=z.copy();ys,xs=np.where(m);z[m]=0;z[ys+my,xs+mx]=v[ys,xs];ops.append({'polygon':points,'translation':[mx,my],'source_negative_cells_preserved':True,'changed_pixels':int((v!=z).sum())})
 if n==246:
  z[148,156]=15;ops.append({'source_iris_cell':[156,148],'actual_cyan_source_pixels':29,'source_palette_index':15,'reason':'weighted cyan iris sample survived in original artwork but not majority quantization'})
 p=O/f'b0_{n:03}_indices.png';Image.fromarray(z).save(p);old=render(arc,0,0,n)[0]
 records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'source_native':rel(source),'source_native_sha256':sha(source.read_bytes()),'generated_sha256':sha((A/'generated.png').read_bytes()),'operations':ops,'output_sha256':sha(p.read_bytes()),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'old_head_or_body_override':False,'manually_invented_color':False})
 for form,words in [('normal',pal),('black',red)]:
  pic=rgba(z,words);pic.save(O/f'{form}_b0_{n:03}.png');items[form].extend([(f'{n} before',rgba(old,words)),(f'{n} source',rgba(a,words)),(f'{n} contacts',pic)])
for form,words in [('normal',pal),('black',red)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':sha(arc),'records':records,'candidate_only':True,'runtime_verified':False,'user_accepted':False,'scope':'Ground recovery244/246; generated native pixels at unchanged registration. Source cyan iris restored at156,148 from29 actual samples. No old body replacement.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(O)
