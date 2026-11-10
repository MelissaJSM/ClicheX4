"""Keep the new head/clothes; align source-authored hands and one boot contact."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'air_saber02';O=D/'air_saber02_registered_v2';assert not O.exists();O.mkdir()
arc=(D/'prepared_air_saber01/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT));assert sha(arc)=='2be858c073b05568f1b7d83b98e62b4f94a71899ae09a078cc0c3083e85c3a11'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
whole={221:(1,0),223:(2,0),225:(1,0),227:(3,1)}
parts={221:[([(138,142),(148,142),(153,144),(153,149),(148,154),(138,154)],(-1,-1)),([(168,128),(178,128),(179,138),(174,143),(165,143),(165,138)],(0,-1))],223:[([(140,137),(149,137),(155,141),(156,145),(151,150),(140,151)],(0,-1))],225:[([(140,140),(151,140),(156,144),(156,148),(151,152),(140,153)],(-1,0))],227:[([(166,167),(176,167),(177,178),(165,178)],(0,-1))]}
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
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':sha(arc),'records':records,'candidate_only':True,'runtime_verified':False,'user_accepted':False,'scope':'공중검격 후속4. 새 원화 전체 수평 정합과 손·커프1px,227 부츠1px 정합. 기존 머리나 옷을 덮지 않는다.'},ensure_ascii=False,indent=2)+'\n','utf8')
(A/'generation.json').write_text(json.dumps({'tool':'builtin image_gen','output_original':'<LOCAL_PATH>','sha256':sha((A/'generated.png').read_bytes()),'size':Image.open(A/'generated.png').size,'prompt_sha256':sha((A/'prompt.txt').read_bytes()),'raw_game_assets_sent':False,'runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(O)
