"""프로스트 타워·라이징 파이어9참조의 실제 자세와 공유 자원을 수집한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import full,D
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_special_20261104T113013217294Z'
PARENT_SHA='4eddaf469b068a463c174c618192d6abc8d13069e849aebc7f812be537dae813'
ARC_SHA='4d47a3ea8bd6eb8e21f1c94ee6540164fdc2c813a649009a62324c47ea2874e1'
FRAMES=[95,96,100,101,102,103,104,231,232]
ORDER=[95,100,101,102,103,104,231]

def prepare(out):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh reference directory required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed')
    out.mkdir();arc=(PARENT/'PL02_U.ARC').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);records=[];words=struct.unpack_from('<16H',entry(arc,9),32)
    board=Image.new('RGBA',(1280,640))
    for n in FRAMES:
        im,v,f,raw=render(arc,n);im.save(out/f'native_{n:03}.png');im.crop((48,32,112,104)).resize((512,576),Image.Resampling.NEAREST).save(out/f'contact_{n:03}.png');aliases=[q['index']for q in bank['frames']if q['offset']==f['offset']];require(set(aliases)<=set(FRAMES),'Unexpected sharing');yy,xx=np.indices(v.shape);ys,xs=np.nonzero((v==14)&(yy<85));eye=[float(np.median(xs)),float(np.median(ys))]if len(xs)else None
        records.append(dict(frame=n,eye=eye,aliases=aliases,stream=f,bbox=im.getbbox(),parts={str(b):composition_frame(c,b,n)for b in(0,5,6,7,8)}))
    for i,n in enumerate(ORDER+[0]):
        im=render(arc,n)[0]if n else save_image(full(arc,0).tobytes(),(160,160),words,out/'accepted_idle.png').convert('RGBA');tile=im.crop((40,24,120,104)).resize((320,320),Image.Resampling.NEAREST);board.alpha_composite(tile,(i%4*320,i//4*320))
    board.save(out/'native_pose_reference.png');ref=Image.new('RGBA',(1280,320))
    for i,n in enumerate((0,37,89,231)):
        source=n if n!=231 else 207;v=full(arc,source);im=save_image(v.tobytes(),(160,160),words,out/f'accepted_{source:03}.png').convert('RGBA');tile=im.crop((40,24,120,104)).resize((320,320),Image.Resampling.NEAREST);ref.alpha_composite(tile,(320*i,0))
    ref.save(out/'accepted_style_reference.png');write(out/'inventory.json',dict(parent=PARENT.relative_to(ROOT).as_posix(),parent_sha256=PARENT_SHA,frames=FRAMES,order=ORDER,records=records));print(json.dumps([dict(frame=q['frame'],eye=q['eye'],aliases=q['aliases'],bbox=q['bbox'])for q in records]))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
