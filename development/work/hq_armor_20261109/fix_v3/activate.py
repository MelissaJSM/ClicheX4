"""Activate verified Nana Force artwork; retain the BR v2 disc and user saves."""
import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent;H=F.parent
sys.path.insert(0,str(ROOT))
from src.psx_disc import file_hash
def load(p):return json.loads(p.read_text('utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
results=load(F/'builds.json');protected=load(F/'protection_before.json')['files']
for n,q in protected.items():assert file_hash(ROOT/n)==q['sha256'],n
assert load(ROOT/'out/illustration_review_20261109/verification.json')['passed']
updates=set()
for result in results:
 mode=result['mode'];assert mode=='ver_rin_nana'
 cp=ROOT/'projects'/mode/'current_build.json';pj=cp.with_name('project.json');old=load(cp)
 assert old==load(F/'baseline'/mode/'current_build.json')
 cue=ROOT/result['cue'];assert file_hash(cue.with_suffix('.bin'))==result['sha256']
 mf=load(cue.parent/'manifest.json');assert mf['only_resource13_container_changed'] and mf['native_cpu']['native_task_tables_preserved']
 new={**old,'task':'hq_force_art_review_20261109','stage':'HQ_FORCE_ART_APPLIED_USER_REVIEW_PENDING',
      'build':cue.parent.relative_to(ROOT).as_posix(),'cue':result['cue'],'sha256':result['sha256'],
      'previous_pointer':(F/'baseline'/mode/'current_build.json').relative_to(ROOT).as_posix(),
      'status_report':'docs/HQ_FORCE_ART_REVIEW_20261109.md',
      'hunter_armor_review':(cue.parent/'review/index.html').relative_to(ROOT).as_posix(),
      'illustration_review':'out/illustration_review_20261109/일러스트_모음집.html',
      'hunter_armor_runtime_verified':False,'hunter_armor_user_accepted':False,'user_accepted':False,
      'current_runtime_state':'실행 중인 v2에서 나나 armor=15, special=0, HQ bank15 선택을 읽기 전용으로 확인. 새 v3는 재시작하지 않음.',
      'runtime_verification_scope':'v3 실제 실행 미실시. 원작 CPU 상태19·보호15, 944타일/상태 및 HQ216그림 네이티브 렌더 일치. v2 로더와 EXE는 동일.',
      'next_action':'모음집에서 의상별 그림 검토. v3 CUE 새 부팅 후 게임 내 카드로 같은 포스 풀세트 상태를 불러와 대화·눈깜빡임·출격 확인.'}
 save(cp,new);meta=load(pj);meta.update(active_task=new['task'],active_substage=new['stage'],latest_integrated_build=new['build'],
   latest_integrated_bin_sha256=new['sha256'],illustration_review=new['illustration_review'],hunter_force_art_report=new['status_report']);save(pj,meta)
 updates.update([cp.relative_to(ROOT).as_posix(),pj.relative_to(ROOT).as_posix()])
 for name in ['gallery.py','gallery_template.html','verify_gallery.py','nana_force_prompt.txt','activate.py']:
  shutil.copyfile(F/name,cue.parent/'review/recipe'/name)
for n,q in protected.items():
 if n not in updates:assert file_hash(ROOT/n)==q['sha256'],n
save(F/'application.json',{'builds':results,'protected_files_unchanged':len(protected)-len(updates),
 'metadata_updates':[{'file':n,'before':protected[n]['sha256'],'after':file_hash(ROOT/n)}for n in sorted(updates)],
 'originals_references_accepted_releases_saves_preserved':True,'BR_disc_and_pointers_unchanged':True,
 'emulator_keys_sent':False,'process_memory_written':False,'actual_v3_gameplay_verified':False})
print('Activated RN v3; BR v2 unchanged. Protected files:',len(protected)-len(updates))
