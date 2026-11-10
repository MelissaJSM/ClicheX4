"""별도 피격233..236의 기본형/아머/효과를 읽기 전용 추출한다."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.project import digest
from src.psx_player import composition_frame
PARENT=ROOT/'out/ver_rin_nana/nana_fourth_reaction_20261030T092843615682Z'
PARENT_SHA='511e6320ad798fa0344c9e887c541b6a2647dcd53cc418928afd11c2f54654e0'
FRAMES=list(range(233,237))

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh work path required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent changed');arc=(PARENT/'modified.arc').read_bytes();c=entry(arc,3);out.mkdir(parents=True)
    board=Image.new('RGBA',(512,256));style=Image.new('RGBA',(768,256));records=[]
    for i,n in enumerate(FRAMES):
        im,v,f,raw=render(arc,n);im.save(out/f'base_{n:03}.png');parts={str(k):composition_frame(c,k,n) for k in (0,5,6,7,8)}
        base={p['tile'] for p in parts['0']['parts']};armor={p['tile'] for k in (5,6,7,8) for p in parts[str(k)]['parts']};require(not base&armor,'Base/armor overlap')
        records.append({'frame':n,'stream':f,'parts':parts,'base_tiles':sorted(base),'armor_tiles':sorted(armor)})
        if i<2:board.alpha_composite(im.crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST),(i*256,0))
    for i,n in enumerate((0,106,110)):style.alpha_composite(render(arc,n,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST),(i*256,0))
    board.save(out/'native_pose_reference.png');style.save(out/'costume_reference.png');write(out/'plan.json',{'parent_sha256':PARENT_SHA,'frames':FRAMES,'source_order':[233,234],'records':records,'game_modified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'frames':FRAMES})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
