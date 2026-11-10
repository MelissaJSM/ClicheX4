"""새85..92와 기존18 순열의 원화·원로더·독립·미술 근거 동결."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_standing_fire import validate,P,PARENT,LOCK,LOCK_SHA
FINAL='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def read(p):return json.loads(p.read_text('utf8'))
def images(rows):
    for r in rows:need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'검토그림 변경 '+r['path'])
def main():
    d=H/'prepared_standing_fire_base01';need(not(d/'FROZEN.json').exists(),'동결본 보호');validate(P.read_bytes());lk=read(d/'PREPARED_LOCK.json')
    for n,digest in lk['files'].items():need(sha((d/n).read_bytes())==digest,'준비본 변경 '+n)
    for n,digest in lk['source_scripts'].items():need(sha((H/n).read_bytes())==digest,'제작도구 변경 '+n)
    need(sha((d/'PL00_U.ARC').read_bytes())==FINAL,'ARC 변경')
    ad=H.parent/'zero_audit/shibuki_standing_fire8_independent01';ip=ad/'report.json';vp=ad/'visual_review.json';dp=H.parent/'zero_audit/shibuki_standing_fire_directory_native01/report.json';rp=H.parent/'root_review_checkpoint135.json'
    need(sha(ip.read_bytes())=='dbd043d42eddbe6e944382c826576b6ecf24bc489a7b7a27c907882f684a7e20','독립보고 변경');need(sha(dp.read_bytes())=='185145c45dbdcfbea6ce89ee1f44dd036d9e986b9ea24cdddfd4b9e5d8c92204','로더보고 변경');need(sha(rp.read_bytes())=='59bf9ea7d827f2dc8c3dd7190a3744a80372fbae7836c74726890ed107ace3f8','루트보고 변경')
    ind,vis,directory,root=map(read,(ip,vp,dp,rp));native=read(H/'standing_fire_components_native_checks.json');v=read(d/'verification.json');author=read(H/'standing_fire_visual_review02.json');seq=read(H/'standing_fire_sequence01/report.json');web=read(H/'standing_fire_sequence01/browser_verification.json')
    need(ind['passed']and ind['candidate_sha256']==FINAL and ind['parent_sha256']==PARENT and ind['input_lock_sha256']==LOCK_SHA,'독립 결속')
    need(ind['inputs'][str((d/'PREPARED_LOCK.json').relative_to(ROOT).as_posix())]==sha((d/'PREPARED_LOCK.json').read_bytes()),'독립준비잠금')
    need(directory['passed']and directory['candidate_sha256']==FINAL and directory['stats']['references']==508 and directory['stats']['native_decode_calls']==1016,'508원로더')
    need(not directory['python_bank_pointer_injection']and not directory['code_patches_or_stubs']and directory['memory_observer_results_identical'],'원코드제약')
    need(ind['native_report']['sha256']==sha(dp.read_bytes())and native['passed']and native['resources']['PL00_U.ARC']['candidate_sha256']==FINAL,'원MIPS 결속')
    need(root['candidate_sha256']==FINAL and len(root['actually_viewed_files'])==12,'루트 실제12판 범위');images(root['actually_viewed_files']);images(author['actual_viewed']);images(vis['sheets'])
    need(vis['candidate_sha256']==FINAL and vis['technical_report_sha256']==sha(ip.read_bytes()),'독립미술 결속')
    need(v['total_identical_builds']==3 and v['rejected_count']==15 and v['non_target_raw_exact']==482 and v['storage_raw_inverse_exact']==18,'재현/보존')
    need(v['target_layers_exact']==40 and v['storage_partial_rgba_exact']==576 and v['new_partial_rgba_exact']==256 and not v['bank_directory_changed'],'그림/부분/고정은행')
    need(ind['counts']['whole_256nibble_tiles_inverse_exact']==288 and ind['other_entries_audio_palette_all_bank_boundaries_exact'],'원타일 전체보존')
    need(seq['native_table_bytes_verified']and not seq['timing_changed']and[ r['id']for r in seq['native_step_checks']]==[88,89,90,91,94]and sum(r['steps']for r in seq['native_step_checks'])==23,'원순서범위')
    need(web['passed']and sum(r['canvas_form_checks']for r in web['cases'])==594 and web['native_table_report_sha256']==sha((H/'standing_fire_sequence01/report.json').read_bytes()),'원순서canvas')
    evidence=[LOCK,d/'PREPARED_LOCK.json',d/'verification.json',ip,vp,dp,rp,H/'standing_fire_components.json',H/'standing_fire_components_native_checks.json',H/'standing_fire_visual_review02.json',H/'standing_fire_sequence01/report.json',H/'standing_fire_sequence01/browser_verification.json',H/'standing_fire_sequence01/REVIEW.html',H/'review_standing_fire_sequence.py',H/'check_standing_fire_browser.py']
    proof={'passed':True,'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'selected_visual_refs':list(range(85,93)),'storage_only_refs':v['storage_only_refs'],'target_lock_sha256':LOCK_SHA,'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in evidence},'counts':ind['counts'],'total_identical_builds':3,'rejected_inputs':15,'root_actually_viewed_plates':12,'root_plate_scope':'접점2+완성6+원순서4;부분8을루트열람으로세지않음','author_final_actual_plates':18,'independent_actual_plates':12,'all508_directory_native':True,'native_calls_observers_on_off':1016,'original_step_bytes_exact':23,'offline_twoform_canvas_checks':594,'graphics_bank0_free_bytes':68,'all_bank_boundaries_preserved':True,'original32tile_full_inverse_nibbles_exact':True,'no_texel_deleted_for_capacity':True,'user_new_address_approval_claimed':False,'selection_copy_refs_pending':list(range(1,9)),'selection_copy_sync_complete':False,'gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'initial_pending_flags_superseded':True,'freeze_script':ev(Path(__file__)),
        'limits':['원MIPS는 실제 원명령을 분리된RAM fixture에서 실행한 검사이며 새 게임실기/전체spawn 검증은 아니다.','별도 투사체·외부타이머와 말미92 이후 상태는 오프라인검토기가 실행하지 않는다.60호출/초 및96calls를 고정 실제 게임시간으로 주장하지 않는다.','새85/86은 현재수용포즈의 개별 상세원화다. 원US 전체몸체 반동391셀의 완전복원이 아니다.','85 한발1px/90·91 신발폭차는 원지지발과함께root 정적수용방향을받았으며 물리판정변경없다.','기본85..92 선택1..8 사본은 향후UIv4 동기화까지 미완료. Ultimate85..92·차량·호버·거부135 등 전폼 잔여는 별도다.']}
    write(d/'final_verification.json',proof);write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'selected_visual_refs':list(range(85,93)),'storage_only_refs':v['storage_only_refs'],'native_and_independent_passed':True,'root_packed_and_ordered_reviewed':True,'root_actual_plates':12,'all_graphics_bank_boundaries_preserved':True,'supersedes_initial_pending_flags':True,'selection_sync_pending':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False});print(json.dumps({'frozen':ev(d/'FROZEN.json'),'verification':ev(d/'final_verification.json'),'candidate':FINAL}))
if __name__=='__main__':main()
