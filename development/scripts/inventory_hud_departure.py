"""Read-only native HUD/Hunter departure comparison for the current accepted parent."""
import json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_riko_illustrations import read_sources
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import DiscReader,sha256
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.inventory_shibuki_ui import sheet
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

PARENT=ROOT/'out/ver_buki_riko/ui_colors_gangzi_20261027T093842860144Z'
PARENT_SHA='85e9fed94574d8c657646cef7a2ed7f947960c538bd1ab8a1edc1705b190e3a1'
D=ROOT/'work/ver_buki_riko/ui_hud_departure_v3'

def load():
    if digest(PARENT/'shibuki_riko.bin')!=PARENT_SHA:raise ValueError('Wrong parent build')
    if digest(ROOT/'MegaMan X4.bin')!='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b':raise ValueError('Wrong original BIN')
    sources=read_sources();records={r['name'].split(';')[0]:r for r,b in sources};original={r['name'].split(';')[0]:b for r,b in sources}
    with (PARENT/'shibuki_riko.bin').open('rb') as f:
        reader=DiscReader(f,(PARENT/'shibuki_riko.bin').stat().st_size);current={n:reader.read(r['lba'],r['size']) for n,r in records.items()}
    return records,original,current

def main():
    D.mkdir(exist_ok=True);out=D/'inventory';out.mkdir(exist_ok=True);records,original,current=load();rows=[]
    for suffix,hi in [('X',75776),('Z',81920)]:
        items=[];name=f'ST0D_0{suffix}.ARC'
        for tag,source in [('original',original),('before',current)]:
            raw=source[name];g=entry(raw,0x10102)[63488:hi];p=entry(raw,10);pal=struct.unpack_from('<16H',entry(source[f'COL0D_0{suffix}.ARC'],5),35*32)
            for n in range(aliased_composition(p,2,0)['bank_frame_count']):
                c=aliased_composition(p,2,n);px,sz,bb,_=compose_static(g,local_composition(c));label=f'{suffix}_{tag}_{n:02}';im=save_image(px,sz,pal,out/(label+'.png')).convert('RGBA');canvas=Image.new('RGBA',(180,180));canvas.alpha_composite(im,(90+bb[0],110+bb[1]));ImageDraw.Draw(canvas).line((0,158,179,158),fill=(100,100,100,255));items.append((label,canvas));rows.append({'label':label,'bounds':bb,'size':sz,'parts':len(c['parts']),'bbox':im.getbbox()})
        sheet(items,out/f'{suffix}_world_comparison.png',7 if suffix=='Z' else 6,(200,200))
    items=[];pal=struct.unpack('<16H',(ROOT/'work/ver_buki_riko/art_pilot/hud_mark_v1/hud_palette.bin').read_bytes())
    for name in ['PL00_U.ARC','PL01_U.ARC']:
        for tag,source in [('original',original),('before',current)]:
            for n in (69,77):
                raw=source[name];px,sz,bb,_=compose_static(entry(raw,0x10206),local_composition(aliased_composition(entry(raw,3),1,n)));im=save_image(px,sz,pal,out/f'hud_{name}_{tag}_{n}.png').convert('RGBA');items.append((f'{name} {tag} {n}',im.resize((sz[0]*4,sz[1]*4),Image.Resampling.NEAREST)))
    sheet(items,out/'hud_comparison.png',4,(240,360));(out/'metadata.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'output':str(out),'frames':len(rows),'stage_entries':records['ST0D_0X.ARC']['entries']}))

if __name__=='__main__':main()
