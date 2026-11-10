from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parent;ROOT=W.parents[1];D=H/'prepared01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
write=lambda p,r:p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 assert not(D/'FROZEN.json').exists();candidate='55b5d04d9a3452f2f12fe5ab21024de58c61f43eaa8b078f873ce4c7d2182f52';assert sha(D/'ST0E_U1.ARC')==candidate
 for lock in('PREPARED_LOCK.json','INPUT_LOCK.json'):
  for row in read(D/lock)['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
 ip=W/'zero_audit/nana_selection8_spares_independent01/report.json';vp=ip.with_name('visual_review.json');lp=ip.with_name('READER_LOCK.json');rp=W/'root_review_checkpoint141.json';gp=W/'selection_standing_v5_checks.json'
 hashes=['a33f6e30a12e252fdb4415dab8ceca47a7244bbda689fc6a82be62925c10ffb2','f270b1882dcaba2d9deb2d9f0e394281b10d0c49fe8af095a79b622d497b0592','27104a2f22472f98f77b248bd544ce78803f20200a75185ec7e4c29554d68db9','f108472291114de909b214ef10a8a54098cdb40fbb83bf4358aa3c7cd30edca9','378cae09f9fd41b5b212fb24635b0892fb658db56135a287f6f246bfd7542478']
 for path,digest in zip((ip,vp,lp,rp,gp),hashes):assert sha(path)==digest,str(path)
 ind,vis,root,guard=map(read,(ip,vp,rp,gp))
 assert ind['passed']and ind['candidate_sha256']==candidate and ind['new_game_sha256']=='8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10'
 for name,digest in ind['inputs'].items():assert sha(ROOT/name)==digest,name
 assert ind['counts']=={'all_UI_frames':80,'non_target_records':1204,'non_target_UI_frames':72,'non_target_X_UI_frames':17,'target_UI_frames':8}
 assert ind['shared5_preserved']==[0,1,2,16,17] and len(ind['additional14_used'])==14
 for key in('all_other155_whole_tiles_exact','other_texture_prefix90112_exact','all_entry_and_bank_boundaries_unchanged','non_target_geometry_records_RGBA_exact','RN_return19_20_dy0_and_Zero_banks_preserved'):assert ind[key]
 assert len(root['actually_viewed_files'])==8 and len(vis['actually_viewed_sheets'])==4
 for row in root['actually_viewed_files']+vis['actually_viewed_sheets']:assert sha(ROOT/row['path'])==row['sha256']
 assert guard['passed']and len(guard['refusals'])==7 and guard['candidate_sha256']==candidate and guard['builder_sha256']==sha(ROOT/'scripts/build_sprite_style_selection_v5.py')
 proof={'passed':True,'candidate_sha256':candidate,'parent_selection_sha256':ind['parent_sha256'],'new_game_sha256':ind['new_game_sha256'],'refs':list(range(1,9)),'all_eight_origins_identity':True,'identical_builds':2,'counts':ind['counts'],'used_exclusive_tiles':39,'used_previously_unconsumed_tiles':ind['additional14_used'],'shared5_exact':True,'other155_tiles_exact':True,'target_GPU_parts':58,'entry_sizes_offsets_and_bank_bounds_exact':True,'root_actual_sheets':8,'independent_actual_sheets':4,'v5_guard_refusals':7,'evidence':[bound(p)for p in(ip,vp,lp,rp,gp,D/'proposal.json',D/'INPUT_LOCK.json',D/'PREPARED_LOCK.json',Path(__file__))],'new_candidate_MIPS_executed':False,'original_capacity_loader_initializers_executed':True,'runtime_verified':False,'whole_project_complete':False,'pending_flags_superseded':True}
 write(D/'final_verification.json',proof)
 write(D/'FROZEN.json',{'frozen':True,'candidate_sha256':candidate,'parent_selection_sha256':ind['parent_sha256'],'new_game_sha256':ind['new_game_sha256'],'files':{p.name:sha(p)for p in sorted(D.iterdir())if p.is_file()},'independent_and_guard_passed':True,'whole_project_complete':False,'runtime_verified':False,'pending_flags_superseded':True})
 print(json.dumps({'frozen':sha(D/'FROZEN.json'),'verification':sha(D/'final_verification.json')}))
if __name__=='__main__':main()
