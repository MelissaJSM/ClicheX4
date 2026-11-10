from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import D,gfx,parts,original,front
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import edit_frame_set
from src.psx_compress import encode_stream
bank=graphics_bank(gfx,1);f=bank['frames'][59];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128)
a=np.array(Image.open(D/'bank1_059.png'));ea=np.array(Image.open(D/'bank1_060.png'));_,b,_=original(59)
head=np.zeros_like(a,bool);hx,hy=-12-b[0],-25-b[1];head[hy:hy+19,hx:hx+23]=front!=0
pairs={15:12,12:15,7:3,3:7,9:11,11:9,10:6,6:10};candidates=[]
for y,x in np.argwhere((a!=0)&~head):
 v=int(a[y,x]);target=pairs.get(v)
 if target is None or x==0 or y==0 or x==a.shape[1]-1 or y==a.shape[0]-1:continue
 region=a[y-1:y+2,x-1:x+2]
 if np.count_nonzero(region==target)<4 or np.count_nonzero(region==v)>2:continue
 trial=a.copy();trial[y,x]=target
 packed=edit_frame_set(raw.data,f['tile_count'],[(composition_frame(parts,5,59),trial.tobytes(),(a.shape[1],a.shape[0])),(composition_frame(parts,5,60),ea.tobytes(),(ea.shape[1],ea.shape[0]))])
 size=len(encode_stream(packed))
 candidates.append({'world':[int(x+b[0]),int(y+b[1])],'from':v,'to':target,'encoded_bytes':size})
 if size<=raw.end-f['offset']:break
(D/'budget_probe.json').write_text(json.dumps(candidates,indent=2));print(json.dumps(candidates))
