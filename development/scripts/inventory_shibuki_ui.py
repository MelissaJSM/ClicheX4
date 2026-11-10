"""Read-only native UI inventory and reference rendering for Shibuki."""
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_riko_illustrations import read_sources
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import DiscReader,sha256
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static

D=ROOT/'work/ver_buki_riko/shibuki_ui_v1'
PARENT=ROOT/'out/ver_buki_riko/shibuki_fourth_hover_alignment_20261027T033818587949Z'

def load():
    sources=read_sources();records={r['name'].split(';')[0]:r for r,b in sources};original={r['name'].split(';')[0]:b for r,b in sources}
    m=json.loads((PARENT/'manifest.json').read_text('utf8'));game=PARENT/'shibuki_riko.bin'
    if digest(game)!=m['modified_bin']['sha256']:raise ValueError('Parent hash differs')
    if digest(ROOT/'MegaMan X4.bin')!=m['source_sha256']:raise ValueError('Original hash differs')
    with game.open('rb') as f:
        d=DiscReader(f,game.stat().st_size);current={n:d.read(r['lba'],r['size']) for n,r in records.items()}
    return records,original,current

def background(raw,palette,screen):
    g=entry(raw,0x10000);mp=entry(raw,0);info=entry(raw,1)
    canvas=Image.new('RGBA',(256,256))
    for j in range(256):
        v=struct.unpack_from('<H',mp,screen*512+j*2)[0]
        # US native renderer 80026B98/80026BA0 skips the complete zero map
        # word before resolving its attribute. Tile 0 may contain other art.
        if v==0:continue
        a=struct.unpack_from('<I',info,(v&16383)*4)[0]
        tid=a>>16&4095;row=(a>>8&63)+64
        words=struct.unpack_from('<16H',palette,row*32)
        pix=tile_pixels(g,tid)
        rgb=[(w&31)*255//31 for w in words]
        im=Image.new('RGBA',(16,16));im.putdata([((words[k]&31)*255//31,((words[k]>>5)&31)*255//31,((words[k]>>10)&31)*255//31,255 if k else 0) for k in pix])
        if v&0x4000:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if v&0x8000:im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        canvas.paste(im,(j%16*16,j//16*16))
    return canvas

def sheet(items,path,cols=5,cell=(260,210)):
    out=Image.new('RGB',(cols*cell[0],((len(items)+cols-1)//cols)*cell[1]),(40,43,57));dr=ImageDraw.Draw(out)
    for i,(title,im) in enumerate(items):
        im=im.copy();im.thumbnail((cell[0]-8,cell[1]-26),Image.Resampling.NEAREST);x=i%cols*cell[0];y=i//cols*cell[1]
        out.paste(im,(x,y+24),im);dr.text((x+3,y+3),title,fill='white')
    out.save(path)

def main():
    D.mkdir(exist_ok=True);(D/'original').mkdir(exist_ok=True);records,original,current=load();meta=[];items=[]
    def render(name,b,n,row,palname=None,texkind=0x10102,start=None,end=None,partskind=10):
        raw=original[name];g=entry(raw,texkind);p=entry(raw,partskind)
        if start is None:
            offs=struct.unpack('<'+'I'*(len(entry(raw,12))//4),entry(raw,12));start=offs[b];end=min((v for v in offs if v>start),default=len(g))
        c=aliased_composition(p,b,n);px,size,bounds,_=compose_static(g[start:end],local_composition(c))
        pal=entry(original[palname or name.replace('ST','COL',1)],5);words=struct.unpack_from('<16H',pal,row*32)
        key=f'{name}_b{b}_f{n}';im=save_image(px,size,words,D/'original'/f'{key}.png').convert('RGBA')
        meta.append(dict(file=name,bank=b,frame=n,count=c['bank_frame_count'],start=start,end=end,size=size,bounds=bounds,row=row,cluts=sorted({p['clut'] for p in c['parts']}),part_count=len(c['parts'])))
        items.append((key,im));return c
    for b in range(3):
        for n in range(aliased_composition(entry(original['ST0E_U1.ARC'],10),b,0)['bank_frame_count']):
            render('ST0E_U1.ARC',b,n,3 if b==2 else [4,5,6,6,6,6,4,4][min(n,7)] if b==1 else 0)
    sheet(items,D/'selection_inventory.png',6,(240,205));items=[]
    for b in (8,10,11,12,13):
        for n in range(aliased_composition(entry(original['ST00_00.ARC'],10),b,0)['bank_frame_count']):render('ST00_00.ARC',b,n,61 if b==10 else 62 if b in (11,12) else 63,'COL00_0X.ARC')
    sheet(items,D/'dialogue_inventory.png',7,(180,145));items=[]
    for name in ('ST0D_0X.ARC','ST0D_0Z.ARC'):
        raw=original[name];offs=struct.unpack('<'+'I'*(len(entry(raw,12))//4),entry(raw,12))
        for b in range(len(offs)):
            try:render(name,b,0,35)
            except (ValueError,IndexError,struct.error):pass
    sheet(items,D/'base_inventory.png');items=[]
    for name,palname in [('ST0E_U0.ARC','COL0E_U0.ARC'),('ST0F_UX.ARC','COL0F_U0.ARC'),('ST0F_UZ.ARC','COL0F_U0.ARC')]:
        raw=original[name];pal=entry(original[palname],5)
        for s in range(len(entry(raw,0))//512):
            im=background(raw,pal,s);im.save(D/'original'/f'{name}_screen{s}.png');items.append((f'{name} screen{s}',im))
    sheet(items,D/'background_inventory.png',5,(260,280))
    (D/'inventory.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    (D/'parent.json').write_text(json.dumps({'build':str(PARENT.relative_to(ROOT)),'sha256':digest(PARENT/'shibuki_riko.bin')},indent=2),encoding='utf8')
    print(json.dumps({'output':str(D),'frames':len(meta),'files':len(records)}))
if __name__=='__main__':main()
