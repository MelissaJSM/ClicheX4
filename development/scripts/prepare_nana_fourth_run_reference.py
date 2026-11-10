"""수용 포스 나나와 기본형 이동16쌍의 자세·공유·공간을 읽기 전용 준비한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from scripts.prepare_nana_fourth_pilot import render,entry,require,write
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame


def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh armor work directory required')
    parent=ROOT/'out/ver_rin_nana/nana_fourth_idle_20261030T063824458758Z'
    require(digest(parent/'rin_nana.bin')=='3d71c9ae921df7b9496e185894def835b2abf564ebc0a779a489d708a92cdaca','Accepted parent differs')
    arc=(parent/'modified.arc').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True)
    plan=json.loads((ROOT/'work/ver_rin_nana/nana_art/run_v1/plan.json').read_text('utf8'));order=plan['order']
    require(sorted(order)==list(range(1,33,2)),'Unexpected motion order');out.mkdir(parents=True)
    board=Image.new('RGBA',(1024,1024),(0,0,0,0));records=[]
    for i,n in enumerate(order):
        aliases=[f['index'] for f in bank['frames'] if f['offset']==bank['frames'][n]['offset']]
        require(aliases==[n,n+1],'Unexpected stream aliases')
        pair=[]
        base_tiles={q['tile'] for f in aliases for q in composition_frame(c,0,f)['parts']}
        for f in aliases:
            im,v,descriptor,raw=render(arc,f);im.save(out/f'base_{f:03}.png')
            armor={str(b):composition_frame(c,b,f) for b in (5,6,7,8)}
            armor_tiles={q['tile'] for b in armor.values() for q in b['parts']}
            require(not armor_tiles&base_tiles,'Base/armor ownership conflict')
            pair.append({'frame':f,'stream':descriptor,'armor_parts':armor,'base_tiles':sorted(base_tiles),'armor_tiles':sorted(armor_tiles)})
        pic=Image.open(out/f'base_{n:03}.png').convert('RGBA').crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST)
        board.alpha_composite(pic,(i%4*256,i//4*256));records.append(pair)
    board.save(out/'native_pose_reference.png')
    idle=Image.open(parent/'fourth_armor/frame_000_mask15.png').convert('RGBA').crop((56,52,104,108)).resize((576,672),Image.Resampling.NEAREST);idle.save(out/'accepted_armor_reference.png')
    write(out/'plan.json',{'task':'fourth_armor_nana','parent':parent.relative_to(ROOT).as_posix(),'parent_sha256':digest(parent/'rin_nana.bin'),'frame_order':order,'paired_frames':records,'native_start_animation':plan['start_animation'],'native_run_animation':plan['run_animation'],'new_game_modified':False})
    print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'pose_order':order,'pairs':len(records),'base_armor_tile_conflicts':0}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
