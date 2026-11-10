"""등장·준비·승리·귀환의 얼티밋 몸과 공통 빛을 분리해 추출한다."""
import argparse,json,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_ceremony_reference import FRAMES,ORDER,PRESERVED
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame
from scripts.prepare_shibuki_capsule_nova import raster
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_ladder_20261104T104212237140Z'
PARENT_SHA='d9c2e52a117bc579dc8a718cf4e1a2f4fdb7f93a9b296eb113765821a2cb51ba'
ARC_SHA='f26be08d15f57687ba489a9b47d8e834abe23b9d53c383bb2e1528b64aab653c'
def prepare(out):
 out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh reference required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();arc=(PARENT/'PL02_U.ARC').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);board=Image.new('RGBA',(960,640));records=[]
 for n in FRAMES+PRESERVED:
  im,base,f,raw=render(arc,n);im.save(out/f'native_{n:03}.png');aliases=[q['index']for q in bank['frames']if q['offset']==f['offset']];parts={str(b):composition_frame(c,b,n)for b in(0,5,6,7,8)}
  if n in FRAMES:require(aliases==[n],'Unexpected aliases')
  else:require(all(not np.any(raster(g,c,0,b,n))for b in(5,6,7,8)),'Common frame has opaque armor')
  records.append(dict(frame=n,aliases=aliases,stream=f,bbox=im.getbbox(),parts=parts,armor_changed=n in FRAMES))
  if n in ORDER:
   i=ORDER.index(n);board.alpha_composite(im.crop((40,32,120,112)).resize((320,320),Image.Resampling.NEAREST),(i%3*320,i//3*320))
 board.save(out/'native_pose_reference.png');words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.uint8);reference=Image.new('RGBA',(1280,320))
 for i,n in enumerate((0,5,122,149)):
  v=full(arc,n);rgba=np.concatenate((rgb[v],((v>0)*255).astype(np.uint8)[...,None]),axis=2);reference.alpha_composite(Image.fromarray(rgba,'RGBA').crop((40,40,120,120)).resize((320,320),Image.Resampling.NEAREST),(i*320,0))
 reference.save(out/'accepted_style_reference.png');write(out/'inventory.json',dict(parent=PARENT.relative_to(ROOT).as_posix(),parent_sha256=PARENT_SHA,frames=FRAMES,order=ORDER,preserved_common_frames=PRESERVED,records=records));print(json.dumps(dict(frames=FRAMES,preserved=PRESERVED,poses=[(q['frame'],q['bbox'])for q in records if q['frame']in FRAMES])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
