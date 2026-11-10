"""체이서13 새원화와 저장순열16의 최종 근거를 동결한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
FINAL='3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d'
PARENT='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'
def read(p):return json.loads(p.read_text('utf8'))
def imgs(rows):
    for r in rows:need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'열람 이미지 변경 '+r['path'])
def main():
    d=H/'prepared_chaser_base01';need(not(d/'FROZEN.json').exists(),'동결본 보호')
    need(sha((d/'PL00_U.ARC').read_bytes())==FINAL,'후보 변경');need(sha((H/'prepared_standing_fire_base01/PL00_U.ARC').read_bytes())==PARENT,'부모 변경')
    lock=read(d/'PREPARED_LOCK.json');source=read(d/'INPUT_LOCK.json')
    for n,v in lock['files'].items():need(sha((d/n).read_bytes())==v,'준비 파일 변경 '+n)
    for n,v in lock['source_scripts'].items():need(sha((H/n).read_bytes())==v,'제작 도구 변경 '+n)
    for n,v in source['files'].items():need(sha((ROOT/n).read_bytes())==v,'잠금 출처 변경 '+n)
    need(len(source['files'])==332,'출처332 범위')
    audit=H.parent/'zero_audit/shibuki_chaser13_independent01';ip=audit/'report.json';vp=audit/'visual_review.json';np=H.parent/'zero_audit/shibuki_chaser13_directory_native01/report.json';rp=H.parent/'root_review_checkpoint144.json'
    hashes={ip:'177bb4cf5552cd6a1976288675d1e0fed9875061b55c4f05a1e80bce0aae86c7',vp:'64f3059f76fbdce41f5d7e6aaf4ccc9f4e0385ae842668a12f8a7b15ccd75a35',np:'e99baffd8a88f474ff7d270004002d0016a4603b50ff4e3fc64da1b7d9b3a61d',rp:'6cb7f35111068ff48113e21187c9f6b92cb88caa11368ccd80fc06307c5fce17'}
    for p,v in hashes.items():need(sha(p.read_bytes())==v,'최종 근거 변경 '+str(p))
    ind,vis,native,root=map(read,(ip,vp,np,rp));v=read(d/'verification.json');author=read(d/'author_visual_review.json')
    need(ind['passed'] and ind['candidate_sha256']==FINAL and ind['parent_sha256']==PARENT,'독립 후보 결속')
    need(ind['input_lock_sha256']==sha((d/'INPUT_LOCK.json').read_bytes()),'독립 잠금 결속')
    c=ind['counts'];need(c['raw_checked']==508 and c['non_target_raw_exact']==479 and c['target_layers_exact']==65 and c['non_art_layers_exact']==1075,'독립 참조/층 범위')
    need(c['storage_partial_RGBA_exact']==512 and c['target_partial_RGBA_exact']==416 and c['full256nibble_tiles_inverse_exact']==256,'역순열/부분 범위')
    need(native['passed'] and native['candidate_sha256']==FINAL and len(native['references'])==508 and native['all_executed_instructions_original_US_exact'],'실제 원디렉터리/원MIPS 결속')
    need(not native['python_bank_pointer_injection'] and not native['code_patches_or_stubs'] and native['memory_observer_results_identical'],'원코드/포인터 주입 금지')
    need(root['candidate_sha256']==FINAL and len(root['actually_viewed_files'])==18,'루트 실제18판');imgs(root['actually_viewed_files']);imgs(vis['actually_viewed']);imgs(author['actually_viewed'])
    need(v['passed'] and v['total_identical_builds']==3 and v['rejected_count']==16 and not v['bank_directory_changed'] and not v['pixel_reduction'],'재현/거부/은행')
    sp=H/'chaser_base_sequence01/report.json';bp=sp.parent/'browser_verification.json';seq,web=map(read,(sp,bp))
    need(seq['native_table_bytes_verified'] and not seq['timing_changed'] and sum(r['steps']for r in seq['native_step_checks'])==39,'원표39단계')
    need(web['passed'] and sum(r['canvas_form_checks']for r in web['cases'])==300 and web['native_table_report_sha256']==sha(sp.read_bytes()),'오프라인300폼')
    evidence=[d/'PREPARED_LOCK.json',d/'INPUT_LOCK.json',d/'verification.json',d/'author_visual_review.json',d/'post_lock_evidence.json',ip,vp,audit/'READER_LOCK.json',np,rp,sp,bp,sp.parent/'REVIEW.html',H/'review_chaser_sequence.py',H/'check_chaser_browser.py',Path(__file__)]
    proof={'passed':True,'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'selected_refs':list(range(162,175)),'storage_only_refs':v['storage_only_refs'],'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in evidence},'counts':c,'source_files_checked':332,'total_identical_builds':3,'rejected_inputs':16,'root_actual_plates':18,'author_actual_plates':22,'independent_actual_plates':12,'all_directory_original_MIPS_refs':508,'native_decodes_with_and_without_observer':1016,'original_step_bytes_exact':39,'offline_twoform_canvas_checks':300,'all_bank_boundaries_preserved':True,'no_art_deleted_or_scaled_for_storage':True,'graphics_bank0_free_bytes':4,'parts_free_bytes':v['parts_slack'],'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'limits':['실제 원MIPS는 RAM-loader부터 디렉터리/객체주소/디코더/업로드 큐까지이며 게임/CD/실제GPU 실행은 아니다.','GPU423파트와 부분928표시는 정적 의미검사다. 차량 손잡이·발판 실기 접촉은 미확인이다.','원표39단계 및 오프라인300폼은60호출/초 가정이며 외부 상태종료·물리·효과·소리는 재현하지 않는다.','새4키의 Y9파생은 실제 원US/현재PL00 관계를 따르며 저장16참조는 전체256nibble 역순열 동등성을 보존한다.','Ultimate 체이서 및 다른 전체 폼 미완료는 별도 계속한다.']}
    write(d/'final_verification.json',proof)
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'selected_refs':list(range(162,175)),'storage_only_refs':v['storage_only_refs'],'native_and_independent_passed':True,'root_packed_and_ordered_reviewed':True,'root_actual_plates':18,'all_graphics_bank_boundaries_preserved':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'candidate':FINAL,'FROZEN':sha((d/'FROZEN.json').read_bytes()),'proof':sha((d/'final_verification.json').read_bytes())}))
if __name__=='__main__':main()
