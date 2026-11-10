"""Ultimate 체이서13의 실제 검토·독립 재구성·원코드 근거를 결속한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
FINAL='2b8faa71d3a94bc6d52ac0e389c6121d530d6455e664ad852061c43c77789b5c'
PARENT='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad'
def read(p):return json.loads(p.read_text('utf8'))
def imgs(rows):
    for r in rows:need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'열람 이미지 변경 '+r['path'])
def main():
    d=H/'prepared_chaser_ultimate01';need(not(d/'FROZEN.json').exists(),'동결본 보호')
    need(sha((d/'PL02_U.ARC').read_bytes())==FINAL,'후보 변경')
    need(sha((H/'prepared_standing_fire_ultimate01/PL02_U.ARC').read_bytes())==PARENT,'부모 변경')
    lock,source=map(read,(d/'PREPARED_LOCK.json',d/'INPUT_LOCK.json'))
    for n,v in lock['files'].items():need(sha((d/n).read_bytes())==v,'준비 파일 변경 '+n)
    for n,v in lock['source_scripts'].items():need(sha((H/n).read_bytes())==v,'제작 도구 변경 '+n)
    for n,v in source['files'].items():need(sha((ROOT/n).read_bytes())==v,'잠금 출처 변경 '+n)
    need(len(source['files'])==297,'출처297 범위')
    audit=H.parent/'zero_audit/shibuki_chaser_ultimate13_independent01'
    ip=audit/'report.json';vp=audit/'visual.json';np=H/'chaser_ultimate_components_native_checks.json';rp=H.parent/'root_review_checkpoint145.json'
    hashes={ip:'6d7feb53df135880090056b2e00b593a7e9c70a7252935b787c95e76011ec100',vp:'55ea21bdbeb659a6de438550aa86c32f5940d79a0e3b146c8ae1557be73f78a9',np:'9bbf130f87b23c66b72640ade3f17396436c3b2adcefcdc0ff214a5db4ba2f53',rp:'7bf38aefd1b675aadf30bd2a8d4ea484dbc344383d81cf4f8334c0e49aa9a74b'}
    for p,v in hashes.items():need(sha(p.read_bytes())==v,'근거 변경 '+str(p))
    ind,vis,native,root=map(read,(ip,vp,np,rp));v=read(d/'verification.json');author=read(d/'author_visual_review.json')
    need(ind['passed'] and ind['candidate_sha256']==FINAL and ind['parent_sha256']==PARENT,'독립 후보 결속')
    need(ind['input_lock_sha256']==sha((d/'INPUT_LOCK.json').read_bytes()),'독립 잠금 결속')
    c=ind['counts'];need(c['raw_checked']==512 and c['non_target_raw_exact']==499 and c['target_layers_exact']==65 and c['non_target_layers_exact']==1075,'독립 참조/층 범위')
    need(c['partial_RGBA_exact']==416 and c['GPU_parts']==174 and c['generated_cells_requantized']==8 and ind['all416_partial_single_component'],'부분·원화 범위')
    need(not ind['producer_functions_called'] and not ind['source_or_resource_modified'],'독립 읽기 범위')
    n=native['resources']['PL02_U.ARC'];need(native['passed'] and n['candidate_sha256']==FINAL,'원MIPS 후보 결속')
    checks=[q for b in n['banks'] for q in b['native_decoder_checks']]
    need(len(checks)==13 and sorted(q['frame']for q in checks)==list(range(162,175)),'원MIPS13 범위')
    need(all(q['buffer_outside_and_unused_tail_preserved']for q in checks),'원디코더 경계')
    need(root['candidate_sha256']==FINAL and len(root['actually_viewed_files'])==18,'루트 실제18판')
    imgs(root['actually_viewed_files']);imgs(vis['actually_viewed']);imgs(author['actually_viewed'])
    need(v['passed'] and v['total_identical_builds']==3 and v['rejected_count']==12 and v['all_bank_boundaries_preserved'] and not v['pixel_reduction'],'재현·거부·은행')
    sp=H/'chaser_ultimate_sequence01/report.json';bp=sp.parent/'browser_verification.json';seq,web=map(read,(sp,bp))
    need(seq['native_table_bytes_verified'] and not seq['timing_changed'] and sum(r['steps']for r in seq['native_step_checks'])==39,'원표39단계')
    need(web['passed'] and sum(r['canvas_form_checks']for r in web['cases'])==300 and web['native_table_report_sha256']==sha(sp.read_bytes()),'오프라인300폼')
    evidence=[d/'PREPARED_LOCK.json',d/'INPUT_LOCK.json',d/'verification.json',d/'author_visual_review.json',d/'post_lock_evidence.json',ip,vp,audit/'READER_LOCK.json',np,rp,sp,bp,sp.parent/'REVIEW.html',H/'review_chaser_ultimate_sequence.py',H/'check_chaser_ultimate_browser.py',Path(__file__)]
    proof={'passed':True,'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'selected_refs':list(range(162,175)),'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in evidence},'counts':c,'source_files_checked':297,'total_identical_builds':3,'rejected_inputs':12,'root_actual_plates':18,'author_actual_plates':22,'independent_actual_plates':12,'original_MIPS_changed_refs':13,'original_step_bytes_exact':39,'offline_twoform_canvas_checks':300,'all_bank_boundaries_preserved':True,'no_art_deleted_or_scaled_for_storage':True,'graphics_bank0_free_bytes':11980,'parts_free_bytes':v['part_slack'],'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'limits':['원MIPS는 새13참조 디코더·업로드 큐 검사이며 전체512 로더나 실제 게임 검사가 아니다.','512raw·65목표층·416부분·174GPU는 독립 정적 읽기검사다. 실제 차량 손잡이·발판 접촉은 미확인이다.','원표39단계·오프라인300폼은60호출/초 가정이며 외부 상태종료·물리·효과·소리는 재현하지 않는다.','새9개 Y파생은 원US5층 관계를 따른 새 공통몸체 정책으로, 부모 after의 기존 차이를 그대로 복원했다는 뜻은 아니다.','170 새발35셀을 위1px 평행등록하며 기존 접속행9셀씩 가려진 것을 기록했다. 저장을 위한 미술 삭제나 전신 축소가 아니다.','다른 모션과 도구 거부 후 보류된135는 전체 미완료로 유지한다.']}
    write(d/'final_verification.json',proof)
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'selected_refs':list(range(162,175)),'native_and_independent_passed':True,'root_packed_and_ordered_reviewed':True,'root_actual_plates':18,'all_graphics_bank_boundaries_preserved':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'candidate':FINAL,'FROZEN':sha((d/'FROZEN.json').read_bytes()),'proof':sha((d/'final_verification.json').read_bytes())}))
if __name__=='__main__':main()
