"""위치 변화가 큰 생성 원화를 발 자동맞춤 없이 고정 셀에서 진단한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'ladder_dash01';O=A/'native_fixed';assert not O.exists();O.mkdir()
info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32)
assert hashlib.sha256((A/'generated.png').read_bytes()).hexdigest()=='8b0421d987948cee062ceac6f545db0161647561f62d9978317859fb44b0b8cf'
im=Image.open(A/'generated.png').convert('RGBA');assert im.width==im.height;cw=im.width/2;scale=192/im.width;colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
def iris(a):
 ys,xs=np.nonzero(a);y0=int(ys.min());yy,xx=np.where((a==15)&(np.indices(a.shape)[0]<y0+22));return None if len(xx)==0 else [float(xx.mean()),float(yy.mean())]
items={k:[]for k in('normal','black')};rows=[]
for f in info['frames']:
 key=f['key'];x,y=f['cell'];v=quantize(im.crop((round(x*cw),round(y*cw),round((x+1)*cw),round((y+1)*cw))),colors,scale);assert v.shape==(96,96);z=np.zeros((384,384),np.uint8);z[104:200,112:208]=v;Image.fromarray(z).save(O/(key+'_indices.png'));old=render(arc,0,0,f['ref'])[0]
 rows.append({'key':key,'ref':f['ref'],'old_bbox':rgba(old,pal).getbbox(),'new_bbox':rgba(z,pal).getbbox(),'old_eye':iris(old),'new_eye':iris(z),'old_floor':int(np.nonzero(old)[0].max()),'new_floor':int(np.nonzero(z)[0].max()),'translation':[0,0],'output_sha256':hashlib.sha256((O/(key+'_indices.png')).read_bytes()).hexdigest()})
 for form,words in [('normal',pal),('black',black)]:items[form].extend([(key+' old',rgba(old,words)),(key+' fixed grid',rgba(z,words))])
for form,words in [('normal',pal),('black',black)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/(form+'_comparison.png'),cols=2,scale=5)
(O/'registration.json').write_text(json.dumps({'source_art_sha256':hashlib.sha256((A/'generated.png').read_bytes()).hexdigest(),'scale':scale,'fixed_grid':True,'records':rows,'applied':False},indent=2)+'\n','utf8');print(json.dumps(rows))
