from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame,decode_stream
D=Path(__file__).parent/'rin_extension';a=(D/'prepared_ride_heads02/PL01_U.ARC').read_bytes();g=entry(a,2);p=entry(a,3);j=json.loads((D/'chaser_detail01/inputs.json').read_text('utf8'));reports=[]
for m in j['masters']:
 n=m['ref'];c=composition_frame(p,5,n);fs=graphics_bank(g,1)['frames'];f=fs[n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;v=np.array(Image.open(D/'chaser_contacts_probe_v1'/f'b1_{n:03}_body_indices.png'));cover=np.zeros((384,384),bool);ps=[q for q in c['parts']if q['tile']in m['body_tiles']]
 for q in ps:cover[160+q['y']:176+q['y'],160+q['x']:176+q['x']]=True
 bad=(v>0)&~cover;reports.append({'ref':n,'outside_existing_windows':int(bad.sum()),'outside_cells':np.argwhere(bad)[:,::-1].tolist(),'parts':[{k:q[k]for k in('tile','x','y','flip_x','flip_y','flags')}for q in ps]})
(D/'chaser_contacts_probe_v1/pack_inspection.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(reports))
