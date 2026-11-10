"""Rin residual ground and movement13: bounded native shared-stream registration."""
from pathlib import Path
import sys,json,shutil
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_after122 as shared
engine=shared.engine;ROOT=engine.ROOT
P=D/'rin_extension/prepared_ground_wall_v1/PL01_U.ARC';SHA='247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6'
A=D/'rin_extension/after141_registered_v2';O=D/'rin_extension/prepared_ground_remaining_v1'
MAP={(0,n):(0,n)for n in[83,85,87,89,91,105,107,130,133,134,3,4]};MAP[0,93]=(0,91)
REG=json.loads((A/'registration.json').read_text('utf8'));HASHES={r['key']:r['output_sha256']for r in REG['records']};assert REG['source_arc_sha256']==SHA
def configure(arc):
 shared.P=P;shared.SHA=SHA;shared.A=A;shared.O=O;shared.MAP=MAP;shared.HASHES=HASHES;shared.JOINT.clear();shared.GROUPS.clear()
 tt=shared.configure(arc);engine.CACHE=D/'rin_extension/after141_pack_cache_v1';return tt
def main():
 assert not O.exists(),'Use a new output'
 art={'ground_second01':'b178ea61d12094a1a9ca0ea07ee7cf601685aa433bb101aaf7b45c4db93ccffb','ground_recovery01':'5205ddf7f4ddf5864b5d4a79d6698f94183e829c49cbdaa77883e01b69c182a6','movement_returns01':'457a644a17a95ca6278ba254152920ff8c3236f3dca0329deed1db10446bf017','recovery130_fix01':'714f4916743715fa8006a3ca89ca3dce8a524be2479291f5bdb03b8d92ab4a74'}
 for folder,h in art.items():assert engine.native.sha((D/'rin_extension'/folder/'generated.png').read_bytes())==h
 arc=P.read_bytes();tt=configure(arc);out,proof=engine.build(arc,tt);again,_=engine.build(arc,tt);assert out==again
 for k in('heads_preserved_pixels_per_reference','source_3rd_saber9_and_rear28_preserved'):proof.pop(k,None)
 for r in proof['changes']:r.pop('head_preserved',None)
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:(0,0,0)for k in MAP};engine.boards(arc,out)
 recipe=json.loads((P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=engine.native.sha(engine.native.entry(out,3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,O/f)
 rp=O/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((O/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in MAP],'shared_support_refs':[f'b{b}_{n:03}'for b,n in tt if(b,n)not in MAP],'native_master_sha256':HASHES,'registration':str((A/'registration.json').relative_to(ROOT)),'source_generated_sha256':art,'cumulative_main_refs':154,'previous_frozen_art_refs':141,'verification':proof,'static_body_patch':{'recipe':str(rp.relative_to(ROOT)),'sha256':engine.native.sha(rp.read_bytes())},'reproducible':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':'지상2타·회복·이동진입의 새12원화와 정확91/93공유. 이전141·검기·부분VRAM·정적몸체 보존. 아직 미술·독립·원MIPS 확인 전.'}
 (O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':j['after_sha256'],'layouts':proof['layouts']}))
if __name__=='__main__':main()
