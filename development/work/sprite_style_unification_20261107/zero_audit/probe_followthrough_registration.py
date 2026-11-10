"""후속 원화의 전신 평행이동만 따로 검토한다. 최종 등록/패킹이 아니다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import rgba,render
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';P=D/'followthrough01';O=P/'anchor_probe';O.mkdir(exist_ok=True)
arc=(D/'prepared_spin01/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
trans={'b1_146':(5,4),'b1_156':(1,5),'b1_158':(6,3),'b0_197':(2,4)}
items={k:[]for k in('normal','black')};rows=[]
for key,(dx,dy)in trans.items():
 old=np.array(Image.open(P/(key+'_before_indices.png')));a=np.array(Image.open(P/'native'/(key+'_indices.png')));new=np.roll(np.roll(a,dy,0),dx,1)
 Image.fromarray(new).save(O/(key+'_indices.png'))
 rows.append({'key':key,'translation_from_generic':[dx,dy],'old_floor':int(np.nonzero(old)[0].max()),'new_floor':int(np.nonzero(new)[0].max()),'purpose':'눈/머리 좌표를 먼저 맞춘 진단본. 하체/접점 미완료.'})
 for form,words in [('normal',pal),('black',black)]:
  items[form].extend([(key+' old',rgba(old,words)),(key+' generic',rgba(a,words)),(key+' eyes anchored',rgba(new,words))])
for form,words in [('normal',pal),('black',black)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/(form+'_comparison.png'),cols=3,scale=5)
(O/'report.json').write_text(json.dumps({'rows':rows,'candidate':False,'applied':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(O)
