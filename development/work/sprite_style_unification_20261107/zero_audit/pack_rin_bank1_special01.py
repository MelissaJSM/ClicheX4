"""Rin bank1 준비/회복4원화→6참조를 기존 검기 소비타일 보호하며 패킹."""
from pathlib import Path
import sys,json,shutil
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_after122 as shared
engine=shared.engine;ROOT=engine.ROOT
P=D/'rin_extension/prepared_dash_saber01/PL01_U.ARC';SHA='94b24181ee1d6ce463f1647e89f58fcf29c57e8eb8cc6ede457cc46e22fc36da'
A=D/'rin_extension/bank1_special_registered_v1';O=D/'rin_extension/prepared_bank1_special01'
MAP={(1,n):(1,m)for m,ns in[(91,[91]),(93,[93]),(101,[101,103]),(105,[105,107])]for n in ns}
REG=json.loads((A/'registration.json').read_text('utf8'));HASHES={r['key']:r['output_sha256']for r in REG['records']};assert REG['source_arc_sha256']==SHA

def pack(c,b,n,raw,count,target):
 nr,rr,proof=shared.joint(c,b,n,raw,count);return nr,rr[n],proof

def configure(arc):
 shared.P=P;shared.SHA=SHA;shared.A=A;shared.O=O;shared.MAP=MAP;shared.HASHES=HASHES;shared.JOINT.clear();shared.GROUPS.clear()
 tt=shared.configure(arc);engine.CACHE=D/'rin_extension/bank1_special_pack_cache_v1';engine.pack_frame=pack;return tt

def main():
 assert not O.exists(),'Use a new output'
 art=D/'rin_extension/bank1_special01/generated.png';assert engine.native.sha(art.read_bytes())=='63045dd29f76bbed0f8b5e00c72d0cdfac45430dbce50dc0529f18b12c046da7'
 arc=P.read_bytes();tt=configure(arc);out,proof=engine.build(arc,tt);again,_=engine.build(arc,tt);assert out==again
 for k in('heads_preserved_pixels_per_reference','source_3rd_saber9_and_rear28_preserved'):proof.pop(k,None)
 for r in proof['changes']:r.pop('head_preserved',None)
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:(0,0,0)for k in MAP};engine.boards(arc,out)
 recipe=json.loads((P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=engine.native.sha(engine.native.entry(out,3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,O/f)
 rp=O/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((O/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in MAP],'shared_support_refs':[f'b{b}_{n:03}'for b,n in tt if(b,n)not in MAP],'native_master_sha256':HASHES,'registration':str((A/'registration.json').relative_to(ROOT)),'source_generated_sha256':{str(art.relative_to(ROOT)):engine.native.sha(art.read_bytes())},'cumulative_main_refs':228,'previous_frozen_art_refs':222,'verification':proof,'static_body_patch':{'recipe':str(rp.relative_to(ROOT)),'sha256':engine.native.sha(rp.read_bytes())},'reproducible':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':REG['scope']}
 (O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':j['after_sha256'],'layouts':proof['layouts']}))
if __name__=='__main__':main()
