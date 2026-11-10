from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rin_extension';O=D/'burst_variant185_01'
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
arc=(D/'prepared_priority_final_v2/PL01_U.ARC').read_bytes()
arrays={'idle147':render(arc,0,0,147)[0],'accepted182':render(arc,1,5,182)[0],'old185':render(arc,1,5,185)[0],'new185':np.array(Image.open(O/'native/b1_185_indices.png'))}
assert np.array_equal(arrays['old185'],render(arc,1,5,184)[0])
meta={}
for k,a in arrays.items():
 meta[k]={'bbox':rgba(a,struct.unpack_from('<16H',entry(arc,9))).getbbox(),'pixels':int((a>0).sum()),'foot_last_rows':{str(y):np.flatnonzero(a[y]).tolist() for y in (182,183,184)},'head':{str(y):np.flatnonzero(a[y,130:161]).tolist() for y in (150,154,158,162)}}
for name,off in [('normal',0),('black',13*32)]:
 pal=struct.unpack_from('<16H',entry(arc,9),off);sheet=Image.new('RGB',(4*560,640),'#25303d');dr=ImageDraw.Draw(sheet)
 for i,(k,a)in enumerate(arrays.items()):
  pic=rgba(a,pal).crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST);sheet.paste(pic,(i*560+24,60),pic)
  dr.text((i*560+24,10),k,fill='white');dr.line((i*560+24,60+32*8,i*560+535,60+32*8),fill='#4b5360');dr.line((i*560+24+32*8,60,i*560+24+32*8,571),fill='#4b5360');dr.text((i*560+24,595),str(meta[k]['bbox']),fill='white')
 sheet.save(O/f'{name}_sequence_comparison.png')
(O/'anchor_review.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
