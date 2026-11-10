"""Collect the locked Shibuki PL00 hover poses without changing artwork."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page,metrics
sha=lambda b:hashlib.sha256(b).hexdigest()
H=W/'shibuki_audit';D=W/'root_shibuki_hover'
p=H/'prepared_nova_strike_base01/PL00_U.ARC'
assert sha(p.read_bytes())=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
assert not D.exists();D.mkdir();a=Archive(p.read_bytes());cases=[]
for form,mask in(('base',0),('base_legs',8),('fourth',15)):
    for start in(221,225,229):
        ns=range(start,min(start+4,231));ims=[]
        for n in ns:
            im=a.composite(n,mask)[0];ims.append((f'{form} {n} mask{mask}',im));cases.append({'form':form,'mask':mask,'ref':n,'rgba_sha256':sha(im.tobytes()),'metrics':metrics(im)})
        page(ims,a.composite(0,mask)[0],D/f'current_{form}_{start}.png',cols=2,scale=4)
# Two pose rows, costume columns. Constant world window, origin and integer size.
crop=(112,112,208,208);target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size)
for row,n in enumerate((221,223)):
    for col,mask in enumerate((0,15)):
        at=(768*col,768*row)
        target.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),at)
        style.alpha_composite(a.composite(0 if row==0 else 45,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),at)
target.save(D/'art01_inputs.png');style.save(D/'style_inputs.png')
report={'read_only':True,'input':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())},'cases':cases,'first_page':{'refs':[221,223],'columns':['base','fourth'],'style_refs':[0,45],'crop':list(crop),'cell_native':[96,96],'origin_in_cell':[48,48],'page':[1536,1536]},'limits':['基本mask0は物理保存用で実ホバーは脚パーツを要する。base_legs8とfourth15も別途比較する。','NanaやPL02の下半身所有規則をPL00に転用しない。','新原画なし、実機検証なし。']}
(D/'input_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'root':D.relative_to(ROOT).as_posix(),'parent':report['input']['sha256'],'cases':len(cases),'plates':9}))
