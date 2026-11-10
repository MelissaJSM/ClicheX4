"""Update only BR metadata after final capsule verification; keep original ROMs and saves untouched."""
import sys,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from src.psx_disc import file_hash
def load(p):return json.loads(p.read_text('utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
protected=load(D/'protection_before.json')['files']
for n,q in protected.items():assert file_hash(ROOT/n)==q['sha256'],n
cp=ROOT/'projects/ver_buki_riko/current_build.json';pj=cp.with_name('project.json');old=load(cp)
assert old==load(D/'before/current_build.json');result=load(D/'build.json');cue=ROOT/result['cue']
assert file_hash(cue.with_suffix('.bin'))==result['sha256'];mf=load(cue.parent/'manifest.json')
assert mf['only_capsule_banks_in_two_archives_changed'] and mf['native_render_cases']==184
current={**old,'task':'shibuki_capsule_outline_20261109','stage':'CAPSULE_OUTLINE_APPLIED_RUNTIME_PENDING',
 'build':cue.parent.relative_to(ROOT).as_posix(),'cue':result['cue'],'sha256':result['sha256'],
 'previous_pointer':(D/'before/current_build.json').relative_to(ROOT).as_posix(),
 'status_report':'docs/SHIBUKI_CAPSULE_OUTLINE_20261109.md','capsule_outline_report':'docs/SHIBUKI_CAPSULE_OUTLINE_20261109.md',
 'capsule_outline_review':(cue.parent/'review/index.html').relative_to(ROOT).as_posix(),
 'capsule_changed':True,'capsule_issue_status':'post_grant_edge_revision_and_force_combinations_applied',
 'capsule_runtime_verified':False,'capsule_user_accepted':False,'user_accepted':False,
 'current_session':None,'running_bin_sha256':None,
 'current_runtime_state':'새 캡슐 수정본 준비. 에뮬레이터 실행·키 입력·F1/F3·메모리 쓰기 없음.',
 'runtime_verification_scope':'원작 CPU의 지급·타이밍100조건, 8압축은행 및 실제 GPU 명령184조건 복원 일치. 새 BIN 실제 플레이는 미실행.',
 'next_action':'새 CUE를 부팅하여 게임 내 카드로 진행. 얼티밋 획득 후 흰 선, 포스 파츠 획득 마지막 섬광 확인. 예전 F3는 예전 효과를 복원할 수 있음.'}
save(cp,current);meta=load(pj);meta.update(active_task=current['task'],active_substage=current['stage'],latest_integrated_build=current['build'],latest_integrated_bin_sha256=current['sha256'],capsule_outline_report=current['status_report']);save(pj,meta)
updated={cp.relative_to(ROOT).as_posix(),pj.relative_to(ROOT).as_posix()}
for n,q in protected.items():
 if n not in updated:assert file_hash(ROOT/n)==q['sha256'],n
for p in D.glob('*.py'):shutil.copyfile(p,cue.parent/'review/recipe'/p.name)
save(D/'application.json',{'build':result,'metadata_updates':[{'file':n,'before_sha256':protected[n]['sha256'],'after_sha256':file_hash(ROOT/n)}for n in sorted(updated)],
 'protected_files_unchanged':len(protected)-len(updated),'originals_references_accepted_release_RN_saves_preserved':True,
 'emulator_keys_sent':False,'process_memory_written':False,'actual_gameplay_verified':False})
print('BR capsule build activated; protected files unchanged:',len(protected)-len(updated))
