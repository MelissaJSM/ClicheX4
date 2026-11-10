"""프로스트/라이징 계열9참조의 기본 몸·아머 분리와 공유 조사."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame
PARENT=ROOT/'out/ver_rin_nana/nana_fourth_special_20261030T110429756883Z'
PARENT_SHA='3c95814cca35499b47c96152c30a15e7791ec062fedd54a19eba50ba368bdb23'
FRAMES=[95,96,100,101,102,103,104,231,232]
ORDER=[95,100,101,102,103,104,231]

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh reference directory required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent changed')
    arc=(PARENT/'modified.arc').read_bytes();c,g=entry(arc,3),entry(arc,2);bank=graphics_bank(g,0,allow_bank_aliases=True);out.mkdir(parents=True);records=[];board=Image.new('RGBA',(1024,512))
    for n in FRAMES:
        im,base,f,raw=render(arc,n);im.save(out/f'base_{n:03}.png');parts={str(b):composition_frame(c,b,n) for b in (0,5,6,7,8)};base_tiles={q['tile'] for q in parts['0']['parts']};armor_tiles={q['tile'] for b in (5,6,7,8) for q in parts[str(b)]['parts']};require(not base_tiles&armor_tiles,'Shared base/armor tile');aliases=[q['index'] for q in bank['frames'] if q['offset']==f['offset']];require(set(aliases)<=set(FRAMES),'Unselected alias')
        records.append({'frame':n,'stream':f,'bbox':im.getbbox(),'parts':parts,'armor_tiles':sorted(armor_tiles),'aliases':aliases})
    for i,n in enumerate(ORDER+[0]):
        im=render(arc,n,n==0)[0];tile=im.crop((48,40,112,104)).resize((256,256),Image.Resampling.NEAREST);board.alpha_composite(tile,(i%4*256,i//4*256))
    board.save(out/'native_pose_reference.png');ref=Image.new('RGBA',(1024,256))
    for i,n in enumerate((0,37,138,89)):
        tile=render(arc,n,True)[0].crop((48,40,112,104)).resize((256,256),Image.Resampling.NEAREST);ref.alpha_composite(tile,(i*256,0))
    ref.save(out/'accepted_armor_reference.png');write(out/'plan.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'frame_order':ORDER+[0],'grid':[4,2],'records':records,'new_game_modified':False});print({'frames':FRAMES,'pose_order':ORDER+[0]})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
