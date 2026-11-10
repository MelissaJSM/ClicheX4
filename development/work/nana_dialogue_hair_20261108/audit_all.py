from pathlib import Path
import json,sys,struct
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_ui import native,D
from scripts.prepare_riko_ui import entry
from scripts.c01_audio_build import read_disc
from src.psx_ui_atlas import aliased_composition
from src.psx_static_effect import compose_static
b=ROOT/'work/armor_dialogue_20261108/ver_buki_riko/native_proposal'
target={n:np.array(Image.open(b/f'{n:02}.png')) for n in range(12)}
sources={0:'dialogue_generated.png',3:'dialogue_armor_generated.png'}
source_checks={str(n):int((target[n]!=native(D/name,(112,96),(112,96),(0,0))).sum()) for n,name in sources.items()}
print('Complete BR source art differences',source_checks)
board=Image.new('RGB',(6*448,430),(32,40,55));d=ImageDraw.Draw(board)
for i,n in enumerate([0,1,2,3,8,9]):
 im=Image.open(b/f'{n:02}.png').convert('RGBA').resize((448,384),0)
 board.paste(im,(448*i,24),im);d.text((448*i+5,5),str(n),fill='white')
 d.line((448*i,24+66*4,448*i+447,24+66*4),fill=(40,100,120))
board.save(H/'shibuki_all_join_audit.png')
checks={}
for mode in ['ver_buki_riko','ver_rin_nana']:
 p=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'))
 assets,_=read_disc((ROOT/p['cue']).with_suffix('.bin'),['ST00_00.ARC'])
 arc=assets['ST00_00.ARC'];g=entry(arc,0x10102)[198656:];parts=entry(arc,10);rows=[]
 for n in range(12):
  pp=parts if n<8 else struct.pack('<I',4)+parts[30588+1376:]
  co=aliased_composition(pp,11 if n<8 else 0,n if n<8 else {8:0,9:1,10:4,11:5}[n])
  data,size,bb,coverage=compose_static(g,co)
  expected=np.array(Image.open(ROOT/'work/armor_dialogue_20261108'/mode/'native_proposal'/f'{n:02}.png'))
  assert data==expected.tobytes() and size==(112,96)
  rows.append({'frame':n,'index_roundtrip':True,'size':size,'bounds':bb,'opaque_pixels':int((expected!=0).sum()),'opaque_pixels_outside_parts':sum(v!=0 and not cov for v,cov in zip(data,coverage))})
 checks[mode]={'parent_sha256':p['sha256'],'all12':rows}
checks['shibuki_original_source_art_difference_pixels']=source_checks
(H/'all_forms_audit.json').write_text(json.dumps(checks,indent=2)+'\n','utf8')
