"""95..97 네폼의 원화·독립 reader·원MIPS·원표·실제 미술검토를 결속한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_standing_special_relocated import validate as validate_base,P as BASE_PARENT
from pack_ultimate_special import validate as validate_ultimate,P as ULT_PARENT
BASE='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e'
ULT='26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce'
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def read(p):return json.loads(p.read_text('utf8'))
def locked_images(rows):
    for q in rows:need(sha((ROOT/q['path']).read_bytes())==q['sha256'],'Reviewed image changed '+q['path'])
def main():
    validate_base(BASE_PARENT.read_bytes(),lambda p:p.read_bytes());validate_ultimate(ULT_PARENT.read_bytes(),lambda p:p.read_bytes())
    common=[H/'standing_special_fourform_components_native_checks.json',H.parent/'root_review_checkpoint127.json',H/'standing_special_sequence01/report.json',H/'standing_special_sequence01/browser_verification.json',H/'standing_special_visual_review01.json']
    native,root,seq,web,author=map(read,common)
    need(native['passed']and web['passed'],'Native/browser incomplete')
    need(sha(common[1].read_bytes())=='6e2e163ff7984cf1d796bcc8a7c39bc4ee639a50149397d8c730229c86af381d','Root review changed')
    need(len(root['root_actually_viewed'])==16,'Root16 review mismatch');locked_images(root['root_actually_viewed'])
    for group in author['groups'].values():locked_images(group)
    need(seq['native_table_bytes_verified']and not seq['timing_changed'],'Original sequence changed')
    need([r['id']for r in seq['native_step_checks']]==[95,96,97,104,105]and all(r['all_bytes_exact']for r in seq['native_step_checks']),'Original table scope')
    need(sum(r['steps']for r in seq['native_step_checks'])==26,'Step count')
    need(web['native_table_report_sha256']==sha(common[2].read_bytes())and web['html_sha256']==sha((H/'standing_special_sequence01/REVIEW.html').read_bytes()),'Browser binding')
    canvas_count=sum(r['canvas_form_checks']for r in web['cases']);need(canvas_count==604,'Canvas count')
    configs=[('base','PL00_U.ARC',BASE,BASE_PARENT,'shibuki_standing3_independent01',11),('ultimate','PL02_U.ARC',ULT,ULT_PARENT,'shibuki_ultimate_special3_independent01',9)]
    pending=[]
    for form,name,final,parent,audit_name,rejections in configs:
        d=H/f'prepared_standing_special_{form}01';need(not(d/'FROZEN.json').exists(),'Already frozen')
        lk=read(d/'PREPARED_LOCK.json')
        for n,digest in lk['files'].items():need(sha((d/n).read_bytes())==digest,'Prepared changed '+n)
        for n,digest in lk.get('source_scripts',lk.get('scripts',{})).items():need(sha((H/n).read_bytes())==digest,'Producer changed '+n)
        need(sha((d/name).read_bytes())==final,'Candidate changed')
        need(root['candidate_sha256'][name]==final and native['resources'][name]['candidate_sha256']==final,'Review/native binding')
        need(author['candidate_assets'][name]==final and seq['candidates'][form]['sha256']==final,'Author/sequence binding')
        ad=H.parent/'zero_audit'/audit_name;ip=ad/'report.json';vp=ad/'visual_review.json';ind=read(ip);vis=read(vp)
        need(ind['passed']and ind['candidate_sha256']==final and ind['parent_sha256']==sha(parent.read_bytes()),'Independent result')
        need(ind['prepared_lock_sha256']==sha((d/'PREPARED_LOCK.json').read_bytes()),'Independent prepared binding')
        need(vis['candidate_sha256']==final and vis['technical_report_sha256']==sha(ip.read_bytes()),'Independent visual binding')
        locked_images(vis['actually_viewed']);v=read(d/'verification.json')
        need(v['total_identical_builds']==3 and v.get('rejected_count',v.get('rejection_count'))==rejections,'Reproduction/refusals')
        evidence=common+[ip,vp,d/'PREPARED_LOCK.json',d/'verification.json'];extra={}
        if form=='base':
            dp=H.parent/'zero_audit/shibuki_standing3_directory_native01/report.json';dr=read(dp)
            need(dr['passed']and dr['candidate_sha256']==final and dr['stats']['references']==508 and dr['stats']['native_decode_calls']==1016,'All directory references')
            need(not dr['python_bank_pointer_injection']and not dr['code_patches_or_stubs']and dr['memory_observer_results_identical'],'Native instrumentation limits')
            need(ind['native_directory_report_sha256']==sha(dp.read_bytes()),'Directory report binding')
            need(ind['bank0_growth']==280 and ind['tail_trim']=={'12':280} and ind['entry2_size_fixed']==186228 and ind['bank13_absolute_bytes_exact'],'Relocation limits')
            evidence += [dp,H.parent/'zero_audit/shibuki_bank12_tail280_audit01/report.json',H/'standing_special_locked01/LOCK.json']
            extra={'native_directory_all_refs':508,'native_calls_observers_on_off':1016,'fixed_entry2_size':186228,'bank0_growth':280,'bank12_unconsumed_tail_trim':280,'tail_nonzero_bytes':264,'bank13_absolute_start':184744,'bank13_full_bytes_exact':True,'internal_directory_relocated':True,'user_new_address_approval_claimed':False,'target_lock_sha256':ind['target_lock_sha256']}
        else:
            need(ind['target_manifest_sha256']==sha((H/'ultimate_special_targets01/manifest.json').read_bytes()),'Target manifest binding')
            evidence += [H/'ultimate_special_targets01/manifest.json'];extra={'all_bank_boundaries_preserved':True,'internal_directory_relocated':False,'target_manifest_sha256':ind['target_manifest_sha256']}
        proof={'passed':True,'candidate_sha256':final,'parent_arc_sha256':sha(parent.read_bytes()),'selected_visual_refs':[95,96,97],'evidence':{e.relative_to(ROOT).as_posix():sha(e.read_bytes())for e in evidence},'counts':ind['counts'],'native_MIPS_GPU':True,'native_changed_refs':[95,96,97],'native_isolated_not_gameplay':True,'independent_producer_functions_called':False,'total_identical_builds':3,'rejected_inputs':rejections,'root_review_joint_fourform_plates':16,'root_form_packed_partial_plates':4,'root_form_ordered_plates':4,'original_sequence_ids':[95,96,97,104,105],'native_step_bytes_exact':26,'offline_canvas_form_checks_fourforms':604,'continuous_animation_actually_watched_by_model':False,'gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'initial_pending_flags_superseded':True,'limits':['정적 재추출/원표 순서판과 오프라인 캔버스 검사다. 실제 무기 객체·외부 상태·물리·모든60Hz 전환 실기는 별도다.','96은 새95의x+1 파생이다. 원US 관계를 근거로 한 신규 공통화이며 현재 Ultimate 부모95/96 픽셀 동일 주장이 아니다.','원표 terminal relative_step0은 외부 상태 종료를 기다린다. 60호출/초·미리보기 유지시간을 실제 고정 게임시간으로 주장하지 않는다.','85..92 새원화/기존135 보류·차량/호버 등 전폼 잔여는 유지하며 전체 품질 완료가 아니다.'],'freeze_script':ev(Path(__file__)),**extra}
        pending.append((d,proof))
    for d,proof in pending:
        write(d/'final_verification.json',proof)
        write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':proof['candidate_sha256'],'parent_arc_sha256':proof['parent_arc_sha256'],'selected_visual_refs':[95,96,97],'native_and_independent_passed':True,'root_packed_partial_ordered_reviewed':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False})
        print(json.dumps({'frozen':ev(d/'FROZEN.json'),'verification':ev(d/'final_verification.json'),'candidate':proof['candidate_sha256']}))
if __name__=='__main__':main()
