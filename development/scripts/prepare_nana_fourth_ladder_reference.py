"""수용 기본형 사다리와 포스 의상 기준, 원작 파츠 공유 구조를 추출한다."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_pilot import render,entry,require,write,ORIGINAL
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame

PARENT=ROOT/'out/ver_rin_nana/nana_fourth_hurt_aura_20261030T100952825921Z'
PARENT_SHA='aa060ae9badee6a1ad0ec9d7d7e8483d5be67b18819e330d43a5178082b46e3d'
FRAMES=list(range(143,156))+[183]
ORDER=[143,144,146,149,151,153,154,183,155]

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh armor reference directory required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Accepted parent changed')
    arc=(PARENT/'modified.arc').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);out.mkdir(parents=True)
    records=[];boards=[Image.new('RGBA',(768,768)) for _ in range(2)]
    original=ORIGINAL.read_bytes()
    for n in FRAMES:
        im,base,f,raw=render(arc,n);im.save(out/f'base_{n:03}.png');parts={str(k):composition_frame(c,k,n) for k in (0,5,6,7,8)}
        aliases=[q['index'] for q in bank['frames'] if q['offset']==f['offset']]
        base_tiles={q['tile'] for a in aliases for q in composition_frame(c,0,a)['parts']};armor_tiles={q['tile'] for k in (5,6,7,8) for a in aliases for q in composition_frame(c,k,a)['parts']}
        require(set(aliases)<=set(FRAMES) and not base_tiles&armor_tiles,'Unselected alias or base/armor overlap')
        records.append({'frame':n,'aliases':aliases,'stream':f,'bbox':im.getbbox(),'base_tiles':sorted(base_tiles),'armor_tiles':sorted(armor_tiles),'parts':parts})
        if n in ORDER:
            i=ORDER.index(n)
            for board,pic in zip(boards,(im,render(original,n)[0])):
                tile=pic.crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);board.alpha_composite(tile,(i%3*256,i//3*256))
    boards[0].save(out/'native_pose_reference.png');boards[1].save(out/'original_pose_reference.png')
    ref=Image.new('RGBA',(1024,256))
    for i,n in enumerate((0,5,37,65)):
        im=render(arc,n,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);ref.alpha_composite(im,(i*256,0))
    ref.save(out/'accepted_armor_reference.png')
    write(out/'plan.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'frame_order':ORDER,'grid':[3,3],'records':records,'new_game_modified':False})
    print({'frames':len(FRAMES),'source_poses':len(ORDER),'groups':[(n,next(q for q in records if q['frame']==n)['aliases']) for n in ORDER]})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
