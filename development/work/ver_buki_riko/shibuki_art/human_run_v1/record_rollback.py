from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,digest,load_project,inspect_references,validate_bin
d=Path(__file__).parent;project=load_project(ROOT,'ver_buki_riko');inspect_references(ROOT,project)
source_sha='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
validate_bin(ROOT/project['source_bin'],source_sha)
old=ROOT/'out/ver_buki_riko/shibuki_idle_20261026T044150188556Z';manifest=json.loads((old/'manifest.json').read_text())
validate_bin(old/'shibuki_riko.bin',manifest['modified_bin']['sha256'])
selection=json.loads((ROOT/'projects/ver_buki_riko/shibuki_art_selection.json').read_text(encoding='utf-8'))
assert digest(ROOT/selection['indexed_png'])==selection['indexed_sha256']
accepted=json.loads((ROOT/'projects/ver_buki_riko/riko_accepted_build.json').read_text(encoding='utf-8'))
out=new_run(ROOT,'ver_buki_riko','shibuki_rollback')
for name in ('current_build.json','shibuki_current_build.json','shibuki_art_selection.json','shibuki_unified_revision.json'):
 shutil.copyfile(ROOT/'projects/ver_buki_riko'/name,out/name)
pointer=json.loads((ROOT/'projects/ver_buki_riko/shibuki_current_build.json').read_text(encoding='utf-8'))
assert pointer['bin_sha256']==manifest['modified_bin']['sha256']
pointer.update(rollback_requested=True,rollback_basis='걷기 디자인을 기준으로 대기를 바꾸기 전의 일반 자세',
               rollback_request='아까 일반모션을 포기하고 걷는모션따라간다고 말할때쯤의 일반모션 수준으로 롤백. 최근 시안이 퍼리처럼 보임.',
               rollback_record=str(out.relative_to(ROOT)),active_art_study='work/ver_buki_riko/shibuki_art/human_run_v1',
               moving_shooting_art_applied=False,next_group='human_design_run_and_buster_revision',session_closed=True)
for name in ('current_build.json','shibuki_current_build.json'):
 (ROOT/'projects/ver_buki_riko'/name).write_text(json.dumps(pointer,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
study={'task':'x_shibuki','status':'human_design_revision_in_progress','basis':selection['candidate'],
       'idle_restored_without_redrawing':True,'study':str(d.relative_to(ROOT)),
       'native_body':str((d/'production').relative_to(ROOT)),'generated_sha256':digest(d/'generated.png'),
       'game_applied':False,'runtime_verified':False,'new_art_user_accepted':False,
       'remaining':'13번의 5조각 제한과 이동/사격 공동 분할·압축·실행 검사. 같은 포즈를 사격 프레임에 임시 적용하지 않음.',
       'buster_allowed':True,'rejected_build':'out/ver_buki_riko/shibuki_run_20261026T071235043138Z'}
write_json(ROOT/'projects/ver_buki_riko/shibuki_run_art_revision.json',study)
rejected=ROOT/study['rejected_build']
write_json(rejected/'user_review.local.json',{'accepted':False,'reason':'사람형 얼굴·몸 비율을 이전 일반 자세 수준으로 롤백 요청',
    'runtime_verification_completed':False,'last_session':'work/ver_buki_riko/emulator_sessions/20261026T071247880585Z',
    'process_already_exited_at_close_attempt':True,'current_build_promoted':False})
write_json(out/'rollback.local.json',{'restored_build':str(old.relative_to(ROOT)),'bin_sha256':pointer['bin_sha256'],
    'original_sha256':source_sha,'idle_png_sha256':selection['indexed_sha256'],'riko_accepted_pointer_unchanged':accepted==json.loads((ROOT/'projects/ver_buki_riko/riko_accepted_build.json').read_text(encoding='utf-8')),
    'previous_idle_preserved_exactly':True,'new_human_motion_in_game':False,'study':study})
print(json.dumps({'rollback':str(out),'cue':pointer['cue'],'sha256':pointer['bin_sha256']}))
