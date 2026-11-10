"""수용 기본형의 벽12참조와 현재 포스 의상을 읽기 전용 추출한다."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame

PARENT=ROOT/'out/ver_rin_nana/nana_fourth_air_20261030T075737575252Z'
PARENT_SHA='ab61854d8a83c9a932e83614f4377261804cb948a19f0e8d3caf1ba22e9bc401'
FRAMES=list(range(55,67));ORDER=list(range(55,67,2))

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh armor work directory required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Accepted air parent changed')
    arc=(PARENT/'modified.arc').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);out.mkdir(parents=True)
    board=Image.new('RGBA',(768,512));shots=Image.new('RGBA',(768,512));records=[]
    for i,n in enumerate(ORDER):
        aliases=[q['index'] for q in bank['frames'] if q['offset']==bank['frames'][n]['offset']];require(aliases==[n,n+1],'Wall stream aliases differ')
        base_tiles={q['tile'] for f in aliases for q in composition_frame(c,0,f)['parts']};pair=[]
        for f in aliases:
            im,v,descriptor,raw=render(arc,f);im.save(out/f'base_{f:03}.png');parts={str(k):composition_frame(c,k,f) for k in (5,6,7,8)};armor_tiles={q['tile'] for cp in parts.values() for q in cp['parts']};require(not base_tiles&armor_tiles,'Base/armor tile conflict')
            pair.append({'frame':f,'stream':descriptor,'bbox':im.getbbox(),'base_tiles':sorted(base_tiles),'armor_tiles':sorted(armor_tiles),'armor_parts':parts})
            tile=im.crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST)
            (board if f==n else shots).alpha_composite(tile,(i%3*256,i//3*256))
        records.append(pair)
    board.save(out/'native_pose_reference.png');shots.save(out/'native_shot_reference.png')
    ref=Image.new('RGBA',(768,256))
    for i,n in enumerate((0,5,37)):
        im=render(arc,n,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);ref.alpha_composite(im,(i*256,0))
    ref.save(out/'accepted_armor_reference.png')
    write(out/'plan.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frame_order':ORDER,'paired_frames':records,'grid':[3,2],'new_game_modified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'poses':len(ORDER),'frames':len(FRAMES),'base_armor_conflicts':0})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
