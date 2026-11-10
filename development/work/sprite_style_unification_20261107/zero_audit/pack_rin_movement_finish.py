"""Bind three new movement masters without modifying timing or other poses."""
from pathlib import Path
import sys,json,hashlib,shutil
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_wall_followup as previous
core=previous.core
core.P=D/'rin_extension/prepared_wall_followup_v2/PL01_U.ARC';core.SHA='289370272eb51e377435e3fea0591921f4497fe3774d1f41e1d15d4d76d22ca2'
core.ART=D/'rin_extension/movement_finish_registered_v1';core.OUT=D/'rin_extension/prepared_movement_finish_v1'
core.EXPECTED_SHA={'b0_037':'45199064f330231d73d6b5497828a6456e6b876a94ea0e5cf281a5ef43bf68c1','b0_045':'da21567b5fa6f73663c651976917117d6104f50b828cb426c232f8b4ecac19f4','b0_193':'f7e1b1d3070e3bc3fa786941bf0adedea82312dcf73ccb7f3cc3a0b8b5698915'}
core.MAP={(0,n):(f'b0_{n:03}',False)for n in(37,45,193)};previous.shared.CACHE=D/'rin_extension/movement_finish_pack_cache_v1'
def main():
 assert not core.OUT.exists(),'Use a separate candidate path'
 assert hashlib.sha256((D/'rin_extension/movement_finish01/generated.png').read_bytes()).hexdigest()=='f5567cc3bc73e52cf1de0d66a5f98a9cafbc0e4efcc8d39e2b1bdac7ce2bfc75'
 core.main();p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'))
 j['cumulative_main_refs']=100;j['previous_frozen_art_refs']=97;j['verification'].pop('previous42_exact',None);j['verification']['previous97_exact']=True
 j.update({'static_burst24_sync_required':False,'static_burst23_sync_required':False,'victory5_included':True,'user_accepted':False,'root_review_only':True,'root_review_pending':True,'registration':str((core.ART/'registration.json').relative_to(core.ROOT)),'native_master_sha256':core.EXPECTED_SHA,'scope':'벽차기37·대시 전환45·사다리 꼭대기193 새3몸체. 기존97·타이밍·다른효과·부분8·정적몸체 보존.','ready_for_checkpoint_integration':False})
 recipe=json.loads((core.P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=core.engine.native.sha(core.engine.native.entry((core.OUT/'PL01_U.ARC').read_bytes(),3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(core.P.parent/f,core.OUT/f)
 rp=core.OUT/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8');j['static_body_patch']={'recipe':str(rp.relative_to(core.ROOT)),'sha256':hashlib.sha256(rp.read_bytes()).hexdigest()};j['static_body_images_and_texture_unchanged_from97']=True
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':str(core.OUT),'sha256':j['after_sha256'],'count':100}))
if __name__=='__main__':main()
