"""수용 나나 대시8자세·속도선 공유18참조와 포스 의상을 추출한다."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame

PARENT=ROOT/'out/ver_rin_nana/nana_fourth_wall_20261030T083253784167Z'
PARENT_SHA='298f5e69ca1abe490499fe68f905375d0938a26a2747b4c64bbc5cc4cea2b88a'
FRAMES=list(range(67,85));ORDER=[67,69,71,75,77,79,81,83]


def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh work directory required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Accepted wall parent changed')
    arc=(PARENT/'modified.arc').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);out.mkdir(parents=True)
    board=Image.new('RGBA',(1024,512));shots=Image.new('RGBA',(1024,512));records=[]
    for i,n in enumerate(ORDER):
        aliases=[q['index'] for q in bank['frames'] if q['offset']==bank['frames'][n]['offset']]
        require(aliases==([71,72,73,74] if n==71 else [n,n+1]),'Dash aliases differ')
        base_tiles={q['tile'] for f in aliases for q in composition_frame(c,0,f)['parts']};group=[]
        for f in aliases:
            im,v,descriptor,raw=render(arc,f);im.save(out/f'base_{f:03}.png');parts={str(k):composition_frame(c,k,f) for k in (5,6,7,8)};armor_tiles={q['tile'] for cp in parts.values() for q in cp['parts']};require(not base_tiles&armor_tiles,'Base/effect/armor overlap')
            group.append({'frame':f,'stream':descriptor,'bbox':im.getbbox(),'base_tiles':sorted(base_tiles),'armor_tiles':sorted(armor_tiles),'armor_parts':parts})
            if f in (n,n+1):
                tile=im.crop((40,48,120,112)).resize((256,205),Image.Resampling.NEAREST)
                (board if f==n else shots).alpha_composite(tile,(i%4*256,i//4*256+25))
        records.append(group)
    board.save(out/'native_pose_reference.png');shots.save(out/'native_shot_reference.png')
    ref=Image.new('RGBA',(1024,256))
    for i,n in enumerate((0,5,37,65)):
        im=render(arc,n,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);ref.alpha_composite(im,(i*256,0))
    ref.save(out/'accepted_armor_reference.png')
    write(out/'plan.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frame_order':ORDER,'paired_frames':records,'grid':[4,2],'speed_line_aliases':{'73':71,'74':72},'new_game_modified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'poses':8,'references':18,'base_armor_conflicts':0})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
