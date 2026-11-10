"""고정 등록 원화의 새 앞팔 두 곳만 원 손 접점으로 정합한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'bank1_special01';O=D/'bank1_special_registered_v1'
assert not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();assert sha(arc)==info['archive_sha256']
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
ops={91:[],93:[],101:[([(139,153),(148,152),(153,154),(153,158),(148,164),(139,164)],(-1,1))],105:[([(134,149),(145,149),(152,150),(155,151),(155,155),(151,157),(147,158),(144,160),(134,160)],(0,2))]}
records=[];items={k:[]for k in('normal','black')}
for n,operations in ops.items():
 src=A/'anchor_probe_v1'/f'b1_{n:03}_indices.png';a=np.array(Image.open(src));z=a.copy();history=[]
 for poly,(dx,dy)in operations:
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(poly,fill=1);m=np.array(mask,bool);yy,xx=np.where(m);z[m]=0;z[yy+dy,xx+dx]=a[yy,xx]
  union=m|np.roll(m,(dy,dx),(0,1));assert np.array_equal(z[~union],a[~union]);history.append({'polygon':poly,'translation':[dx,dy],'negative_space_moved_with_source':True,'changed_pixels':int(np.count_nonzero(z!=a))})
 out=O/f'b1_{n:03}_indices.png';Image.fromarray(z).save(out)
 old=render(arc,1,5,n)[0]
 for name,words in [('normal',pal),('black',black)]:items[name].extend([(f'{n} old',rgba(old,words)),(f'{n} fixed source',rgba(a,words)),(f'{n} contacts',rgba(z,words))])
 records.append({'key':f'b1_{n:03}','bank':1,'ref':n,'source_native':str(src.relative_to(ROOT)),'source_native_sha256':sha(src.read_bytes()),'operations':history,'output_sha256':sha(out.read_bytes()),'old_head_override':False,'manually_invented_colors':False})
for name,words in [('normal',pal),('black',black)]:page(items[name],rgba(render(arc,0,0,147)[0],words),O/(name+'_comparison.png'),cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':sha(arc),'source_generated_sha256':sha((A/'generated.png').read_bytes()),'records':records,'scope':'지상 준비·회복4키에서 정확 같은101/103·105/107만 공유. 새 앞팔101은(-1,+1),105는(0,+2)로 원손 접점을 정합한다. 기존 머리나 옷을 덮지 않으며 손 외부 새 원화는 그대로다.','runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(O)
