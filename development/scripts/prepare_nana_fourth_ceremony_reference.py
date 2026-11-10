"""등장/승리/귀환 중 실제 아머 표시10참조와 공통17참조를 분리한다."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame
from src.psx_sprite_batch import canvas_from_parts

PARENT=ROOT/'out/ver_rin_nana/nana_fourth_ladder_20261030T102737287966Z'
PARENT_SHA='1821dc0ff7e95a644ed42a8a2f5e81529fbf794b618c31ce214f551ef62583b4'
FRAMES=[138,139,141,142,156,157,204,205,206,207]
ORDER=[138,156,204,205,206,207]
PRESERVED=[n for n in list(range(126,143))+list(range(156,162))+list(range(204,208)) if n not in FRAMES]

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh reference directory required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent changed')
    arc=(PARENT/'modified.arc').read_bytes();c,g=entry(arc,3),entry(arc,2);bank=graphics_bank(g,0,allow_bank_aliases=True);out.mkdir(parents=True);records=[];board=Image.new('RGBA',(768,512))
    for n in FRAMES+PRESERVED:
        im,base,f,raw=render(arc,n);im.save(out/f'base_{n:03}.png');parts={str(b):composition_frame(c,b,n) for b in (0,5,6,7,8)};base_tiles={q['tile'] for q in parts['0']['parts']};armor_tiles={q['tile'] for b in (5,6,7,8) for q in parts[str(b)]['parts']};require(not base_tiles&armor_tiles,'Shared base/armor tile')
        if n in FRAMES:require([q['index'] for q in bank['frames'] if q['offset']==f['offset']]==[n],'Unselected alias')
        else:require(all(not np.any(canvas_from_parts(raw,f['tile_count'],parts[str(b)])) for b in (5,6,7,8)),'Preserved frame unexpectedly contains armor')
        records.append({'frame':n,'stream':f,'bbox':im.getbbox(),'parts':parts,'armor_tiles':sorted(armor_tiles),'armor_changed':n in FRAMES})
        if n in ORDER:
            i=ORDER.index(n);tile=im.crop((48,40,112,104)).resize((256,256),Image.Resampling.NEAREST);board.alpha_composite(tile,(i%3*256,i//3*256))
    board.save(out/'native_pose_reference.png');ref=Image.new('RGBA',(1024,256))
    for i,n in enumerate((0,5,37,149)):
        tile=render(arc,n,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);ref.alpha_composite(tile,(i*256,0))
    ref.save(out/'accepted_armor_reference.png');write(out/'plan.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'frame_order':ORDER,'preserved_common_frames':PRESERVED,'grid':[3,2],'records':records,'new_game_modified':False});print({'frames':FRAMES,'preserved_common_frames':PRESERVED})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
