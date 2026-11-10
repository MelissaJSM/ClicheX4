"""등장5 새원화의 기존타일창·공유 범위를 쓰기 없이 점검한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_frame_edit import frame_coverage
R=Path(__file__).parent/'rin_extension';arc=(R/'prepared_chaser01/PL01_U.ARC').read_bytes();g=entry(arc,2);p=entry(arc,3);fs=graphics_bank(g,0)['frames'];rows=[]
for n in range(247,254):
 f=fs[n];c=composition_frame(p,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cov,sz,bb=frame_coverage(raw,f['tile_count'],c);mask=np.zeros((384,384),bool);mask[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.array([bool(v)for v in cov]).reshape(sz[1],sz[0]);bad=[]
 if n>=249:
  a=np.array(Image.open(R/f'arrival_contacts_probe_v3/b0_{n:03}_indices.png'));bad=np.argwhere((a>0)&~mask)[:,::-1].tolist()
 rows.append({'ref':n,'count':f['tile_count'],'shared_refs':[h['index']for h in fs if h['offset']==f['offset']],'parts':[{k:q[k]for k in('index','tile','x','y','flags','flip_x','flip_y','record_offset')}for q in c['parts']],'bad_world_xy':bad,'size':sz,'bounds':bb})
(R/'arrival_pack_probe.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
