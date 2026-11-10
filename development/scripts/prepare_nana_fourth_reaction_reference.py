"""수용 대시판에서 피격·저체력의 실제 조립과 공유 효과를 추출한다."""
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image, ImageDraw
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame

PARENT=ROOT/'out/ver_rin_nana/nana_fourth_dash_20261030T090709235005Z'
PARENT_SHA='4099da5395590da96f22c984241cd7f7f28aeccc5721507c332f4557d9c303b4'
FRAMES=[106,107,108,110,111,120,121,122,123,124,125]
PRESERVED_FLASH=[109,112,113,114]
ORDER=[106,110,120]

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh work directory required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Accepted dash parent changed')
    arc=(PARENT/'modified.arc').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);out.mkdir(parents=True)
    records=[];board=Image.new('RGBA',(768,256));detail=Image.new('RGBA',(1024,1024))
    for i,n in enumerate(FRAMES+PRESERVED_FLASH):
        im,v,f,raw=render(arc,n);im.save(out/f'base_{n:03}.png')
        aliases=[q['index'] for q in bank['frames'] if q['offset']==f['offset']]
        parts={str(k):composition_frame(c,k,n) for k in (0,5,6,7,8)}
        base_tiles={q['tile'] for q in parts['0']['parts']};armor_tiles={q['tile'] for k in (5,6,7,8) for q in parts[str(k)]['parts']}
        require(not base_tiles&armor_tiles,'Base/armor tiles overlap')
        records.append({'frame':n,'aliases':aliases,'stream':f,'bbox':im.getbbox(),'parts':parts})
        tile=im.crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);detail.alpha_composite(tile,(i%4*256,i//4*256))
        if n in ORDER:board.alpha_composite(tile,(ORDER.index(n)*256,0))
    board.save(out/'native_pose_reference.png');detail.save(out/'all_native_references.png')
    ref=Image.new('RGBA',(1024,256))
    for i,n in enumerate((0,5,37,65)):
        im=render(arc,n,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);ref.alpha_composite(im,(i*256,0))
    ref.save(out/'accepted_armor_reference.png')
    write(out/'plan.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frame_order':ORDER,'frames':FRAMES,'preserved_flash':PRESERVED_FLASH,'records':records,'grid':[3,1],'new_game_modified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'poses':3,'costume_references':len(FRAMES),'preserved_flash':PRESERVED_FLASH})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
