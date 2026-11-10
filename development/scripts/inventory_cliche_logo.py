"""Read-only logo inventory bound to the accepted integrated US build."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.prepare_riko_ui import entry
from scripts.inventory_shibuki_ui import background,sheet
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from src.psx_ui_render import render_static_rgba

D=ROOT/'work/ver_buki_riko/cliche_logo_v1'
PARENT=ROOT/'out/ver_buki_riko/loading_life_ladder_fix_20261028T002440936544Z'
PARENT_HASH='0d439f758c9c08987a04fff2d2b12209f8ca5ef2b3f2b0e2db5b318848cd1965'
SOURCE_HASH='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
REFERENCE_HASH='6118d22558f9ceb6853d8b315c0635e1f2fa19e73a07637984f01d81388491b2'

def load(all_files=False):
    if digest(PARENT/'shibuki_riko.bin')!=PARENT_HASH or digest(ROOT/'MegaMan X4.bin')!=SOURCE_HASH or digest(ROOT/'character/cliche/Logo.webp')!=REFERENCE_HASH:raise ValueError('Protected input differs')
    inv=json.loads((ROOT/'work/ver_buki_riko/art_pilot/illustrations_v1/archive_inventory.json').read_text())
    records={r['name'].split(';')[0]:r for r in inv if all_files or r['name'].startswith(('ST0E','ST0F','COL0E','COL0F','LOAD','MOJIPAT','SLUS'))}
    with (PARENT/'shibuki_riko.bin').open('rb') as f:
        reader=DiscReader(f,(PARENT/'shibuki_riko.bin').stat().st_size);files={n:reader.read(r['lba'],r['size']) for n,r in records.items()}
    return records,files

def indexed(raw):
    a=np.frombuffer(raw,np.uint8);v=np.empty(len(a)*2,np.uint8);v[::2]=a&15;v[1::2]=a>>4;return v.reshape(-1,256)

def main():
    records,files=load();out=D/'inventory';out.mkdir(exist_ok=False);items=[];data={}
    for n,b in files.items():(out/n).write_bytes(b)
    (out/'records.json').write_text(json.dumps(records,indent=2))
    for name in ('ST0E_U0.ARC','ST0E_U1.ARC','ST0F_UX.ARC','ST0F_UZ.ARC','ST0F_U1.ARC'):
        pal=entry(files['COL0E_U1.ARC' if name=='ST0E_U1.ARC' else 'COL0E_U0.ARC' if name=='ST0E_U0.ARC' else 'COL0F_U1.ARC' if name=='ST0F_U1.ARC' else 'COL0F_U0.ARC'],5)
        for s in range(len(entry(files[name],0))//512):
            im=background(files[name],pal,s);im.save(out/f'{name}_screen{s}.png');items.append((f'{name} s{s}',im))
    for i in range(0,len(items),20):sheet(items[i:i+20],out/f'backgrounds_{i//20}.png',5,(260,280))
    menu=files['MOJIPAT.ARC'];starts=struct.unpack_from('<4I',menu);pal=menu[starts[1]:starts[2]];g=entry(files['LOAD_U.ARC'],0x10008);items=[]
    for n in range(53):
        cp=aliased_composition(menu,2,n)
        pals={i:struct.unpack_from('<16H',pal,i*32) for i in range(4)}
        im,bb=render_static_rgba(g,cp,pals);im.save(out/f'load_frame_{n}.png');items.append((f'LOAD b2/f{n}',im));data[str(n)]={'size':im.size,'bounds':bb,'parts':cp}
    sheet(items,out/'loading_compositions.png',6,(240,150))
    # Static texture preview; title/intro graphics are still to be bound to draw records.
    for name,kind,palname in [('ST0E_U0.ARC',0x10002,'COL0E_U0.ARC'),('ST0F_UX.ARC',0x10102,'COL0F_U0.ARC')]:
        a=indexed(entry(files[name],kind));pal=entry(files[palname],5);items=[]
        Image.fromarray(a*17).save(out/f'{name}_texture_gray.png')
        for row in range(16):
            im=save_image(a.tobytes(),(256,a.shape[0]),struct.unpack_from('<16H',pal,row*32),out/f'{name}_texture_p{row}.png').convert('RGBA');items.append((f'{name} pal{row}',im))
        sheet(items,out/f'{name}_texture_palettes.png',8,(160,235))
    (out/'loading_frames.json').write_text(json.dumps(data,indent=2));print(out)

if __name__=='__main__':main()
