"""Record the actual representative test coverage without claiming exhaustive play."""
import hashlib,json
from pathlib import Path
ROOT=Path.cwd();BASE=ROOT/'work/sprite_consistency_20261105/runtime'
cases=['nana_base_sync','riko_wall_sync','shibuki_fourth_special_sync','rin_wall_sync']
rows=[]
for name in cases:
    sync=json.loads((BASE/name/'synchronization.json').read_text('utf8'))
    obs=json.loads((BASE/name/'observer/evidence.json').read_text('utf8'))
    rec=json.loads((BASE/name/'recording/evidence.json').read_text('utf8'))
    assert sync['input_recording_fully_within_observation'] and rec['error'] is None
    assert all(all(v.values()) for v in obs['resident_assets_still_exact'].values())
    rows.append({'case':name,'project':obs['project'],'session':obs['session'],
        'verified_references':len(obs['verified_bank_frames']),'capture_frames':rec['frames'],
        'unverified_events':obs['unverified_events'],'evidence':str((BASE/name/'synchronization.json').relative_to(ROOT)).replace('\\','/')})
album=ROOT/'out/sprite_consistency_20261105/ALL_SPRITES.html'
assert hashlib.sha256(album.read_bytes()).hexdigest()=='0997b82203efe919b859e0716ba684d160f09c3c2543024117244d0fa4a17fa3'
for row in rows:
    closed=json.loads((ROOT/row['session']/'close.local.json').read_text('utf8'))
    assert closed['exited']
for mode in ('ver_buki_riko','ver_rin_nana'):
    p=ROOT/'projects'/mode/'current_build.json';data=json.loads(p.read_text('utf8'))
    selected=[r for r in rows if r['project']==mode]
    data.update(stage='SPRITE_CONSISTENCY_REPRESENTATIVE_RUNTIME_REVIEW',
        sprite_collection='out/sprite_consistency_20261105/ALL_SPRITES.html',
        sprite_album_report='docs/SPRITE_ALBUM_VALIDATION.md',
        representative_sprite_runtime_verified=True,
        runtime_verification_scope=selected,
        exhaustive_sprite_runtime_verified=False,
        current_session=None,running_bin_sha256=None,
        current_runtime_state='테스트 세션 정상 종료. 원본 F1/메모리카드는 변경하지 않음.',
        last_test_session=selected[-1]['session'],
        next_action='단독 모음집의 대기/전후/연속 재생 비교와 남은 실기 장면 검토. 전수 미술 수용은 별도.')
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
    p=ROOT/'projects'/mode/'project.json';data=json.loads(p.read_text('utf8'))
    data['latest_sprite_album']='out/sprite_consistency_20261105/ALL_SPRITES.html'
    data['sprite_album_validation_report']='docs/SPRITE_ALBUM_VALIDATION.md'
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
report={'cases':rows,'all_input_recordings_synchronized':True,'all_test_sessions_closed':True,
    'album':'out/sprite_consistency_20261105/ALL_SPRITES.html','art_changed_this_followup':False,
    'exhaustive_gameplay_verified':False,'user_art_acceptance':False,
    'remaining_runtime':['Shibuki Fourth ladder-top 183','Nana partial Fourth combinations and save icon','Nana Ultimate arrival 142','all other unsampled moves/forms'],
    'report':'docs/SPRITE_ALBUM_VALIDATION.md'}
(BASE/'review_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(report,ensure_ascii=False))
