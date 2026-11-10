"""Read-only raster-text inventory of the accepted game, not original graphics."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import load,D
from scripts.prepare_riko_ui import entry
from scripts.inventory_cliche_logo import indexed
from scripts.inventory_shibuki_ui import sheet
from scripts.prepare_ui_revision import pause_background
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

def grey(px,size):
    a=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);out=np.zeros((size[1],size[0],4),np.uint8)
    out[:,:,:3]=(a*17)[:,:,None];out[:,:,3]=np.where(a,255,0);return Image.fromarray(out)

def main():
    rr,files=load();out=D/'ui_inventory';out.mkdir(exist_ok=False);metadata={}
    names=('ST0E_U0.ARC','ST0E_U1.ARC','ST0F_UX.ARC','ST0F_UZ.ARC','ST0F_U1.ARC','COL0E_U0.ARC','COL0E_U1.ARC','COL0F_U0.ARC','COL0F_U1.ARC')
    for name in names:(out/name).write_bytes(files[name])
    menu=files['MOJIPAT.ARC'];texture=entry(files['LOAD_U.ARC'],0x10008);items=[]
    for n in range(aliased_composition(menu,2,0)['bank_frame_count']):
        c=aliased_composition(menu,2,n);px,size,bb,_=compose_static(texture,local_composition(c));im=grey(px,size)
        im.save(out/f'menu_{n:02d}.png');items.append((f'MENU {n}',im));metadata[f'menu_{n}']={'size':size,'bounds':bb,'parts':len(c['parts'])}
    for start in range(0,len(items),24):sheet(items[start:start+24],out/f'menu_sheet_{start//24}.png',4,(270,110))
    for name in ('PL00_U.ARC','PL01_U.ARC','LOAD_U.ARC'):
        raw=files[name]
        Image.fromarray(indexed(entry(raw,0x10007))*17).resize((768,768),Image.Resampling.NEAREST).save(out/f'{name}_menu_texture.png')
        if name.startswith('PL'):pause_background(raw).resize((960,720),Image.Resampling.NEAREST).save(out/f'{name}_pause.png')
    for name,kind in [('ST0E_U0.ARC',0x10002),('ST0E_U1.ARC',0x10102),('ST0F_UX.ARC',0x10102),('ST0F_U1.ARC',0x10102)]:
        a=indexed(entry(files[name],kind));Image.fromarray(a*17).save(out/f'{name}_texture.png')
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2));print(out)

if __name__=='__main__':main()
