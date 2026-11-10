"""첫4 질풍아 원화의 공유 검기 타일 보존·고정 은행 수용성만 시험한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).parent;sys.path.insert(0,str(D));import pack_rin_after122 as shared
engine=shared.engine;P=D/'rin_extension/prepared_ladder_dash01/PL01_U.ARC';SHA='c2ec4099740eb77cca2d37e4b0f997728e1748a35e47b45475289725ec1dd09b'
A=D/'rin_extension/dash_saber_followup01/registered_probe_v2';O=D/'rin_extension/dash_saber_first_pack_probe';MAP={(0,n):(0,n)for n in(158,160,162,164)}
reg=json.loads((A/'registration.json').read_text('utf8'));HASHES={r['key']:r['indices_sha256']for r in reg['records']}
def targets(arc):
 engine.native.need(engine.native.sha(arc)==SHA,'Wrong parent');tt={}
 for key,h in HASHES.items():
  p=A/(key+'_indices.png');engine.native.need(engine.native.sha(p.read_bytes())==h,'Changed art');v=np.array(Image.open(p));engine.native.need(v.shape==(384,384)and v.dtype==np.uint8 and v.max()<=15,'Invalid native');tt[int(key[1]),int(key[3:])]=v
 for b,n in list(tt):
  bank=engine.native.graphics_bank(engine.native.entry(arc,2),b);off=bank['frames'][n]['offset']
  for f in bank['frames']:
   if f['offset']==off and(b,f['index'])not in tt:tt[b,f['index']]=engine.native.render(arc,b,b*5,f['index'])[0].copy()
 return tt
def pack(c,b,n,raw,count,target):
 nr,rr,proof=shared.joint(c,b,n,raw,count);return nr,rr[n],proof
def configure(arc):
 shared.P=P;shared.SHA=SHA;shared.A=A;shared.O=O;shared.MAP=MAP;shared.HASHES=HASHES;shared.JOINT.clear();shared.GROUPS.clear();shared.targets=targets
 tt=shared.configure(arc);engine.CACHE=D/'rin_extension/dash_saber_pack_probe_cache';engine.pack_frame=pack;return tt
if __name__=='__main__':
 assert not O.exists(),'Use new output';arc=P.read_bytes();tt=configure(arc);out,proof=engine.build(arc,tt)
 for k in('heads_preserved_pixels_per_reference','source_3rd_saber9_and_rear28_preserved'):proof.pop(k,None)
 for r in proof['changes']:r.pop('head_preserved',None)
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out);(O/'probe.json').write_text(json.dumps({'candidate_sha256':engine.native.sha(out),'source_sha256':SHA,'verification':proof,'diagnostic_only':True,'game_changed':False,'frozen':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':engine.native.sha(out),'layouts':proof['layouts']}))
