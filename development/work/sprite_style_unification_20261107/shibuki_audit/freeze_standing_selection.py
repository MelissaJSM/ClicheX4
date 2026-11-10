"""선택1..8 원화복사·고정atlas·독립·v4범위검사를 결속하여 동결."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];W=H.parent;sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
FINAL='47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'
def read(p):return json.loads(p.read_text('utf8'))
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    d=H/'prepared_selection_standing01';need(not(d/'FROZEN.json').exists(),'동결본 보호')
    for name in('PREPARED_LOCK.json','INPUT_LOCK.json'):
        for r in read(d/name)['files']:need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'잠금불일치 '+r['path'])
    need(sha((d/'ST0E_U1.ARC').read_bytes())==FINAL,'ARC 변경')
    ip=W/'zero_audit/shibuki_selection8_independent01/report.json';vp=ip.with_name('visual.json');rp=W/'root_review_checkpoint139.json';gp=W/'selection_standing_v4_checks.json'
    for p,s in [(ip,'7c34becccbda504df4040fbdcbda68b82d383a2a88172756fb47a08500b6b26e'),(vp,'371583a63a5c6507573111a465f7287866b1a49da2af8cfab09b50da5b786126'),(rp,'33d7c93a4a2b6bb7acfbd6c3d511c918fe3a39ae5252a5468de668ab7ac1c128'),(gp,'283c71ebb2ae89c95dbc7abd8783f32dfa43ec238df0c0c2feb98521d612e6e4')]:need(sha(p.read_bytes())==s,'근거변경 '+str(p))
    ind,vis,root,guard=map(read,(ip,vp,rp,gp));p=read(d/'proposal.json');source=read(ROOT/p['source_report']['path'])
    need(ind['passed']and ind['candidate_sha256']==FINAL and ind['parent_sha256']==p['parent']['sha256']and ind['new_game_sha256']==p['game_new']['sha256'],'독립결속')
    need(ind['counts']=={'all_UI_frames':80,'non_target_records':1194,'non_target_UI_frames':72,'non_target_X_UI_frames':17,'target_UI_frames':8,'target_GPU_parts':52,'flipped_target_parts':20},'독립범위')
    need(ind['protected_shared_blank_tile4_exact']and ind['other_entries_and_bank_bounds_exact']and ind['other_parts_banks_byte_exact'],'비대상보존')
    need(len(ind['changed_tiles'])==48 and ind['nonowned_whole_tiles_exact']==159 and all(r['safe_UV_endpoint']for r in ind['GPU_parts']),'타일/GPU')
    need(root['candidate_sha256']==FINAL and len(root['actually_viewed_files'])==8,'루트실제8판')
    for r in root['actually_viewed_files']:need(r['actually_viewed']and sha((ROOT/r['path']).read_bytes())==r['sha256'],'열람판 변경')
    need(vis['candidate_sha256']==FINAL and vis['report_sha256']==sha(ip.read_bytes())and len(vis['actually_viewed'])==4,'독립실제4판')
    for name in vis['actually_viewed']:
        r=next(r for r in ind['readback_sheets']if Path(r['path']).name==name);need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'독립판변경')
    need(guard['passed']and guard['candidate_sha256']==FINAL and len(guard['refusals'])==6 and guard['checked_standing_refs']==list(range(1,9)),'v4범위')
    builder=ROOT/'scripts/build_sprite_style_selection_v4.py';need(sha(builder.read_bytes())==guard['builder_sha256'],'빌더 변경')
    need(p['reproduction']['identical_builds']==2 and source['palette_proof']['COL_entry5_row16_matches_game_CLUT0'],'재현/팔레트')
    evidence=[d/'proposal.json',d/'PREPARED_LOCK.json',d/'INPUT_LOCK.json',ROOT/p['source_report']['path'],ip,vp,rp,gp,builder,d/'visual_review.json',Path(__file__)]
    proof={'passed':True,'candidate_sha256':FINAL,'parent_selection_sha256':p['parent']['sha256'],'new_game_sha256':p['game_new']['sha256'],'mapping':p['mapping'],'evidence':[ev(x)for x in evidence],'counts':ind['counts'],'whole_UI_bank_count':80,'target_only_atlas_tiles':48,'shared_blank_tile4_exact':True,'all_bank_bounds_and_entry_lengths_exact':True,'other_17_X_selection_displays_exact':True,'source_game_pixels_and_UI_origins_exact':True,'original_part_counts_preserved':False,'historical_parts':63,'new_parts':52,'new_game_art_changed':False,'identical_builds':2,'root_guard_refusals':6,'root_actual_sheets':8,'author_actual_sheets':8,'independent_actual_sheets':4,'builder_v4_checks_passed':True,'independent_reading_passed':True,'new_MIPS_executed':False,'runtime_verified':False,'user_accepted':False,'whole_project_complete':False,'limits':['선택1..8의새몸체복사만동결한다.타아머/게임본체/타이밍변경없음.','원조립63개를새52개로바꾸고물리반전타일을공유했지만전체RGBA/원점은동일하다.','v4범위검사·GPU끝점/독립읽기를통과했으며이번UI후보의새MIPS나실제선택화면검사는아직수행하지않았다.','Ultimate85..92의상·차량/호버및거부135 등전체미술잔여는계속남아있다.'],'initial_prepared_pending_flags_superseded':True}
    write(d/'final_verification.json',proof);write(d/'FROZEN.json',{'frozen':True,'candidate_sha256':FINAL,'parent_selection_sha256':p['parent']['sha256'],'new_game_sha256':p['game_new']['sha256'],'files':{x.name:sha(x.read_bytes())for x in sorted(d.iterdir())if x.is_file()and x.name!='FROZEN.json'},'selection_bank':2,'references':list(range(1,9)),'independent_and_v4_guard_passed':True,'root_actual_sheets':8,'new_MIPS_executed':False,'runtime_verified':False,'user_accepted':False,'whole_project_complete':False,'initial_pending_flags_superseded':True})
    print(json.dumps({'FROZEN':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json')}))
if __name__=='__main__':main()
