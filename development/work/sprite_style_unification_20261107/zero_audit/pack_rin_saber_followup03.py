"""Rin air-saber four masters plus exact spin-entry alias, bounded native ARC."""
from pathlib import Path
import sys,json,shutil
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_after122 as shared
engine=shared.engine;ROOT=engine.ROOT
P=D/'rin_extension/prepared_air_saber02/PL01_U.ARC';SHA='9dc63497fbc367cd7330e0c4337bb208b75cee76f2ecbbf0faaaa72b73ee66a4'
A=D/'rin_extension/saber_followup03_registered_v1';O=D/'rin_extension/prepared_saber_followup03'
MAP={(0,n):(0,n)for n in[229,230,232,234]};MAP[1,132]=(0,229)
REG=json.loads((A/'registration.json').read_text('utf8'));HASHES={r['key']:r['output_sha256']for r in REG['records']};assert REG['source_arc_sha256']==SHA
def configure(arc):
 shared.P=P;shared.SHA=SHA;shared.A=A;shared.O=O;shared.MAP=MAP;shared.HASHES=HASHES;shared.JOINT.clear();shared.GROUPS.clear()
 tt=shared.configure(arc);engine.CACHE=D/'rin_extension/air_saber_pack_cache_v1';return tt
def main():
 assert not O.exists(),'Use a new output'
 artsha='be9f76899f4aefce5655b28d8e7161aa6f7ba2e641266ce45cf8b3acc20ebb9d';assert engine.native.sha((D/'rin_extension/saber_followup03/generated.png').read_bytes())==artsha
 arc=P.read_bytes();tt=configure(arc);out,proof=engine.build(arc,tt);again,_=engine.build(arc,tt);assert out==again
 for k in('heads_preserved_pixels_per_reference','source_3rd_saber9_and_rear28_preserved'):proof.pop(k,None)
 for r in proof['changes']:r.pop('head_preserved',None)
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:(0,0,0)for k in MAP};engine.boards(arc,out)
 recipe=json.loads((P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=engine.native.sha(engine.native.entry(out,3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,O/f)
 rp=O/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((O/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in MAP],'shared_support_refs':[f'b{b}_{n:03}'for b,n in tt if(b,n)not in MAP],'native_master_sha256':HASHES,'registration':str((A/'registration.json').relative_to(ROOT)),'source_generated_sha256':{'saber_followup03':artsha},'cumulative_main_refs':168,'previous_frozen_art_refs':163,'verification':proof,'static_body_patch':{'recipe':str(rp.relative_to(ROOT)),'sha256':engine.native.sha(rp.read_bytes())},'reproducible':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':'공중검격213/215/217/219 새4원화와 원래 전신 동일한회전준비b1_160. 이전154·검기·부분VRAM·정적몸체 보존. 아직 미술·독립·원MIPS 확인 전.'}
 (O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':j['after_sha256'],'layouts':proof['layouts']}))
if __name__=='__main__':main()
