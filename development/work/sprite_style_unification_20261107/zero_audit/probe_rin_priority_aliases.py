"""Find exact complete-pose copies, including original native reflection."""
from pathlib import Path
import sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;R=D/'rin_extension'
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank
arc=(R/'prepared_air_continuation2_v2/PL01_U.ARC').read_bytes()
def cut(a):
 y,x=np.nonzero(a)
 if not len(x):return None
 box=(int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1)
 return a[box[1]:box[3],box[0]:box[2]],box
poses={}
for b in (0,1):
 for f in graphics_bank(entry(arc,2),b)['frames']:
  n=f['index']
  if b==1 and 42<=n<=49:continue
  got=cut(render(arc,b,b*5,n)[0])
  if got:poses[b,n]=got
out=[]
for key in[(0,61),(0,174),(1,5),(1,183)]:
 master,box=poses[key];hits=[]
 for (b,n),(a,bb)in poses.items():
  for flipped in (False,True):
   if np.array_equal(np.fliplr(master)if flipped else master,a):
    hits.append({'bank':b,'ref':n,'flip_x':flipped,'origin_xy':[bb[0],bb[1]],'master_crop':list(box),'native_offset_from_master':[bb[0]-box[0],bb[1]-box[1]]})
 out.append({'key':list(key),'exact_complete_aliases':hits})
(R/'detail_priority_singles/exact_aliases.json').write_text(json.dumps(out,indent=2)+'\n','utf8');print(json.dumps(out))
