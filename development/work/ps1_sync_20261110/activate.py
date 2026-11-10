"""Publish verified PS1 pointers and record the user's actual acceptance."""
import json
import shutil
from sync import ROOT,D,W,STEAM,INSTALLED,file_hash,save

def load(path):return json.loads(path.read_text('utf8'))
build=load(D/'build.json')
assert file_hash((ROOT/build['cue']).with_suffix('.bin'))==build['sha256']
assert file_hash((ROOT/build['rn_cue']).with_suffix('.bin'))==build['rn_sha256']
for name in ['preparation','scope_verification','native_verification','player_audit','runtime_verification']:
    assert load(D/(name+'.json'))['passed']
runtime=load(D/'runtime_verification.json')
runtime['user_quote']='내가 테스트를 해봤는데 잘적용되었어'
save(D/'runtime_verification.json',runtime)
protected=load(D/'protected_before.json')
for path,digest in protected.items():assert file_hash(ROOT/path)==digest,path
for path,digest in INSTALLED.items():assert file_hash(STEAM/path)==digest,path
backup=D/'metadata_before'
backup.mkdir(exist_ok=True)
records=[]
for mode in ['ver_buki_riko','ver_rin_nana']:
    cp=ROOT/'projects'/mode/'current_build.json'
    pj=cp.with_name('project.json')
    old=load(cp);project=load(pj)
    for p in [cp,pj]:
        target=backup/mode/p.name
        target.parent.mkdir(exist_ok=True)
        assert not target.exists()
        shutil.copyfile(p,target)
    new={**old,'ps1_latest_sync_report':'docs/PS1_LATEST_SYNC_20261110.md',
         'steam_player_sprite_art_matches':True,'steam_player_sprite_art_audit':'work/ps1_sync_20261110/player_audit.json'}
    if mode=='ver_buki_riko':
        assert old==load(D/'parent_pointer.json')
        out=(ROOT/build['cue']).parent
        new.update(task='ps1_latest_sync_20261110',stage='PS1_LATEST_SYNC_USER_ACCEPTED',
                   build=out.relative_to(ROOT).as_posix(),cue=build['cue'],sha256=build['sha256'],
                   previous_pointer=(backup/mode/'current_build.json').relative_to(ROOT).as_posix(),
                   status_report='docs/PS1_LATEST_SYNC_20261110.md',
                   shibuki_eyes_ps1_applied=True,shibuki_eyes_user_accepted=True,
                   user_accepted=True,user_acceptance_source='2026-11-10 사용자: 내가 테스트를 해봤는데 잘적용되었어',
                   acceptance_scope='latest_PS1_iris_backport_observed_by_user_not_all_outfit_scenes',
                   current_session=runtime['session'],running_bin_sha256=build['sha256'],
                   current_runtime_state='새 CUE 정상 부팅 후 선택 화면의 수정 눈 영역750픽셀을 실제 VRAM 두 프레임에서 확인. 사용자 적용 테스트 수용.',
                   runtime_verification_scope='자동 검사: 선택 얼굴 GPU 프레임, 네이티브 HQ19상태/보호15조건. 모든 의상·장면 자동 실기 전수 확인은 아님.',
                   next_action='이 CUE를 현재 PS1 실행본으로 사용. 이후 사용자 버그 제보를 기준으로 수정.',
                   illustration_review=(out/'review/index.html').relative_to(ROOT).as_posix())
        project.update(active_task=new['task'],active_substage=new['stage'],
                       latest_integrated_build=new['build'],latest_integrated_bin_sha256=new['sha256'])
        manifest=load(out/'manifest.json')
        manifest.update(runtime_verified=True,runtime_scope='fresh boot and native selection face framebuffer',
                        user_accepted=True,user_acceptance_quote=runtime['user_quote'],all_outfit_scenes_live_tested=False)
        save(out/'manifest.json',manifest)
        shutil.copyfile(D/'runtime_verification.json',out/'review/runtime_verification.json')
        recipe=out/'review/recipe';recipe.mkdir(exist_ok=True)
        for p in D.glob('*.py'):shutil.copyfile(p,recipe/p.name)
    else:
        assert old['cue']==build['rn_cue'] and old['sha256']==build['rn_sha256']
        new['ps1_latest_sync_content_changed']=False
    project['ps1_latest_sync_report']='docs/PS1_LATEST_SYNC_20261110.md'
    save(cp,new);save(pj,project)
    records.append({'mode':mode,'cue':new['cue'],'sha256':new['sha256'],'bin_changed':mode=='ver_buki_riko'})
save(D/'application.json',{'passed':True,'builds':records,'protected_files_preserved':len(protected),
    'steam_files_preserved':len(INSTALLED),'user_quote':runtime['user_quote'],'metadata_backup':str(backup.relative_to(ROOT)),
    'new_cue_started_without_F3':True,'save_states_or_original_memory_cards_written':False,'user_test_accepted':True,
    'new_external_upload':False})
print('Current PS1 pointers updated; user acceptance recorded; old builds and Steam preserved.')
