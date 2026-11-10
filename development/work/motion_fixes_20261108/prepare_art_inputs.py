from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from common import board
rin=W/'ver_rin_nana';im=Image.open(rin/'zero_046.png').convert('RGBA');im.crop((120,132,216,196)).resize((768,512),Image.Resampling.NEAREST).save(rin/'rin_dash_edit.png')
br=W/'ver_buki_riko';a=Archive((br/'PL01_U.ARC').read_bytes());normal=a.words[:16].copy();wanted=normal.copy()
changes={2:(21,22,24),3:(27,28,30),6:(28,29,30),7:(3,4,6),10:(31,31,31),12:(5,6,8),15:(10,11,13)}
for i,(r,g,b)in changes.items():wanted[i]=(int(normal[i])&0x8000)|r|(g<<5)|(b<<10)
black=a.words.copy();black[:16]=wanted
items=[]
for n in(147,7,20,46,68,229):
 px,_=a.layer(n);old=a.words.copy();items.append((f'normal {n}',a.rgba(px)));a.words=black;items.append((f'coat black / inner white {n}',a.rgba(px)));a.words=old
board(items,br/'riko_inverted_trial.png',4)
(br/'riko_inverted_palette.bin').write_bytes(struct.pack('<16H',*wanted))
(br/'riko_inverted_palette.json').write_text(json.dumps({'normal':list(map(int,normal)),'black':list(map(int,wanted)),'changed_indices':list(changes),'skin_preserved':[9,11,13],'green_hair_midtones_preserved':[4,8,14],'shared_highlights':'index10 mint becomes white; white highlights12/15 also shared with footwear'},indent=2)+'\n','utf8')
