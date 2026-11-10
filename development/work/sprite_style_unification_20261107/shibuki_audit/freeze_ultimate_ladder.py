"""사다리14 동결: 기존 후보를 바꾸지 않고 원MIPS·독립·직접열람 증거를 연결."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_ultimate_ladder import P,PARENT,LOCK,REFS,validate
FINAL='03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a'
def main():
    d=H/'prepared_ultimate_ladder01';need(not(d/'FROZEN.json').exists(),'Already frozen');lk=json.loads((d/'PREPARED_LOCK.json').read_text('utf8'))
    for n,h in lk['files'].items():need(sha((d/n).read_bytes())==h,'Prepared changed '+n)
    for n,h in lk['source_scripts'].items():need(sha((H/n).read_bytes())==h,'Producer changed '+n)
    validate(P.read_bytes());need(sha((d/'PL02_U.ARC').read_bytes())==FINAL,'Candidate changed')
    paths=[H/'ultimate_ladder_components_native_checks.json',ROOT/'work/sprite_style_unification_20261107/zero_audit/shibuki_ultimate_ladder_independent01/report.json',ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint94.json',ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint96.json',H/'ultimate_ladder_shot_sequence01/browser_verification.json',H/'ultimate_ladder_review_progress02.json'];r=[json.loads(p.read_text('utf8'))for p in paths]
    need(r[0]['passed']and r[1]['passed']and r[4]['passed'],'Checks not passed');need(r[0]['resources']['PL02_U.ARC']['candidate_sha256']==FINAL and r[1]['candidate_sha256']==FINAL,'Wrong resource');need(r[1]['target_lock_sha256']==LOCK,'Wrong target lock')
    for q,count in((r[2],6),(r[3],4)):
        need(q['candidate_arc_sha256']==FINAL,'Wrong art review');need(len(q['root_actually_viewed'])==count,'Review incomplete')
        for im in q['root_actually_viewed']:need(sha((ROOT/im['path']).read_bytes())==im['sha256'],'Reviewed image changed')
    proof={'passed':True,'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'target_lock_sha256':LOCK,'selected_visual_refs':list(REFS),'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in paths},'counts':r[1]['counts'],'native_MIPS_GPU':True,'independent_reader_no_producer_called':True,'root_actual_packed_plates':6,'root_actual_sequence_endpoint_plates':4,'author_actual_packed_plates':6,'reproduction_runs':3,'invalid_input_rejections':8,'browser_native_canvas_checks':128,'native_bank_boundaries_preserved':True,'new_gameplay_verified':False,'user_accepted':False,'full_project_complete':False,'replaces_pending_status_in_initial_prepared_reports':True,'limitations':['原US155의 전신 반동을 복원한 것이 아니라 수용기본형의149공통몸체와150/155팔·총구반동 정책이다.','143/149/151/154 발끝은 이전Ult보다1px,183은2px높음. 현재정적판에추가확정단절은없으나실제사다리가로대접촉은미확인.','93 초기시간은 caller attack_pose_timer-8이며 브라우저8/17은 검토가정이다. 실기 시간 검증이나 연속영상을 직접본 것으로 표시하지 않는다.','공통머리/사지의CLUT16→0대응은기존팔레트의최근접색을사용하므로RGB전체동일이아니다.'],'next_scope':'전폼피격106..114/233..236의몸체4키/효과별등록,이후Ult등장·승리귀환/차량·특수잔여.'};proof['limitations'][0]=proof['limitations'][0].replace('原US','원US');write(d/'final_verification.json',proof)
    write(d/'FROZEN.json',{'frozen':True,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()and p.name!='FROZEN.json'},'candidate_sha256':FINAL,'parent_arc_sha256':PARENT,'source_lock_sha256':LOCK,'selected_visual_refs':list(REFS),'native_and_independent_passed':True,'root_packed_art_reviewed':True,'supersedes_initial_pending_flags':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False});print(json.dumps({'frozen':sha((d/'FROZEN.json').read_bytes()),'verification':sha((d/'final_verification.json').read_bytes()),'native':sha(paths[0].read_bytes())}))
if __name__=='__main__':main()
