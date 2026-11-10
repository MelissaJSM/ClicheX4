"""Keep connected authored anatomy; only shared horizontal registration and 130 arm edit."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'after141_registered_v2';assert not O.exists();O.mkdir()
arc=(D/'prepared_ground_wall_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
assert sha(arc)=='247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
iris={q['ref']:q['votes']for q in json.loads((D/'after141_contact_review/iris.json').read_text('utf8'))};whole={85:(2,0),89:(4,0),105:(1,0),134:(2,0),3:(1,0),4:(2,0)}
records=[]
for folder,refs in [('ground_second01',[83,85,87,89]),('ground_recovery01',[91,105,107,130]),('movement_returns01',[133,134,3,4])]:
 items={k:[]for k in('normal','black')}
 for n in refs:
  source=D/folder/'native'/f'b0_{n:03}_indices.png';a=np.array(Image.open(source));z=a.copy();ops=[]
  if not np.any(z[130:155,135:175]==15):
   q=iris[n][0];assert q['actual_cyan_pixels']>=10;x,y=q['cell'];z[y,x]=15;ops.append({'source_iris_cell':[x,y],'actual_cyan_source_pixels':q['actual_cyan_pixels'],'mapped_palette_index':15})
  if n==130:
   p=D/'recovery130_fix01/native/b0_130_indices.png';v=np.array(Image.open(p));points=[(140,154),(169,154),(173,160),(175,168),(166,172),(143,171),(140,166)];mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(points,fill=1);m=np.array(mask,bool);z[m]=v[m];ops.append({'arm_repaint_source':rel(p),'source_sha256':sha(p.read_bytes()),'polygon':points,'outside_mask_preserved':True,'first_pass_head_body_kept':True})
  if n in whole:
   dx,dy=whole[n];z=np.roll(z,(dy,dx),(0,1));ops.append({'whole_translation':[dx,dy],'reason':'얼굴·몸통·양발의 공통 수평 편차 정합. 부위 내부 연결은 바꾸지 않는다.'})
  p=O/f'b0_{n:03}_indices.png';Image.fromarray(z).save(p);old=render(arc,0,0,n)[0]
  records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'source_native':rel(source),'source_native_sha256':sha(source.read_bytes()),'generated_sha256':sha((D/folder/'generated.png').read_bytes()),'operations':ops,'output_sha256':sha(p.read_bytes()),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'old_body_or_head_override':False,'manually_invented_color':False})
  for form,words in [('normal',pal),('black',red)]:
   pic=rgba(z,words);pic.save(O/f'{form}_b0_{n:03}.png');items[form].extend([(f'{n} before',rgba(old,words)),(f'{n} source',rgba(a,words)),(f'{n} registered',pic)])
 for form,words in [('normal',pal),('black',red)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{folder}_{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'candidate_only':True,'source_arc_sha256':sha(arc),'records':records,'runtime_verified':False,'user_accepted':False,'rejected_prior':'after141_registered_v1: 부위별 1픽셀 이동이 리본·발목·목 연결을 훼손하여 미채택.','remaining_contact_review':'새 눈 높이3/107 및 앞발83/85/87의1~2픽셀 차이는 원화 전체 체형·동작 연속성으로 검토해야 하며, 외곽 극값을 강제하지 않는다.'},ensure_ascii=False,indent=2)+'\n','utf8');print(O)
