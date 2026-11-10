"""뇌신격 마지막 회복 단독 원화 고정96×96 등록."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension/bank1_recovery128';O=D/'native_fixed';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();info=json.loads((D/'inputs.json').read_text('utf8'));src=ROOT/info['actual_input_arc'];assert sha(src)==info['archive_sha256'];arc=src.read_bytes()
im=Image.open(D/'generated.png').convert('RGBA');assert sha(D/'generated.png')=='7300247eb1281aaaaf71328c42043ab557ac5bc5040b3c6c7234a50ba21c1a28'and im.size==(1254,1254)and im.getchannel('A').getextrema()==(0,255)
pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32);colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);v=quantize(im,colors,96/1254);assert v.shape==(96,96)
a=np.zeros((384,384),np.uint8);a[104:200,112:208]=v;old=render(arc,1,5,128)[0];p=O/'b1_128_indices.png';Image.fromarray(a).save(p)
for name,words in [('normal',pal),('black',black)]:page([('128 old',rgba(old,words)),('128 fixed native',rgba(a,words))],rgba(render(arc,0,0,147)[0],words),O/(name+'_comparison.png'),cols=2,scale=6)
j={'source_art_sha256':sha(D/'generated.png'),'source_arc_sha256':sha(src),'actual_size':im.size,'fixed_canvas':[1254,1254],'target_canvas':[96,96],'old_art_override':False,'game_changed':False,'old_bbox':rgba(old,pal).getbbox(),'new_bbox':rgba(a,pal).getbbox(),'old_floor':int(np.nonzero(old)[0].max()),'new_floor':int(np.nonzero(a)[0].max()),'old_cyan':np.argwhere(old==15)[:,::-1].tolist(),'new_cyan':np.argwhere(a==15)[:,::-1].tolist(),'components':[len(g)for g in connected_groups(a>0)],'output_sha256':sha(p),'translation':[0,0]}
(O/'registration.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j))
