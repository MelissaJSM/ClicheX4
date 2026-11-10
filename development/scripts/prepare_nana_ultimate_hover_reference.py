"""수용 얼티밋 상체·원작 추진 발·현재 호버 타일 관계를 기록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_pilot import entry,render,require,write,ORIGINAL
from scripts.prepare_nana_ultimate_shot_arm import D,full
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_elemental_20261104T115308106297Z'
PARENT_SHA='9b938696d0a370e517e677a490012b3ff00ac5ea4beb8cb14ca029fb09a8906c'
ARC_SHA='233a48b390046884b3caf0bd96895eb8ed06d8f0ea313c6de6d51b60175d912f'
FRAMES=list(range(221,231));ORDER=FRAMES[::2]
REUSE={221:39,222:40,223:37,224:38,225:45,226:46,227:47,228:48,229:41,230:42}
CUTS={221:85,222:85,223:86,224:86,225:85,226:85,227:87,228:87,229:85,230:85}

def prepare(out):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir()
    arc=(PARENT/'PL02_U.ARC').read_bytes();orig=ORIGINAL.read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.uint8);inventory=[]
    for n in FRAMES:
        f=bank['frames'][n];parts={str(b):composition_frame(c,b,n)['parts']for b in(0,5,6,7,8)};inventory.append(dict(frame=n,stream=f,parts=parts,aliases=[q['index']for q in bank['frames']if q['offset']==f['offset']],upper_source=REUSE[n],cut=CUTS[n],base_equal_to_air=bool(np.array_equal(render(arc,n)[1],render(arc,REUSE[n])[1]))))
    for kind in('accepted','native','base'):
        board=Image.new('RGBA',(1600,360));draw=ImageDraw.Draw(board)
        for i,n in enumerate(ORDER):
            if kind=='native':im=render(orig,n,True)[0]
            else:
                v=full(arc,REUSE[n])if kind=='accepted'else render(arc,n)[1];im=Image.fromarray(np.concatenate((rgb[v],((v>0)*255).astype(np.uint8)[...,None]),2))
            pic=im.crop((40,36,120,116)).resize((320,320),Image.Resampling.NEAREST);board.alpha_composite(pic,(i*320,30));draw.text((i*320+5,5),str(n),fill='white');im.save(out/f'{kind}_{n:03}.png')
        board.save(out/f'{kind}_reference.png')
    write(out/'inventory.json',inventory);print(json.dumps([dict(frame=q['frame'],tiles=q['stream']['tile_count'],base_equal=q['base_equal_to_air'],aliases=q['aliases'])for q in inventory]))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
