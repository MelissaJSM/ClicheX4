"""공중 대시·호버12참조와 기존 의상/원작 발 위치를 조사한다."""
import argparse,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_pilot import render,entry,require,write,ORIGINAL
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame
PARENT=ROOT/'out/ver_rin_nana/nana_fourth_elemental_20261030T112208921559Z'
PARENT_SHA='161942372bd8016b0002d1de09722df60545c314a56954b944a1294555d27d42'
FRAMES=[93,94]+list(range(221,231))
ORDER=[94,221,223,225,227,229]
REUSE={93:37,221:39,222:40,223:37,224:38,225:45,226:46,227:47,228:48,229:41,230:42}
CUTS={221:85,222:85,223:86,224:86,225:85,226:85,227:87,228:87,229:85,230:85}

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh reference path required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent changed');out.mkdir(parents=True)
    arc=(PARENT/'modified.arc').read_bytes();original=ORIGINAL.read_bytes();require(digest(ORIGINAL)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a','Original changed')
    c,g=entry(arc,3),entry(arc,2);bank=graphics_bank(g,0,allow_bank_aliases=True);records=[]
    for n in FRAMES:
        im,base,f,raw=render(arc,n);im.save(out/f'base_{n:03}.png');parts={str(b):composition_frame(c,b,n) for b in (0,5,6,7,8)};bt={q['tile'] for q in parts['0']['parts']};at={q['tile'] for b in (5,6,7,8) for q in parts[str(b)]['parts']}
        require(not bt&at,'Base/armor conflict');aliases=[q['index'] for q in bank['frames'] if q['offset']==f['offset']];require(set(aliases)<=set(FRAMES),'Unselected alias')
        if n in REUSE:require(np.array_equal(base,render(arc,REUSE[n])[1]),'Reuse body differs')
        records.append({'frame':n,'source':REUSE.get(n),'stream':f,'bbox':im.getbbox(),'parts':parts,'armor_tiles':sorted(at),'aliases':aliases,'lower_cut':CUTS.get(n)})
    for name,orig in [('native_pose_reference.png',False),('original_foot_reference.png',True)]:
        board=Image.new('RGBA',(768,512))
        for i,n in enumerate(ORDER):
            im=render(original,n,True)[0] if orig else render(arc,REUSE.get(n,n),n!=94)[0]
            board.alpha_composite(im.crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST),(i%3*256,i//3*256))
        board.save(out/name)
    ref=Image.new('RGBA',(768,256))
    for i,n in enumerate((0,37,39)):ref.alpha_composite(render(arc,n,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST),(i*256,0))
    ref.save(out/'accepted_armor_reference.png')
    write(out/'plan.json',{'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'frames':FRAMES,'frame_order':ORDER,'grid':[3,2],'records':records,'reuse':REUSE,'new_game_modified':False})
    print({'frames':FRAMES,'reuse_upper':REUSE,'lower_cut':CUTS})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
