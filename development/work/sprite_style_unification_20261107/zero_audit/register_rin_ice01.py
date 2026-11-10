"""빙열참 새 원화의 손·발과 cyan 눈 표본을 네이티브에 등록한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'ice_detail01';O=D/'ice_registered_v1'
assert not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
arc=(D/'prepared_saber_followup05_v2/PL01_U.ARC').read_bytes()
assert sha(arc)=='0f6665a4cca930edf7e90351b8a8ac044b23326b19836eaa52d473b1b2390941'
assert sha((A/'generated.png').read_bytes())=='e26e32c9dddb8c37088e23ef6f6de271ad08657846643e47d09927e38c854b73'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
whole={133:(0,0),135:(2,0),138:(0,0),139:(2,0)}
parts={133:[([(151,128),(158,128),(160,132),(159,134),(154,134),(151,131)],(0,1))],
       135:[([(154,116),(178,116),(178,124),(161,134),(155,132),(153,129)],(0,1))],
       138:[([(175,174),(189,175),(190,184),(178,185),(179,179)],(-1,0))],139:[]}
reg=json.loads((A/'native/registration.json').read_text('utf8'));inf=json.loads((A/'inputs.json').read_text('utf8'))
gen=np.array(Image.open(A/'generated.png').convert('RGBA'));records=[];items={k:[]for k in('normal','black')}
for f,r in zip(inf['frames'],reg['records']):
 n=f['ref'];source=A/'native'/f'b1_{n:03}_indices.png';a=np.array(Image.open(source));z=a.copy();ops=[]
 # Restore a genuinely present cyan iris, lost by majority quantization, before registration.
 if n in (133,135):
  x,y=f['cell'];h,w=gen.shape[:2];s=gen[y*h//2:(y+1)*h//2,x*w//2:(x+1)*w//2]
  m=(s[:,:,0]<s[:,:,1]*.6)&(s[:,:,1]>90)&(s[:,:,1]>s[:,:,2]*.6)&(s[:,:,1]<s[:,:,2]*1.15)&(s[:,:,3]>=128)
  cells={}
  for sy,sx in zip(*np.where(m)):
   p=(112+int(sx*96/s.shape[1]),96+r['translate'][1]+int(sy*96/s.shape[0]));cells[p]=cells.get(p,0)+1
  (ix,iy),samples=max(cells.items(),key=lambda p:p[1]);assert samples>=15 and z[iy,ix]>0
  z[iy,ix]=15;ops.append({'source_iris_cell':[ix,iy],'actual_cyan_source_pixels':samples,'source_palette_index':15})
 dx,dy=whole[n];z=np.roll(z,(dy,dx),(0,1));ops.append({'whole_translation':[dx,dy]})
 for points,(mx,my)in parts[n]:
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(points,fill=1);m=np.array(mask,bool);v=z.copy();ys,xs=np.where(m);z[m]=0;z[ys+my,xs+mx]=v[ys,xs]
  ops.append({'polygon':points,'translation':[mx,my],'source_negative_cells_preserved':True,'changed_pixels':int((v!=z).sum())})
 p=O/f'b1_{n:03}_indices.png';Image.fromarray(z).save(p);old=render(arc,1,5,n)[0]
 records.append({'key':f'b1_{n:03}','bank':1,'ref':n,'source_native':rel(source),'source_native_sha256':sha(source.read_bytes()),'generated_sha256':sha((A/'generated.png').read_bytes()),'operations':ops,'output_sha256':sha(p.read_bytes()),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'old_head_or_body_override':False,'manually_invented_color':False})
 for form,words in [('normal',pal),('black',red)]:
  pic=rgba(z,words);pic.save(O/f'{form}_b1_{n:03}.png');items[form].extend([(f'{n} before',rgba(old,words)),(f'{n} source',rgba(a,words)),(f'{n} contacts',pic)])
for form,words in [('normal',pal),('black',red)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':sha(arc),'records':records,'candidate_only':True,'runtime_verified':False,'user_accepted':False,'scope':'빙열참133/135/138/139 새 원화.135/139 전신x+2; 올린 장갑/도구의 새 원화1px와138 뒤 구두1px 정합.133/135 cyan 눈은 실제 생성 표본 복구. 이전 머리·의상 덮기와 임의 색 채움 없음.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(O)
