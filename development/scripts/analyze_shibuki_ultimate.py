"""Hash-bound, read-only Ultimate resource inventory and native previews."""
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.project import digest
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,bank_offsets,composition_frame,decode_stream
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from scripts.extract_zero import save_image

PARENT=ROOT/'out/ver_buki_riko/hud_departure_fix_20261027T100223972729Z'
PARENT_SHA='1ea0875f548846b140bfad4914fa52a0a3f10e75c459d4436b18030b1738d3d8'
SOURCE_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
D=ROOT/'work/ver_buki_riko/shibuki_art/ultimate_v1'

def load():
    if digest(PARENT/'shibuki_riko.bin')!=PARENT_SHA or digest(ROOT/'MegaMan X4.bin')!=SOURCE_SHA:raise ValueError('Wrong game input')
    inventory=json.loads((ROOT/'work/ver_buki_riko/art_pilot/illustrations_v1/archive_inventory.json').read_text())
    records={r['name'].split(';')[0]:r for r in inventory if r['name'].split(';')[0] in ('PL00_U.ARC','PL02_U.ARC')}
    result={}
    for label,path in [('original',ROOT/'MegaMan X4.bin'),('parent',PARENT/'shibuki_riko.bin')]:
        with path.open('rb') as f:
            reader=DiscReader(f,path.stat().st_size)
            result[label]={n:reader.read(r['lba'],r['size']) for n,r in records.items()}
    return records,result

def main():
    d=D/'analysis';d.mkdir(parents=True,exist_ok=True);records,arcs=load();rows={};images=[]
    for label,files in arcs.items():
        for name,arc in files.items():
            (d/f'{label}_{name}').write_bytes(arc)
            g,c,pal=map(lambda k:entry(arc,k),(2,3,9));bank=graphics_bank(g,0,allow_bank_aliases=True);frames=[]
            for fr in bank['frames']:
                n=fr['index'];raw=decode_stream(g,fr['offset'],fr['limit'],fr['tile_count']*128);layers=[];combined=Image.new('RGBA',(160,160))
                for bi in (0,8,5,7,6):
                    cp=composition_frame(c,bi,n)
                    try:v=canvas_from_parts(raw.data,fr['tile_count'],local_composition(cp))
                    except ValueError as exc:
                        layers.append({'bank':bi,'unrenderable_original_or_parent':str(exc),'parts':cp['parts']});continue
                    cluts=sorted({q['clut'] for q in cp['parts']});words=struct.unpack_from('<16H',pal,0 if bi==0 else 32)
                    layers.append({'bank':bi,'parts':len(cp['parts']),'tiles':sorted({q['tile'] for q in cp['parts']}),'cluts':cluts,'visible_pixels':int(np.count_nonzero(v))})
                    if n in (0,115,116,117,118,119,221,236):
                        im=save_image(v.tobytes(),(160,160),words,d/f'{label}_{name}_{n:03}_{bi}.png').convert('RGBA');combined.alpha_composite(im)
                        if n==0 and bi==0:images.append((f'{label} {name} base',im))
                if n==0:
                    combined.save(d/f'{label}_{name}_full_000.png');images.append((f'{label} {name} full',combined))
                frames.append({'frame':n,'offset':fr['offset'],'tiles':fr['tile_count'],'capacity':fr['limit']-fr['offset'],'encoded_bytes':raw.end-fr['offset'],'layers':layers})
            rows[label+'_'+name]={'sha256':sha256(arc),'size':len(arc),'entries':psx_arc(arc),'graphics_banks':bank_offsets(g,allow_aliases=True),'composition_banks':bank_offsets(c),'frame_count':len(frames),'frames':frames}
    sheet=Image.new('RGB',(4*230,2*280),'#283341');dr=ImageDraw.Draw(sheet)
    for i,(label,im) in enumerate(images):
        x,y=i%4*230,i//4*280;im=im.crop((48,48,112,112)).resize((224,224),Image.Resampling.NEAREST);sheet.paste(im,(x,y+35),im);dr.text((x+4,y+5),label,fill='white')
    sheet.save(d/'native_comparison.png')
    (d/'inventory.json').write_text(json.dumps(rows,indent=2));(d/'records.json').write_text(json.dumps(records,indent=2))
    print(json.dumps({'output':str(d),'archives':{k:{a:v[a] for a in ('sha256','size','frame_count','graphics_banks')} for k,v in rows.items()}}))

if __name__=='__main__':main()
