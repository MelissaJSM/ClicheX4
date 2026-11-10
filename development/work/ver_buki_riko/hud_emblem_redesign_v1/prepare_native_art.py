"""Palette/size conversion of generated art; no drawing of substitute emblems."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import aliased_composition, local_composition

META = json.loads((D/'inventory/inventory.json').read_text())
COLORS = np.array(META['palette']['rgb'], dtype=np.int32)
RECORDS = {r['name'].split(';')[0]:r for r in json.loads((ROOT/'work/ver_buki_riko/art_pilot/illustrations_v1/archive_inventory.json').read_text())}
ROWS = json.loads((ROOT/'config/riko_hud_mark_us.json').read_text())['background_rows']

def read_arc(path, name):
    r=RECORDS[name]
    with path.open('rb') as f:
        return DiscReader(f,path.stat().st_size).read(r['lba'],r['size'])

def pixels(raw):
    px,sz,bb,_=compose_static(entry(raw,0x10206),local_composition(aliased_composition(entry(raw,3),1,69)))
    return np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]).copy(),bb

def rgba(a):
    out=np.zeros((*a.shape,4),np.uint8)
    out[:,:,:3]=COLORS[a]
    out[:,:,3]=np.where(a>0,255,0)
    return Image.fromarray(out)

def convert(name, size, filtering, alpha_cut, exposure=1.0):
    filename={'shibuki':'shibuki_torii.png','riko':'riko_sword.png','riko_v2':'riko_sword_v2.png'}[name]
    src=Image.open(D/'masters'/filename).convert('RGBA')
    src=src.crop(src.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox())
    native=src.convert('RGBa').resize(size,filtering).convert('RGBA')
    a=np.array(native)
    a[:,:,:3]=np.minimum(a[:,:,:3].astype(float)*exposure,255).astype(np.uint8)
    choices=np.array([3,4,10,11,12,13,14] if name=='shibuki' else [5,6,7,9,10,11,12,13,14])
    dist=((a[:,:,:3].astype(np.int32)[:,:,None,:]-COLORS[choices])**2).sum(3)
    indices=choices[dist.argmin(2)].astype(np.uint8)
    # Generated saturated violet is encoded into the existing purple ramp only.
    if name=='shibuki':
        r,g,b=a[:,:,0].astype(float),a[:,:,1].astype(float),a[:,:,2].astype(float)
        purple=(r>g*1.45)&(b>g*1.5)&(r>75)&(b>80)
        indices[purple]=np.where(r[purple]>150,3,4)
    indices[a[:,:,3]<alpha_cut]=0
    return indices

def main():
    out=D/'native_trials';out.mkdir(exist_ok=True)
    panel=Image.new('RGB',(900,1700),(30,33,44));draw=ImageDraw.Draw(panel)
    specs=[('shibuki',(19,12),Image.Resampling.BOX,96,1.0),('shibuki',(20,13),Image.Resampling.BOX,96,1.0),
           ('shibuki',(19,12),Image.Resampling.NEAREST,128,1.0),('riko',(15,13),Image.Resampling.BOX,96,1.0),
           ('riko',(17,13),Image.Resampling.BOX,96,1.0),('riko',(15,13),Image.Resampling.NEAREST,128,1.0),
           ('shibuki',(19,12),Image.Resampling.BOX,96,1.18),('riko',(17,13),Image.Resampling.BOX,96,1.18),
           ('riko',(17,13),Image.Resampling.BOX,96,1.35),
           ('riko_v2',(17,13),Image.Resampling.BOX,96,1.0),('riko_v2',(17,13),Image.Resampling.BOX,96,1.12),
           ('riko_v2',(17,13),Image.Resampling.NEAREST,128,1.0),
           ('riko_v2',(17,13),Image.Resampling.BOX,96,1.12),('riko_v2',(17,13),Image.Resampling.BOX,96,1.12),
           ('riko_v2',(17,13),Image.Resampling.BOX,96,1.12)]
    for k,(name,size,filt,cut,exposure) in enumerate(specs):
        file='PL00_U.ARC' if name=='shibuki' else 'PL01_U.ARC'
        original,bb=pixels(read_arc(ROOT/'MegaMan X4.bin',file))
        current,_=pixels(read_arc(ROOT/'out/ver_buki_riko/korean_20261028T060610973785Z/shibuki_riko.bin',file))
        clean=original.copy()
        for y,x1,x2 in ROWS:
            clean[y-17-bb[1],x1-24-bb[0]:x2-24-bb[0]+1]=14
        yy,xx=np.indices(clean.shape)
        interior=(yy+bb[1]>=26)&(yy+bb[1]<=38)&(xx+bb[0]>=-19)&(xx+bb[0]<=3)
        clean[interior&(clean>=1)&(clean<=9)]=14
        sx,sy=-19-bb[0],26-bb[1]
        base=clean[sy:sy+13,sx:sx+23].copy()
        art=convert(name,size,filt,cut,exposure)
        x=(23-size[0])//2;y=(13-size[1])//2
        offset_x=-(k-11) if k>=12 else 0
        x+=offset_x
        dst=base[y:y+size[1],x:x+size[0]]
        dst[art>0]=art[art>0]
        mask=original[sy:sy+13,sx:sx+23]>0
        base[~mask]=0
        im=Image.fromarray(base,mode='P');im.putpalette(COLORS.astype(np.uint8).reshape(-1).tolist()+[0]*720)
        im.save(out/f'{name}_{k}_indices.png')
        patched=current.copy();patched[sy:sy+13,sx:sx+23]=base
        rgba(patched).save(out/f'{name}_{k}_hud.png')
        px=(k%3)*300;py=(k//3)*340
        draw.text((px+8,py+5),f'{name} {k} gain={exposure} dx={offset_x}',fill='white')
        low=rgba(patched[-32:]);panel.paste(low.resize((288,192),Image.Resampling.NEAREST),(px+5,py+25),low.resize((288,192),Image.Resampling.NEAREST))
        icon=rgba(base).resize((230,130),Image.Resampling.NEAREST)
        panel.paste(icon,(px+25,py+205),icon)
    panel.save(out/'review.png')
    panel.crop((0,1360,900,1700)).save(out/'riko_alignment_review.png')
    print(out/'review.png')

if __name__=='__main__':main()
