"""Native asset inventory for the approved UI corrections and GangZi capsule."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_riko_illustrations import read_sources
from scripts.inventory_shibuki_ui import sheet
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

PARENT=ROOT/'out/ver_buki_riko/shibuki_ui_dash_fix_20261027T060318663516Z'
PARENT_SHA='9fd5f0bfa42735b071e4a719c265868583ab224092575715002a7477202de03c'
D=ROOT/'work/ver_buki_riko/ui_revision_v2'

def load():
    sources=read_sources();records={r['name'].split(';')[0]:r for r,b in sources};original={r['name'].split(';')[0]:b for r,b in sources}
    if digest(PARENT/'shibuki_riko.bin')!=PARENT_SHA:raise ValueError('Parent BIN changed')
    if digest(ROOT/'MegaMan X4.bin')!='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b':raise ValueError('Original BIN changed')
    with (PARENT/'shibuki_riko.bin').open('rb') as f:
        reader=DiscReader(f,(PARENT/'shibuki_riko.bin').stat().st_size)
        current={n:reader.read(r['lba'],r['size']) for n,r in records.items()}
    return records,original,current

def main():
    D.mkdir(exist_ok=True);out=D/'inventory';out.mkdir(exist_ok=True);records,original,current=load();meta=[];items=[]
    gray=[0]+[0x8000|(i*2)|(i*2<<5)|(i*2<<10) for i in range(1,16)]
    def render(g,p,b,n,pal,label):
        c=aliased_composition(p,b,n);px,sz,bb,_=compose_static(g,local_composition(c))
        im=save_image(px,sz,pal,out/(label+'.png')).convert('RGBA');meta.append({'label':label,'bank':b,'frame':n,'size':sz,'bounds':bb,'opaque_bbox':im.getbbox(),'parts':len(c['parts']),'cluts':sorted({r['clut'] for r in c['parts']})})
        return im
    # All static player banks, including the capsule/Dr. Light assets.
    for name in ['PL00_U.ARC','PL01_U.ARC']:
        raw=current[name];p=entry(raw,3);g=entry(raw,0x10206)
        for b in range(struct.unpack_from('<I',p)[0]//4):
            if b in ([0,5,6,7,8] if name=='PL00_U.ARC' else [0,5]):continue
            for n in range(aliased_composition(p,b,0)['bank_frame_count']):
                c=aliased_composition(p,b,n)
                try:px,sz,bb,_=compose_static(g,local_composition(c))
                except ValueError:continue
                if sz[0]<40 or sz[1]<40:continue
                label=f'{name}_b{b}_n{n}';im=render(g,p,b,n,gray,label);items.append((label,im))
    for i in range(0,len(items),30):sheet(items[i:i+30],out/f'large_static_{i//30}.png',6,(180,170))
    # Actual world-space HQ placement, without thumbnail autoscaling.
    items=[]
    for tag,source in [('before',current),('original',original)]:
        raw=source['ST0D_0X.ARC'];g=entry(raw,0x10102)[63488:75776];p=entry(raw,10);pal=struct.unpack_from('<16H',entry(source['COL0D_0X.ARC'],5),35*32)
        for n in range(12):
            label=f'hq_{tag}_{n:02}';im=render(g,p,2,n,pal,label);bb=meta[-1]['bounds'];canvas=Image.new('RGBA',(160,160));canvas.alpha_composite(im,(80+bb[0],115+bb[1]));items.append((label,canvas))
    sheet(items,out/'hq_world_positions.png',6,(200,200))
    items=[]
    for name in ['PL00_U.ARC','PL01_U.ARC']:
        for tag,source in [('before',current),('original',original)]:
            raw=source[name];g=entry(raw,0x10007)[96*128:];p=struct.pack('<I',4)+entry(raw,0x12);pal=struct.unpack_from('<16H',entry(raw,0x11),10*32)
            im=render(g,p,0,10,pal,f'pause_{name}_{tag}');items.append((f'{name} {tag}',im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)))
    sheet(items,out/'pause_alignment.png',4,(220,300))
    (out/'metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    trails={}
    for n,raw in original.items():
        if n.startswith('COL'):
            pal=entry(raw,5);trails[n]=[pal[r*32:(r+1)*32].hex() for r in range(10,16)]
    (out/'trail_rows.json').write_text(json.dumps(trails,indent=2),encoding='utf8')
    print(json.dumps({'output':str(out),'large_frames':len(meta),'light_reference_sha256':digest(ROOT/'character/dr_light/light.webp')}))
if __name__=='__main__':main()
