"""Collect current selection/save sprites without changing any game resource."""
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.project import digest
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import rgba
from scripts.ultimate_costume_swap_ui import ui_canvas
from scripts.verify_shibuki_save_icon import icon, rgba as word_rgba
from src.psx_player import composition_frame
from src.psx_ui_atlas import local_composition
from src.psx_static_effect import compose_static
from scripts.export_x_consistency import SOURCES

OUT = ROOT/'out/sprite_consistency_20261105'
MODES = {'ver_buki_riko':('shibuki','riko'), 'ver_rin_nana':('nana','rin')}

def canvas(im, origin=80):
    result=Image.new('RGBA',(384,384))
    result.alpha_composite(im,(160-origin,160-origin))
    return result

def sheet(items, path):
    # A single shared viewport for every frame on this board; never trim poses separately.
    boxes=[im.getbbox() for _,im in items if im.getbbox()]
    lo=min([b[0] for b in boxes]+[148])-4; top=min([b[1] for b in boxes]+[128])-4
    hi=max([b[2] for b in boxes]+[172])+4; bottom=max([b[3] for b in boxes]+[184])+4
    w=(hi-lo)*3; h=(bottom-top)*3+28
    board=Image.new('RGB',(6*w,((len(items)+5)//6)*h),'#242d3b');d=ImageDraw.Draw(board)
    for i,(label,im) in enumerate(items):
        x=i%6*w;y=i//6*h
        p=im.crop((lo,top,hi,bottom)).resize((w,h-28),Image.Resampling.NEAREST)
        board.paste(p,(x,y+28),p);d.text((x+3,y+5),label,fill='white')
    board.save(path)

def main():
    summary={}
    for mode,(xc,zc) in MODES.items():
        project,stem,expected=SOURCES[xc]
        source=ROOT/f'out/{project}/ultimate_costumes_swapped_20261105_v1/{stem}.bin'
        if digest(source)!=expected:raise ValueError('Review baseline BIN hash differs')
        assets,_=read_disc(source,('ST0E_U1.ARC','COL0E_U1.ARC','MOJIPAT.ARC','LOAD_U.ARC'))
        arc=assets['ST0E_U1.ARC'];texture=entry(arc,0x10102);parts=entry(arc,10)
        palette=entry(assets['COL0E_U1.ARC'],5);menu=assets['MOJIPAT.ARC'];load=entry(assets['LOAD_U.ARC'],0x10008)
        for char,bank,lo,hi,row in ((zc,0,0,40960,0),(xc,2,90112,len(texture),16)):
            folder=OUT/char/'supplementary';folder.mkdir(parents=True,exist_ok=True)
            records=[];items=[]
            count=composition_frame(parts,bank,0)['bank_frame_count']
            for n in range(count):
                comp=composition_frame(parts,bank,n);im=Image.new('RGBA',(384,384))
                for p in comp['parts']:
                    px,size,bounds,_=compose_static(texture[lo:hi],local_composition({**comp,'parts':[p]}))
                    words=struct.unpack_from('<16H',palette,(row+p['clut'])*32)
                    img=rgba(np.frombuffer(px,np.uint8).reshape(size[1],size[0]),words)
                    im.alpha_composite(img,(160+bounds[0],160+bounds[1]))
                name=f'selection_{n:03}.png';im.save(folder/name);items.append((f'select {bank}:{n}',im))
                records.append({'id':f'selection_{n:03}','kind':'selection','frame':n,'bank':bank,'image':name,'parts':comp['parts']})
            for start in range(0,len(items),36):sheet(items[start:start+36],folder/f'selection_sheet_{start//36:02}.png')
            saved=[]
            if char==zc:
                saved=[('save_normal',ui_canvas(menu,load,43,8)),('save_black',ui_canvas(menu,load,43,27))]
            else:
                saved=[(f'save_fourth_{mask:02}_arm{arm}',icon(menu,load,mask,arm)) for arm in (1,2) for mask in range(16)]
                saved += [('save_ultimate_pre',ui_canvas(menu,load,52,30)),('save_ultimate_post',ui_canvas(menu,load,53,31))]
            save_items=[]
            for label,a in saved:
                im=canvas(word_rgba(a));im.save(folder/(label+'.png'));save_items.append((label,im))
                records.append({'id':label,'kind':'save','image':label+'.png'})
            sheet(save_items,folder/'save_sheet.png')
            report={'character':char,'source_bin':source.relative_to(ROOT).as_posix(),'source_sha256':expected,
                    'canvas':{'size':[384,384],'origin':[160,160]},'frames':records,'runtime_verified':False,
                    'note':'Supplementary selection/save sprites. Large illustrations are outside the gameplay style comparison.'}
            (folder/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
            summary[char]={'selection':count,'save':len(saved)}
    print(json.dumps(summary))

if __name__=='__main__':main()
