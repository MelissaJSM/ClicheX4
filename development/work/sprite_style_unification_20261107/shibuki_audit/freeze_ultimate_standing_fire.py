"""Ultimate85..92의 원화/검증/독립/미술 근거를 해시로 동결."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_ultimate_standing_fire import validate,P,PARENT
FINAL='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad'
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def read(p):return json.loads(p.read_text('utf8'))
def imgs(rows):
    for r in rows:need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'실제 열람 그림 변경 '+r['path'])
def main():
    d=H/'prepared_standing_fire_ultimate01';need(not(d/'FROZEN.json').exists(),'동결본 보호');validate(P.read_bytes())
    need(sha((d/'PL02_U.ARC').read_bytes())==FINAL,'후보 변경')
    lock=read(d/'PREPARED_LOCK.json');source=read(d/'INPUT_LOCK.json')
    for n,v in lock['files'].items():need(sha((d/n).read_bytes())==v,'준비 파일 변경 '+n)
    for n,v in lock['source_scripts'].items():need(sha((H/n).read_bytes())==v,'제작 도구 변경 '+n)
    for n,v in source['files'].items():need(sha((ROOT/n).read_bytes())==v,'잠금 출처 변경 '+n)
    need(len(source['files'])==390,'390 출처 범위')
    ad=H.parent/'zero_audit/shibuki_ultimate_fire8_independent01';ip=ad/'report.json';vp=ad/'visual_review.json';rp=H.parent/'root_review_checkpoint140.json'
    need(sha(ip.read_bytes())=='0d8c6f3fd66fe69d5b951fa230aa61d93d32794f57c4b9dae6f8d8f98eca3f57','독립 보고 변경')
    need(sha(rp.read_bytes())=='cf6424be4f688506b83469395053e8283944cda25e94b1f55c9e567f6aaf250f','루트 보고 변경')
    ind,vis,root=map(read,(ip,vp,rp));v=read(d/'verification.json');author=read(d/'author_visual_review.json')
    np=H/'ultimate_standing_fire_components_native_checks.json';native=read(np)
    sp=H/'ultimate_standing_fire_sequence01/report.json';bp=sp.parent/'browser_verification.json';seq,web=map(read,(sp,bp))
    need(ind['passed']and ind['candidate_sha256']==FINAL and ind['parent_sha256']==PARENT,'독립 후보/부모 결속')
    need(ind['input_lock_sha256']==sha((d/'INPUT_LOCK.json').read_bytes()),'독립 출처잠금')
    for n,digest in ind['inputs'].items():need(sha((ROOT/n).read_bytes())==digest,'독립 입력 변경 '+n)
    need(ind['counts']['raw_checked']==512 and ind['counts']['non_target_raw_exact']==504 and ind['counts']['target_layers_exact']==40,'독립 전체/목표 범위')
    need(ind['counts']['partial_RGBA_exact']==256 and ind['counts']['gun_guard_RGBA_exact']==224 and ind['counts']['effect83_RGBA_exact']==32,'부분/총열/효과')
    need(ind['other_entries_audio_palette_all_bank_bounds_exact'],'외부/은행 보존')
    need(native['passed']and native['resources']['PL02_U.ARC']['candidate_sha256']==FINAL and ind['native_report']['sha256']==sha(np.read_bytes()),'원MIPS 결속')
    need(root['candidate']['sha256']==FINAL and root['actual_images_count']==10,'루트 실제10판');imgs(root['actually_viewed_images']);imgs(vis['actually_viewed_sheets']);imgs(author['actually_viewed'])
    need(vis['candidate_sha256']==FINAL and vis['independent_report_sha256']==sha(ip.read_bytes()),'독립 열람 결속')
    need(v['passed']and v['total_identical_builds']==3 and v['rejected_count']==17 and v['all_bank_boundaries_preserved'],'재현/거부/은행')
    need(seq['native_table_bytes_verified']and not seq['timing_changed']and sum(r['steps']for r in seq['native_step_checks'])==23,'원표 바이트')
    need(web['passed']and sum(r['canvas_form_checks']for r in web['cases'])==594 and web['native_table_report_sha256']==sha(sp.read_bytes()),'원표 canvas')
    evidence=[d/'PREPARED_LOCK.json',d/'INPUT_LOCK.json',d/'verification.json',ip,vp,ad/'READER_LOCK.json',rp,np,H/'ultimate_standing_fire_components.json',sp,bp,sp.parent/'REVIEW.html',H/'review_ultimate_standing_fire_sequence.py',H/'check_ultimate_standing_fire_browser.py',d/'author_visual_review.json',d/'post_lock_evidence.json']
    proof={'passed':True,'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'selected_refs':list(range(85,93)),
        'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in evidence},'counts':ind['counts'],
        'source_files_checked':390,'total_identical_builds':3,'rejected_inputs':17,'root_actual_plates':10,'author_actual_plates':18,'independent_actual_plates':4,
        'original_mips_changed_refs':8,'all_directory_native_reexecuted_here':False,'original_step_bytes_exact':23,'offline_twoform_canvas_checks':594,
        'graphics_bank0_free_bytes':9208,'all_bank_boundaries_preserved':True,'no_art_deleted_or_scaled_for_storage':True,
        'old_135_preserved_unfinished':True,'native_and_independent_passed':True,'root_packed_and_ordered_reviewed':True,
        'initial_pending_flags_superseded':True,'gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'freeze_script':ev(Path(__file__)),
        'limits':['원MIPS는 변경8의 원디코더/업로드 및 GPU 검사다. 실제 게임/전체spawn/512참조 새디렉터리 실행이라고 확대하지 않는다.',
            '원표23단계와 브라우저594폼 검사는60호출/초 가정이며 실제 투사체/외부타이머/음향/물리 검증이 아니다.',
            '88은 현재부모의 별도 옛몸198셀을 복사하지 않고 원US 효과83과 새89 x−1을 통일한 새제작 정책이다.',
            '생성14셀의 전체 캔버스 등록은 제작자가 수행했고 독립독자는 등록14표시부터 재구성했다. 독립 재양자화로 세지 않는다.',
            '차량/호버 및 거부135 등 전폼 잔여는 계속 진행 중이며 전체 미술 완료가 아니다.']}
    write(d/'final_verification.json',proof)
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},
        'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'selected_refs':list(range(85,93)),'native_and_independent_passed':True,
        'root_packed_and_ordered_reviewed':True,'root_actual_plates':10,'all_graphics_bank_boundaries_preserved':True,
        'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
    print(json.dumps({'frozen':ev(d/'FROZEN.json'),'verification':ev(d/'final_verification.json'),'candidate':FINAL}))
if __name__=='__main__':main()
