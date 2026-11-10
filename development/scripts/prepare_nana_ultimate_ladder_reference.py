"""얼티밋 사다리의 실제 조립·반전·슬롯과 승인된 체형 기준을 추출한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_low_hp_shape_20261104T102858790508Z'
PARENT_SHA='5385c70137954a9e380540539f389899c8f20e5428926e8e7bd51c8dbc60af08'
ARC_SHA='9efea33ac169d8da0fa16c29d76c026f8211b2b355da4368bf28ac7eb407d9db'
FRAMES=list(range(143,156))+[183]
ORDER=[143,144,146,149,151,153,154,183,155]
def prepare(out):
 out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated reference required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent differs');out.mkdir();arc=(PARENT/'PL02_U.ARC').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);board=Image.new('RGBA',(960,960));records=[]
 for n in FRAMES:
  im,base,f,raw=render(arc,n);im.save(out/f'native_{n:03}.png');aliases=[q['index']for q in bank['frames']if q['offset']==f['offset']];require(set(aliases)<=set(FRAMES),'Shared with unselected pose');parts={str(k):composition_frame(c,k,n)for k in(0,5,6,7,8)};records.append(dict(frame=n,aliases=aliases,stream=f,bbox=im.getbbox(),parts=parts))
  if n in ORDER:
   i=ORDER.index(n);tile=im.crop((40,40,120,120)).resize((320,320),Image.Resampling.NEAREST);board.alpha_composite(tile,(i%3*320,i//3*320))
 board.save(out/'native_pose_reference.png')
 reference=Image.new('RGBA',(1280,320))
 import numpy as np,struct
 words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.uint8)
 for i,n in enumerate((0,5,55,122)):
  v=full(arc,n);rgba=np.concatenate((rgb[v],((v>0)*255).astype(np.uint8)[...,None]),2);im=Image.fromarray(rgba,'RGBA').crop((48,44,112,108)).resize((320,320),Image.Resampling.NEAREST);reference.alpha_composite(im,(320*i,0))
 reference.save(out/'accepted_style_reference.png');write(out/'inventory.json',dict(parent=PARENT.relative_to(ROOT).as_posix(),parent_sha256=PARENT_SHA,frames=FRAMES,order=ORDER,records=records));print(json.dumps(dict(output=str(out),groups=[(q['frame'],q['aliases'],q['stream']['tile_count'])for q in records])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
