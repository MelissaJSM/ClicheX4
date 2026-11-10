"""차지 연계와 더블 사이클론의 실제 조립·사랑이 접점을 수집한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import full,D
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_victory_edge_20261104T111230439476Z'
PARENT_SHA='0d32b509c59a07febf875e286a90555f7437cdbb4b3c4349fa532c8eeb75e121'
ARC_SHA='720c5e6745a7d97a653f925654e042e966907127233490378f0e9210df6c5648'
FRAMES=[88,89,90,91,97,98,99]
ORDER=[89,90,91,97,98]

def prepare(out):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh reference directory required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed')
    out.mkdir();arc=(PARENT/'PL02_U.ARC').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);records=[]
    words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.uint8)
    board=Image.new('RGBA',(960,640))
    for n in FRAMES:
        im,v,f,raw=render(arc,n);im.save(out/f'native_{n:03}.png');aliases=[q['index']for q in bank['frames']if q['offset']==f['offset']];require(set(aliases)<=set(FRAMES),'Unexpected sharing')
        ys,xs=np.nonzero(v==14);eye=[float(np.median(xs)),float(np.median(ys))]if len(xs)else None
        records.append(dict(frame=n,eye=eye,aliases=aliases,stream=f,bbox=im.getbbox(),parts={str(b):composition_frame(c,b,n)for b in(0,5,6,7,8)}))
    for i,n in enumerate(ORDER+[0]):
        im=render(arc,n)[0]if n else save_image(full(arc,0).tobytes(),(160,160),words,out/'accepted_idle.png').convert('RGBA')
        tile=im.crop((40,32,120,112)).resize((320,320),Image.Resampling.NEAREST);board.alpha_composite(tile,(i%3*320,i//3*320))
    board.save(out/'native_pose_reference.png')
    ref=Image.new('RGBA',(1280,320))
    for i,n in enumerate((0,85,205,207)):
        v=full(arc,n);rgba=np.concatenate((rgb[v],((v>0)*255).astype(np.uint8)[...,None]),2);im=Image.fromarray(rgba).crop((48,36,112,100)).resize((320,320),Image.Resampling.NEAREST);ref.alpha_composite(im,(320*i,0))
    ref.save(out/'accepted_style_reference.png');write(out/'inventory.json',dict(parent=PARENT.relative_to(ROOT).as_posix(),parent_sha256=PARENT_SHA,frames=FRAMES,order=ORDER,records=records))
    print(json.dumps([dict(frame=q['frame'],eye=q['eye'],aliases=q['aliases'],bbox=q['bbox'])for q in records]))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
