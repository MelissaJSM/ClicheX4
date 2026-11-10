"""Thicken native selection lettering; isolate mint death-orb resources."""
import argparse,json,shutil,struct
from pathlib import Path
import numpy as np
from PIL import Image
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_riko_illustrations import repack_one_bank
from scripts.inventory_riko_illustrations import read_sources
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_ui_atlas import tile_pixels
from src.psx_death_orbs import recolor_death_orbs,CONFIG


def labels(font):
    glyphs=[]
    for ch in 'RIKO':
        pixels=np.frombuffer(tile_pixels(font,'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'.index(ch)),dtype='uint8').reshape(16,16)
        im=Image.fromarray(np.uint8(pixels>=8)*255);im=im.crop(im.getbbox())
        im=im.resize((round(im.width*16/im.height),16),Image.Resampling.NEAREST)
        a=np.array(im)>0;bold=np.zeros((16,a.shape[1]+1),bool)
        bold[:,:-1]|=a;bold[:,1:]|=a;glyphs.append(bold)
    width=sum(a.shape[1] for a in glyphs)+3
    if width>60:raise ValueError('Native letter width exceeds name frame')
    mask=np.zeros((32,64),bool);x=(64-width)//2
    for a in glyphs:
        mask[7:23,x:x+a.shape[1]]=a;x+=a.shape[1]+1
    outline=np.zeros_like(mask);shadow=np.zeros_like(mask)
    for dy in (-1,0,1):
        for dx in (-1,0,1):outline|=np.roll(np.roll(mask,dy,0),dx,1)
    shadow[2:,1:]=outline[:-2,:-1]
    small=np.zeros(mask.shape,dtype='uint8');small[shadow]=2;small[outline]=1
    for y in range(32):small[y,mask[y]]=15 if y<15 else 14 if y<20 else 13
    # The large name uses its original independent row-4 palette.
    large=np.zeros((48,208),dtype='uint8');lm=np.zeros_like(large,dtype=bool)
    for j,a in enumerate(glyphs):
        doubled=np.repeat(np.repeat(a,2,0),2,1);x=26+j*52-doubled.shape[1]//2
        lm[6:38,x:x+doubled.shape[1]]=doubled
    border=np.zeros_like(lm)
    for dy in (-1,0,1):
        for dx in (-1,0,1):border|=np.roll(np.roll(lm,dy,0),dx,1)
    large[np.roll(np.roll(border,2,0),1,1)]=1;large[border]=1;large[lm]=2
    large[32:][lm[32:]]=4
    return small,large


def prepare(source,out):
    if out.exists():raise ValueError('Output already exists')
    shutil.copytree(source,out)
    recipe=json.loads((out/'recipe.json').read_text('utf8'))
    originals={r['name'].split(';')[0]:raw for r,raw in read_sources()}
    names=labels(entry(originals['LOAD_U.ARC'],0x10001))
    path=out/'ST0E_U1.ARC';raw=path.read_bytes();g=entry(raw,0x10102);p=entry(raw,0xa)
    targets={4:(names[0].tobytes(),(64,32)),7:(names[1].tobytes(),(208,48))}
    ng,np_,report=repack_one_bank(g[40960:90112],p,1,targets,{7:0})
    path.write_bytes(replace_entry(replace_entry(raw,0x10102,g[:40960]+ng+g[90112:]),0xa,np_))
    for n,arr,row in [(4,names[0],6),(7,names[1],4)]:
        pal=struct.unpack('<16H',entry(originals['COL0E_U1.ARC'],5)[row*32:(row+1)*32])
        save_image(arr.tobytes(),(arr.shape[1],arr.shape[0]),pal,out/f'name_{n}.png')
    path=out/'PL01_U.ARC';changed,orb_report=recolor_death_orbs(path.read_bytes());path.write_bytes(changed)
    config=json.loads(CONFIG.read_text('utf8'))
    for row in config['stage_palettes']:
        raw=originals[row['path'].split('/')[-1].split(';')[0]]
        palette=entry(raw,5)[96:128]
        from hashlib import sha256
        if sha256(palette).hexdigest()!=row['sha256']:raise ValueError('Stage orb palette mismatch')
    recipe['death_orbs']=orb_report
    recipe['checks']['selection_name_bold']=report
    for item in recipe['files']:item['sha256']=digest(out/item['file'])
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'output':str(out),'name_frames':report,'death_orbs':orb_report}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();prepare(a.source,a.output)
