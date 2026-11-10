"""용염인 진입 준비144와 8방향 회전을 고정 뱅크에 패킹한다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_after122 as shared
engine=shared.engine;ROOT=engine.ROOT
P=D/'rin_extension/prepared_ice01/PL01_U.ARC';SHA='70b483ba78dedefa9c4af45c9b4c5fe4fb8ef915290a4c92c1dd5dea6b0b01d8'
A=D/'rin_extension/ice_spin_registered_v1';O=D/'rin_extension/prepared_spin01'
ROTATIONS={161:(161,0),163:(163,0),165:(161,1),167:(163,1),169:(161,2),171:(163,2),173:(161,3),175:(163,3)}
MAP={(1,n):(1,m)for n,(m,k)in ROTATIONS.items()};MAP[1,144]=(1,144)
REG=json.loads((A/'registration.json').read_text('utf8'));HASHES={r['key']:r['output_sha256']for r in REG['records']};assert REG['source_arc_sha256']==SHA
def rotated(a,k):
 engine.native.need(not a[320:,:].any()and not a[:,320:].any(),'Rotation outside pivot canvas');z=np.zeros_like(a);z[:320,:320]=np.rot90(a[:320,:320],k);return z
def targets(arc):
 engine.native.need(engine.native.sha(arc)==SHA,'Wrong working source');masters={}
 for key,h in HASHES.items():
  p=A/(key+'_indices.png');engine.native.need(engine.native.sha(p.read_bytes())==h,'Changed registered art');a=np.array(Image.open(p));engine.native.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Invalid indexed source');masters[int(key[3:])]=a
 relation=json.loads((D/'rin_extension/ice_spin02/source_rotation_relations.json').read_text('utf8'));engine.native.need(relation['source_sha256']==SHA,'Changed rotation evidence')
 for row in relation['rows']:
  actual=engine.native.render(arc,1,5,row['ref'])[0];rr=rotated(engine.native.render(arc,1,5,row['master'])[0],row['quarter_turns']);engine.native.need(int((actual!=rr).sum())==row['changed_pixels'],'Source rotation relationship changed')
 tt={(1,n):rotated(masters[m],k)for n,(m,k)in ROTATIONS.items()};tt[1,144]=masters[144]
 bank=engine.native.graphics_bank(engine.native.entry(arc,2),1)
 for b,n in list(tt):
  off=bank['frames'][n]['offset']
  for f in bank['frames']:
   k=1,f['index']
   if f['offset']==off and k not in tt:
    engine.native.need(not 42<=k[1]<=49,'Partial group');tt[k]=engine.native.render(arc,1,5,k[1])[0].copy()
 return tt
def pack(c,b,n,raw,count,target):
 nr,rr,proof=shared.joint(c,b,n,raw,count);return nr,rr[n],proof
def configure(arc):
 shared.P=P;shared.SHA=SHA;shared.A=A;shared.O=O;shared.MAP=MAP;shared.HASHES=HASHES;shared.JOINT.clear();shared.GROUPS.clear();shared.targets=targets
 tt=shared.configure(arc);engine.CACHE=D/'rin_extension/spin_pack_cache_v1';engine.pack_frame=pack;return tt
def main():
 assert not O.exists(),'Use a fresh output'
 assert engine.native.sha((D/'rin_extension/ice_spin02/generated.png').read_bytes())=='ad1bde14dfc0979dbeab30f6534e50935d8182356d61b2b331c68539a8b1b035'
 arc=P.read_bytes();tt=configure(arc);out,proof=engine.build(arc,tt);again,_=engine.build(arc,tt);assert out==again
 for k in('heads_preserved_pixels_per_reference','source_3rd_saber9_and_rear28_preserved'):proof.pop(k,None)
 for r in proof['changes']:r.pop('head_preserved',None)
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:(0,0,0)for k in MAP};engine.boards(arc,out)
 recipe=json.loads((P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=engine.native.sha(engine.native.entry(out,3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,O/f)
 rp=O/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((O/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in MAP],'shared_support_refs':[f'b{b}_{n:03}'for b,n in tt if(b,n)not in MAP],'native_master_sha256':HASHES,'registration':str((A/'registration.json').relative_to(ROOT)),'source_generated_sha256':{'ice_spin02':'ad1bde14dfc0979dbeab30f6534e50935d8182356d61b2b331c68539a8b1b035'},'cumulative_main_refs':200,'previous_frozen_art_refs':191,'verification':proof,'rotation_pivot':[159.5,159.5],'nonexact_original_rotation_normalized_refs':[167,171],'static_body_patch':{'recipe':str(rp.relative_to(ROOT)),'sha256':engine.native.sha(rp.read_bytes())},'reproducible':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':REG['scope']+' 新167/171은 원래 대각선18/15px 차이의 복제가 아니라 새163 정회전 미술 통일. 기존 다른 검기/부분VRAM/정적효과를 보존.'}
 (O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':j['after_sha256'],'layouts':proof['layouts']}))
if __name__=='__main__':main()
