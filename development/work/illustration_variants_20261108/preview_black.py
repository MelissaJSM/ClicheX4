from pathlib import Path
import json,struct,sys
from PIL import Image,ImageDraw
from black_ui import H,ROOT,words,CHANGES
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import DiscReader,psx_arc
from src.psx_ui_atlas import aliased_composition
from src.psx_ui_render import render_static_rgba

for mode in CHANGES:
    d=H/mode; info=json.loads((d/'source.json').read_text('utf8')); normal,black=words(mode)
    out=d/'black_proposal'; rows=[]; board=Image.new('RGB',(912,1032),'#202a3a'); dr=ImageDraw.Draw(board)
    for group,(file,base,bank,cols,top) in enumerate([('ST0D_0Z.ARC',63488,2,7,0),('ST00_00.ARC',217088,13,3,540)]):
        raw=(d/'originals'/file).read_bytes(); texture=entry(raw,0x10102)[base:];parts=entry(raw,10);count=aliased_composition(parts,bank,0)['bank_frame_count']
        for n in range(count):
            comp=aliased_composition(parts,bank,n)
            for var,pal in [('normal',normal),('black',black)]:
                im,bb=render_static_rgba(texture,comp,{0:pal}); name=f'{"hq" if group==0 else "dialogue"}_{n:02}_{var}.png';im.save(out/name)
                if group==0:
                    if var=='normal':continue
                    x=n%cols*130;y=top+n//cols*265
                    big=im.resize((im.width*2,im.height*2),0);board.paste(big,(x+(130-big.width)//2,y+30),big);dr.text((x+5,y+8),f'HQ {n} / BLACK',fill='white')
                else:
                    x=n*300+(0 if var=='normal' else 145);y=top
                    big=im.resize((im.width*1,im.height*1),0);board.paste(big,(x,y+35),big);dr.text((x,y+10),f'{n} / {var}',fill='white')
                if n in (0,1):rows.append((group,n,var,name))
    # Large, directly decoded closed-mouth comparison for clothing/eyes.
    for k,var in enumerate(('normal','black')):
        im=Image.open(out/f'dialogue_01_{var}.png').resize((336,288),0);board.paste(im,(k*440+20,710),im)
    board.save(out/'review.png')
    palette_matches=[]
    src=ROOT/Path(info['pointer']['cue']).with_suffix('.bin')
    with src.open('rb')as f:
        reader=DiscReader(f,src.stat().st_size); files=reader.inspect()['files']
        for rec in files:
            name=rec['name'].split(';')[0]
            if not name.startswith('COL') or not name.endswith('.ARC'):continue
            raw=reader.read(rec['lba'],rec['size']);p=entry(raw,5)
            hits=[i for i in range(len(p)//32)if p[i*32:(i+1)*32]==struct.pack('<16H',*normal)]
            if hits:palette_matches.append({'file':name,'rows':hits})
    (out/'palette_inventory.json').write_text(json.dumps(palette_matches,indent=2)+'\n','utf8')
    print(mode,len(palette_matches),'palette files',flush=True)
