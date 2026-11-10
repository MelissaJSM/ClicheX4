"""낙봉파9의 입력·공유/타일창 상태를 읽기 검사한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_frame_edit import frame_coverage
R=D/'rin_extension';arc=(R/'prepared_arrival01/PL01_U.ARC').read_bytes();g=entry(arc,2);p=entry(arc,3);fs=graphics_bank(g,1)['frames'];rows=[]
def targets():
 expected={177:'dc15fb38bcdac12e50d6e4c4a403d1eb83e7b3b3cd468633520354557411e078',178:'1c727254e5d123dfb71d4299acb272789eed25d41815f637564affa5fb31682d',179:'c81eeae791dfe5c339882a7dd829d5ce967225302feab3aa24951a71ddc0190b',180:'316d7ee7faf3be92ee246e8548ede084ba29c4e7df31442bb8505d85acda8ce8',181:'3a2ddc7867a70328d8ccbe1d3f1d8e1e167bc5ec048d222f28862a250a50a77f',186:'69c311a56e8fabf11ca25eb4d96359234e1953d051442531cf33b1d6898fac5b',187:'69c311a56e8fabf11ca25eb4d96359234e1953d051442531cf33b1d6898fac5b',188:'589e6bbef1d5140cebc7745d50cb7446a1b9f500e4cb093398ceed758c6b2055',189:'ed94f901c920ec311b6a6e29b3f3f954da8abf9efdf0bdc6bbff63589bbb3da2'}
 paths={177:R/'burst177_reuse_probe01/b1_177_combined_indices.png'}
 paths.update({n:R/'burst_charge_registered_v1'/f'b1_{n:03}_combined_indices.png'for n in range(178,182)})
 paths.update({n:R/'burst_recovery_registered_v1'/f'b1_{n:03}_body_indices.png'for n in range(186,190)})
 tt={}
 for n,p in paths.items():
  assert hashlib.sha256(p.read_bytes()).hexdigest()==expected[n],('Changed registered art',n)
  tt[n]=np.array(Image.open(p))
 return tt
if __name__=='__main__':
 for n,z in targets().items():
  f=fs[n];c=composition_frame(p,5,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cov,sz,bb=frame_coverage(raw,f['tile_count'],c);mask=np.zeros((384,384),bool);mask[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.array([bool(v)for v in cov]).reshape(sz[1],sz[0]);bad=np.argwhere((z>0)&~mask)[:,::-1].tolist();rows.append({'ref':n,'count':f['tile_count'],'shared_refs':[h['index']for h in fs if h['offset']==f['offset']],'parts':[{k:q[k]for k in('index','tile','x','y','flags','flip_x','flip_y','record_offset')}for q in c['parts']],'bad_world_xy':bad})
 (R/'burst_pack_probe.json').write_text(json.dumps(rows,indent=2)+'\n','utf8');print(json.dumps(rows))
