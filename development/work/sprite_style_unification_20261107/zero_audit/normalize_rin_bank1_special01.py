"""Fixed-grid palette registration; no bounding-box resizing or old-art overlay."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension/bank1_special01';O=D/'native_fixed';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();info=json.loads((D/'inputs.json').read_text('utf8'));src=ROOT/info['actual_input_arc'];assert sha(src)==info['archive_sha256'];arc=src.read_bytes()
im=Image.open(D/'generated.png').convert('RGBA');assert sha(D/'generated.png')=='63045dd29f76bbed0f8b5e00c72d0cdfac45430dbce50dc0529f18b12c046da7'and im.size==(1254,1254)and im.getchannel('A').getextrema()==(0,255)
pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32);colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);rows=[];items={k:[]for k in('normal','black')}
for f in info['frames']:
 x,y=f['cell'];cell=im.crop((x*627,y*627,(x+1)*627,(y+1)*627));v=quantize(cell,colors,96/627);assert v.shape==(96,96)
 a=np.zeros((384,384),np.uint8);a[104:200,112:208]=v;old=render(arc,1,5,f['ref'])[0];p=O/(f['key']+'_indices.png');Image.fromarray(a).save(p)
 for name,words in [('normal',pal),('black',black)]:items[name].extend([(f['key']+' old',rgba(old,words)),(f['key']+' fixed native',rgba(a,words))])
 rows.append({**f,'new_bbox':rgba(a,pal).getbbox(),'old_floor':int(np.nonzero(old)[0].max()),'new_floor':int(np.nonzero(a)[0].max()),'old_cyan':np.argwhere(old==15)[:,::-1].tolist(),'new_cyan':np.argwhere(a==15)[:,::-1].tolist(),'components':[len(g)for g in connected_groups(a>0)],'output_sha256':sha(p),'translation':[0,0]})
for name,words in [('normal',pal),('black',black)]:page(items[name],rgba(render(arc,0,0,147)[0],words),O/(name+'_comparison.png'),cols=2,scale=5)
(O/'registration.json').write_text(json.dumps({'source_art_sha256':sha(D/'generated.png'),'actual_size':im.size,'fixed_cell':[627,627],'target_cell':[96,96],'old_art_override':False,'game_changed':False,'records':rows},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
