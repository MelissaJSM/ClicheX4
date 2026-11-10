"""Candidate registration of new detail art; all pixels originate in authored art."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'after141_registered_v1';assert not O.exists();O.mkdir()
arc=(D/'prepared_ground_wall_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
assert sha(arc)=='247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
iris={q['ref']:q['votes']for q in json.loads((D/'after141_contact_review/iris.json').read_text('utf8'))}
def poly(points):
 m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon(points,fill=1);return np.array(m,bool)
def move(z,points,delta,exclude=None):
 m=poly(points)
 if exclude:m&=~poly(exclude)
 a=z.copy();dx,dy=delta;z[m]=0;y,x=np.where(m);assert np.all((x+dx>=0)&(x+dx<384)&(y+dy>=0)&(y+dy<384));z[y+dy,x+dx]=a[y,x]
 return {'polygon':points,'exclude_polygon':exclude,'translation':list(delta),'source_opaque_pixels':int((a[m]>0).sum()),'source_negative_pixels':int((a[m]==0).sum())}
whole={85:(2,0),89:(4,0),105:(1,0),134:(2,0),3:(1,0),4:(2,0)}
head={83:([(136,131),(160,131),(160,143),(156,149),(151,154),(142,154),(135,149)],(0,1),None),
89:([(145,131),(169,131),(169,142),(164,151),(158,153),(148,152),(142,146)],(0,1),None),
107:([(140,134),(163,134),(164,146),(161,151),(156,153),(142,152)],(0,-2),[(159,151),(164,151),(164,157),(159,157)]),
133:([(147,132),(172,132),(171,145),(165,152),(157,153),(147,149)],(0,-1),[(162,152),(169,152),(169,156),(162,156)]),
134:([(146,132),(170,132),(170,144),(165,151),(160,154),(149,151)],(1,-1),[(160,152),(167,152),(167,158),(160,158)]),
3:([(144,130),(168,130),(168,140),(165,145),(163,151),(159,152),(150,151),(144,148)],(0,-2),[(159,151),(165,151),(165,156),(159,156)]),
130:([(140,134),(165,134),(164,146),(159,153),(152,154),(142,151)],(0,-1),[(156,153),(163,153),(163,157),(156,157)])}
records=[]
for folder,refs in [('ground_second01',[83,85,87,89]),('ground_recovery01',[91,105,107,130]),('movement_returns01',[133,134,3,4])]:
 items={k:[]for k in('normal','black')}
 for n in refs:
  source=D/folder/'native'/f'b0_{n:03}_indices.png';a=np.array(Image.open(source));z=a.copy();ops=[]
  if not np.any(z[130:155,135:175]==15):
   q=iris[n][0];assert q['actual_cyan_pixels']>=10;x,y=q['cell'];z[y,x]=15;ops.append({'source_iris_cell':[x,y],'actual_cyan_source_pixels':q['actual_cyan_pixels'],'mapped_palette_index':15})
  if n==130:
   p=D/'recovery130_fix01/native/b0_130_indices.png';v=np.array(Image.open(p));points=[(140,154),(169,154),(173,160),(175,168),(166,172),(143,171),(140,166)];m=poly(points);z[m]=v[m];ops.append({'arm_repaint_source':rel(p),'source_sha256':sha(p.read_bytes()),'polygon':points,'outside_mask_preserved':True,'first_pass_head_body_kept':True})
  if n in whole:
   dx,dy=whole[n];z=np.roll(z,(dy,dx),(0,1));ops.append({'whole_translation':[dx,dy],'reason':'얼굴·몸통·양발의 공통 수평 편차 정합'})
  if n in head:
   points,delta,exclude=head[n];ops.append(move(z,points,delta,exclude))
  if n in(83,85,87):ops.append(move(z,[(134,176),(154,176),(154,187),(134,187)],(0,1)))
  if n==89:
   ops.append(move(z,[(136,176),(151,176),(151,187),(136,187)],(1,1)))
   ops.append(move(z,[(166,177),(182,177),(182,187),(166,187)],(-1,0)))
   ops.append(move(z,[(132,150),(149,150),(151,159),(146,162),(132,162)],(2,2)))
   ops.append(move(z,[(166,150),(178,151),(180,161),(167,161)],(0,2)))
  if n==91:
   ops.append(move(z,[(130,178),(145,178),(145,187),(130,187)],(-1,0)))
   ops.append(move(z,[(164,179),(179,179),(179,187),(164,187)],(-1,0)))
  if n==130:
   ops.append(move(z,[(133,177),(151,177),(151,187),(133,187)],(2,0)))
   ops.append(move(z,[(166,177),(183,177),(183,187),(166,187)],(1,0)))
  if n==133:
   ops.append(move(z,[(142,154),(153,154),(156,159),(152,163),(142,163)],(1,-1)))
   ops.append(move(z,[(171,152),(180,152),(181,163),(170,163)],(-3,-1)))
  if n==134:ops.append(move(z,[(171,145),(184,145),(184,156),(175,161),(170,156)],(0,-1)))
  p=O/f'b0_{n:03}_indices.png';Image.fromarray(z).save(p);old=render(arc,0,0,n)[0]
  records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'source_native':rel(source),'source_native_sha256':sha(source.read_bytes()),'generated_sha256':sha((D/folder/'generated.png').read_bytes()),'operations':ops,'output_sha256':sha(p.read_bytes()),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'old_body_or_head_override':False,'manually_invented_color':False})
  for form,words in [('normal',pal),('black',red)]:
   pic=rgba(z,words);pic.save(O/f'{form}_b0_{n:03}.png');items[form].extend([(f'{n} before',rgba(old,words)),(f'{n} source',rgba(a,words)),(f'{n} registered',pic)])
 for form,words in [('normal',pal),('black',red)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{folder}_{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'candidate_only':True,'source_arc_sha256':sha(arc),'records':records,'runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(O)
