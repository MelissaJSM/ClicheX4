"""New five victory poses and source-pose synchronized departure flashes."""
from pathlib import Path
import sys,json,hashlib,shutil
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_rear_continuation as shared
core=shared.core
core.P=D/'rin_extension/prepared_rising_rear_v1/PL01_U.ARC';core.SHA='223e553f97ecc85d52b085f3e0e6cd46ecc914063f1adcef43fd1d34c25d298e'
core.ART=D/'rin_extension/victory_targets_v1';core.OUT=D/'rin_extension/prepared_victory_details_v1'
core.EXPECTED_SHA={'b1_001':'c81e948cf736f3ea3d268f0eb6c3317890987322b06dc896cc112ebac07460cc','b1_002':'475982f79d685df5b5ccf82e242ed3789c34a6440fdc2df6ed3f97a6f4ece2de','b1_003':'9514b6073047669eecd4d88a3319c345c0a8bd52f6872c90106f5fa58355b3d1','b1_004':'c024927198dd2c3a9beb279546ba047a40b528fc66f6d1b84ee1c88dea4ff3ca','b1_006':'4cf50db05c5f763ece0786a8e5be746fed819dd6d97caf6c747bea75461a3e06','b1_007':'0d30e30a0154527ecc0466fe1bb140c29bcd40c5bbb56aabf713f7f45026e5ad','b1_008':'0bc625ab98ee0a1480ee23e82a8893861b448267b426084312b00fd1d5911b18'}
core.MAP={(1,n):(f'b1_{n:03}',False)for n in(1,2,3,4,6,7,8)};shared.CACHE=D/'rin_extension/victory_details_pack_cache_v1'
def main():
 assert not core.OUT.exists(),'Choose a new candidate output'
 for folder,h in [('victory_detail01','1db69b93d93ee61e121a156557df87a77c0218f5d772d4f320c0b28b86421719'),('victory_detail02','0fc788eb53bc774697af9b5b7167d07457eebce27d01973fb941a5203ec6d956')]:assert hashlib.sha256((D/'rin_extension'/folder/'generated.png').read_bytes()).hexdigest()==h
 core.main();p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'));j['cumulative_main_refs']=91;j['previous_frozen_art_refs']=84;j['verification'].pop('previous42_exact',None);j['verification']['previous84_exact']=True
 assert set(j['shared_support_refs'])=={'b1_000','b1_005','b1_009'}
 j.update({'static_burst24_sync_required':False,'static_burst23_sync_required':False,'victory5_included':True,'victory5_preserved_from_parent':True,'user_accepted':False,'root_review_only':True,'root_review_pending':True,'registration':str((D/'rin_extension/victory_registered_v1/registration.json').relative_to(core.ROOT)),'targets_provenance':str((core.ART/'targets.json').relative_to(core.ROOT)),'native_master_sha256':core.EXPECTED_SHA,'scope':'승리1/2/3/4/6 새5몸체와3에서파생한귀환섬광7/8 동기화. 대기0·수용5·순수빛9..13·이전84 보존.','authored_body_refs':[1,2,3,4,6],'derived_main_flash_refs':[7,8]})
 recipe=json.loads((core.P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=core.engine.native.sha(core.engine.native.entry((core.OUT/'PL01_U.ARC').read_bytes(),3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(core.P.parent/f,core.OUT/f)
 rp=core.OUT/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8');j['static_body_patch']={'recipe':str(rp.relative_to(core.ROOT)),'sha256':hashlib.sha256(rp.read_bytes()).hexdigest()};j['static_body_images_and_texture_unchanged_from84']=True
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':str(core.OUT),'sha256':j['after_sha256'],'count':91}))
if __name__=='__main__':main()
