"""용염인 준비/회복과 사다리 진입5참조를 원래 공유 그룹 안에 패킹."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_after122 as shared
engine=shared.engine;ROOT=engine.ROOT
P=D/'rin_extension/prepared_spin01/PL01_U.ARC';SHA='cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a'
A=D/'rin_extension/followthrough_registered_v1';O=D/'rin_extension/prepared_followthrough01'
MAP={(1,146):(1,146),(1,156):(1,156),(1,158):(1,158),(0,197):(0,197),(0,212):(0,197)}
REG=json.loads((A/'registration.json').read_text('utf8'));HASHES={r['key']:r['output_sha256']for r in REG['records']};assert REG['source_arc_sha256']==SHA
def targets(arc):
 engine.native.need(engine.native.sha(arc)==SHA,'Wrong working source');masters={}
 for key,h in HASHES.items():
  p=A/(key+'_indices.png');engine.native.need(engine.native.sha(p.read_bytes())==h,'Changed registered art');a=np.array(Image.open(p));engine.native.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Invalid indexed source');masters[int(key[1]),int(key[3:])]=a
 tt={}
 for(b,n),(mb,m)in MAP.items():
  engine.native.need(np.array_equal(engine.native.render(arc,b,b*5,n)[0],engine.native.render(arc,mb,mb*5,m)[0]),'Source exact alias changed');tt[b,n]=masters[mb,m].copy()
 for b,n in list(tt):
  bank=engine.native.graphics_bank(engine.native.entry(arc,2),b);off=bank['frames'][n]['offset']
  for f in bank['frames']:
   k=b,f['index']
   if f['offset']==off and k not in tt:
    engine.native.need(not(b==1 and 42<=k[1]<=49),'Partial group');tt[k]=engine.native.render(arc,b,b*5,k[1])[0].copy()
 return tt
def pack(c,b,n,raw,count,target):
 nr,rr,proof=shared.joint(c,b,n,raw,count);return nr,rr[n],proof
def configure(arc):
 shared.P=P;shared.SHA=SHA;shared.A=A;shared.O=O;shared.MAP=MAP;shared.HASHES=HASHES;shared.JOINT.clear();shared.GROUPS.clear();shared.targets=targets
 tt=shared.configure(arc);engine.CACHE=D/'rin_extension/followthrough_pack_cache_v1';engine.pack_frame=pack;return tt
def main():
 assert not O.exists(),'Use a fresh output'
 for folder,h in [('followthrough01','039e810e08a9a50b51746f96da7ca3b4149ae9cd10c7ae70b538fc536148f6cf'),('followthrough_contacts_fix01','7e66e058b6c6ad73c2495e49c899501182f5dea2c7344ab5013ef6d5a8faeadc')]:assert engine.native.sha((D/'rin_extension'/folder/'generated.png').read_bytes())==h
 arc=P.read_bytes();tt=configure(arc);out,proof=engine.build(arc,tt);again,_=engine.build(arc,tt);assert out==again
 for k in('heads_preserved_pixels_per_reference','source_3rd_saber9_and_rear28_preserved'):proof.pop(k,None)
 for r in proof['changes']:r.pop('head_preserved',None)
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out)
 import runpy
 runpy.run_path(str(D/'export_rin205_readbacks.py'),run_name='__main__')
 recipe=json.loads((P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=engine.native.sha(engine.native.entry(out,3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,O/f)
 rp=O/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((O/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in MAP],'shared_support_refs':[f'b{b}_{n:03}'for b,n in tt if(b,n)not in MAP],'native_master_sha256':HASHES,'registration':str((A/'registration.json').relative_to(ROOT)),'source_generated_sha256':{'followthrough01':'039e810e08a9a50b51746f96da7ca3b4149ae9cd10c7ae70b538fc536148f6cf','followthrough_contacts_fix01':'7e66e058b6c6ad73c2495e49c899501182f5dea2c7344ab5013ef6d5a8faeadc'},'cumulative_main_refs':205,'previous_frozen_art_refs':200,'verification':proof,'static_body_patch':{'recipe':str(rp.relative_to(ROOT)),'sha256':engine.native.sha(rp.read_bytes())},'reproducible':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':REG['scope']+' 기존200·다른 검기·부분VRAM·정적효과를 보존.'}
 (O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':j['after_sha256'],'layouts':proof['layouts']}))
if __name__=='__main__':main()
