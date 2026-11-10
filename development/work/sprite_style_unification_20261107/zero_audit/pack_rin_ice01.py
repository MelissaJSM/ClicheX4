"""빙열참 4원화와 검증된 평행이동/동일 사본을 고정 은행 안에 패킹한다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_after122 as shared
engine=shared.engine;ROOT=engine.ROOT
P=D/'rin_extension/prepared_saber_followup05_v2/PL01_U.ARC';SHA='0f6665a4cca930edf7e90351b8a8ac044b23326b19836eaa52d473b1b2390941'
A=D/'rin_extension/ice_registered_v1';O=D/'rin_extension/prepared_ice01'
TRANSLATIONS={133:(133,0,0),134:(133,0,-1),135:(135,0,0),136:(133,0,-1),137:(133,0,-1),138:(138,0,0),**{n:(139,0,0)for n in range(139,144)}}
MAP={(1,n):(1,v[0])for n,v in TRANSLATIONS.items()}
REG=json.loads((A/'registration.json').read_text('utf8'));HASHES={r['key']:r['output_sha256']for r in REG['records']};assert REG['source_arc_sha256']==SHA

def targets(arc):
 engine.native.need(engine.native.sha(arc)==SHA,'Wrong working source')
 masters={}
 for key,h in HASHES.items():
  p=A/(key+'_indices.png');engine.native.need(engine.native.sha(p.read_bytes())==h,'Changed registered art');a=np.array(Image.open(p));engine.native.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Invalid indexed source');masters[int(key[3:])]=a
 tt={}
 for n,(m,dx,dy)in TRANSLATIONS.items():
  old=engine.native.render(arc,1,5,n)[0];ref=engine.native.render(arc,1,5,m)[0];engine.native.need(np.array_equal(old,engine.shifted(ref,dx,dy)),'Exact source alias changed');tt[1,n]=engine.shifted(masters[m],dx,dy)
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
 tt=shared.configure(arc);engine.CACHE=D/'rin_extension/ice_pack_cache_v1';engine.pack_frame=pack;return tt

def main():
 assert not O.exists(),'Use a fresh output'
 assert engine.native.sha((D/'rin_extension/ice_detail01/generated.png').read_bytes())=='e26e32c9dddb8c37088e23ef6f6de271ad08657846643e47d09927e38c854b73'
 arc=P.read_bytes();tt=configure(arc);out,proof=engine.build(arc,tt);again,_=engine.build(arc,tt);assert out==again
 for k in('heads_preserved_pixels_per_reference','source_3rd_saber9_and_rear28_preserved'):proof.pop(k,None)
 for r in proof['changes']:r.pop('head_preserved',None)
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:(0,0,0)for k in MAP};engine.boards(arc,out)
 recipe=json.loads((P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=engine.native.sha(engine.native.entry(out,3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,O/f)
 rp=O/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((O/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in MAP],'shared_support_refs':[f'b{b}_{n:03}'for b,n in tt if(b,n)not in MAP],'native_master_sha256':HASHES,'registration':str((A/'registration.json').relative_to(ROOT)),'source_generated_sha256':{'ice_detail01':'e26e32c9dddb8c37088e23ef6f6de271ad08657846643e47d09927e38c854b73'},'cumulative_main_refs':191,'previous_frozen_art_refs':180,'verification':proof,'static_body_patch':{'recipe':str(rp.relative_to(ROOT)),'sha256':engine.native.sha(rp.read_bytes())},'reproducible':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':REG['scope']}
 (O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':j['after_sha256'],'layouts':proof['layouts']}))
if __name__=='__main__':main()
