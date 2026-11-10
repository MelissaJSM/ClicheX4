"""Read-only inventory of loading labels, life pickups and ladder transitions."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_ui_atlas import local_composition,aliased_composition
from src.psx_static_effect import compose_static
from src.psx_sprite_batch import canvas_from_parts
from scripts.extract_zero import save_image

D=ROOT/'work/ver_buki_riko/loading_life_ladder_v1'
PARENT=ROOT/'out/ver_buki_riko/shibuki_capsule_nova_fix_20261027T232250486027Z'
PARENT_HASH='e162470a826206c6529d1bea085b4b78a2615cfb413353da5c218e6aa4e39896'
SOURCE_HASH='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'

def load():
    game=PARENT/'shibuki_riko.bin'
    if digest(game)!=PARENT_HASH:raise ValueError('Unexpected parent')
    inv=json.loads((ROOT/'work/ver_buki_riko/art_pilot/illustrations_v1/archive_inventory.json').read_text())
    names={'PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','LOAD_U.ARC','MOJIPAT.ARC','FONT8X8.ARC','SLUS_005.61'}
    records={r['name'].split(';')[0]:r for r in inv if r['name'].split(';')[0] in names}
    with game.open('rb') as stream:
        reader=DiscReader(stream,game.stat().st_size)
        files={n:reader.read(r['lba'],r['size']) for n,r in records.items()}
    return records,files

def main():
    out=D/'inventory';out.mkdir(parents=True,exist_ok=False);records,files=load()
    (out/'records.json').write_text(json.dumps(records,indent=2))
    for n,b in files.items():(out/n).write_bytes(b)
    pictures=[];frames=[]
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        arc=files[name];parts=entry(arc,3);texture=entry(arc,0x10206);pal=entry(arc,9)
        for n in range(89,99):
            c=composition_frame(parts,3,n);px,size,bb,_=compose_static(texture,local_composition(c))
            words=struct.unpack_from('<16H',pal,11*32)
            im=save_image(px,size,words,out/f'{name}_pickup_{n}.png').convert('RGBA')
            pictures.append((f'{name} b3 f{n}',im.resize((size[0]*4,size[1]*4),Image.Resampling.NEAREST)))
            frames.append({'file':name,'bank':3,'frame':n,'composition':c,'bounds':bb,'size':size})
    sheet=Image.new('RGB',(5*190,6*125),'#283442');dr=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(pictures):
        x,y=i%5*190,i//5*125;sheet.paste(im,(x+8,y+20),im);dr.text((x+3,y+3),name,fill='white')
    sheet.save(out/'pickups.png');pictures=[]
    for name in ('PL00_U.ARC','PL02_U.ARC'):
        arc=files[name];g,c,pal=[entry(arc,k) for k in (2,3,9)];bank=graphics_bank(g,0,allow_bank_aliases=True)
        for n in (1,151,152,153,154,155,183):
            f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            result=Image.new('RGBA',(160,160));layers=[]
            for bi in (0,8,5,7,6):
                cp=composition_frame(c,bi,n);v=canvas_from_parts(raw,f['tile_count'],local_composition(cp))
                words=struct.unpack_from('<16H',pal,(0 if bi==0 else 1)*32)
                im=save_image(v.tobytes(),(160,160),words,out/f'{name}_{n}_{bi}.png').convert('RGBA');result.alpha_composite(im)
                layers.append({'bank':bi,'opaque':int(np.count_nonzero(v)),'parts':cp})
            result.save(out/f'{name}_full_{n}.png');pictures.append((f'{name} f{n}',result.crop((48,40,120,120)).resize((216,240),Image.Resampling.NEAREST)))
            frames.append({'file':name,'frame':n,'layers':layers})
    sheet=Image.new('RGB',(7*220,2*270),'#283442');dr=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(pictures):
        x,y=i%7*220,i//7*270;sheet.paste(im,(x,y+25),im);dr.text((x+3,y+3),name,fill='white')
    sheet.save(out/'ladder.png')
    for e in psx_arc(files['LOAD_U.ARC']):
        b=files['LOAD_U.ARC'][e['offset']:e['offset']+e['size']];a=np.frombuffer(b,np.uint8);px=np.empty(len(a)*2,np.uint8);px[::2]=a&15;px[1::2]=a>>4
        Image.fromarray(px.reshape(-1,256)*17).resize((512,len(px)//128),Image.Resampling.NEAREST).save(out/f'load_{e["type"]}.png')
    (out/'frames.json').write_text(json.dumps(frames,indent=2))
    print(out)

if __name__=='__main__':main()
