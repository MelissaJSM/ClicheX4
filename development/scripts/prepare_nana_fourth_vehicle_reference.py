"""체이서13·탑승 머리19와 공유 빈198을 읽기 전용 조사한다."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame
PARENT=ROOT/'out/ver_rin_nana/nana_fourth_hover_20261030T113845331469Z'
PARENT_SHA='f8b10f3bf16c37f5635f2c652c46dbbab766f858a80d4a4013cf5960b448f1fa'
FRAMES=list(range(162,175))+list(range(184,204))
EDITED_FRAMES=[n for n in FRAMES if n!=198]
ORDER=[162,166,170,174]

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh reference required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent changed');out.mkdir(parents=True)
    arc=(PARENT/'modified.arc').read_bytes();c,g=entry(arc,3),entry(arc,2);bank=graphics_bank(g,0,allow_bank_aliases=True);records=[]
    for n in FRAMES:
        im,base,f,raw=render(arc,n);im.save(out/f'base_{n:03}.png');parts={str(b):composition_frame(c,b,n) for b in (0,5,6,7,8)};bt={q['tile'] for q in parts['0']['parts']};at={q['tile'] for b in (5,6,7,8) for q in parts[str(b)]['parts']};aliases=[q['index'] for q in bank['frames'] if q['offset']==f['offset']];require(set(aliases)<=set(FRAMES),'Unselected alias')
        if n<184:require(not bt&at,'Body/armor conflict')
        records.append({'frame':n,'stream':f,'bbox':im.getbbox(),'parts':parts,'base_tiles':sorted(bt),'armor_tiles':sorted(at),'aliases':aliases,'blank_preserved':n==198})
    board=Image.new('RGBA',(1024,256));ref=Image.new('RGBA',(768,256))
    for i,n in enumerate(ORDER):board.alpha_composite(render(arc,n)[0].crop((40,40,104,104)).resize((256,256),Image.Resampling.NEAREST),(i*256,0))
    for i,n in enumerate((0,37,94)):ref.alpha_composite(render(arc,n,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST),(i*256,0))
    board.save(out/'native_pose_reference.png');ref.save(out/'accepted_armor_reference.png')
    write(out/'plan.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'edited_frames':EDITED_FRAMES,'blank_preserved':[198],'frame_order':ORDER,'grid':[4,1],'records':records,'new_game_modified':False});print({'edited':len(EDITED_FRAMES),'processed':len(FRAMES),'blank_preserved':198})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
