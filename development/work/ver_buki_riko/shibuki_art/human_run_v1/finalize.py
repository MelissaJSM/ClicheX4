from pathlib import Path
import json,sys,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest,write_json
out=ROOT/'out/ver_buki_riko/shibuki_run_20261026T082418920727Z';manifest=json.loads((out/'manifest.json').read_text());sha=manifest['modified_bin']['sha256'];assert digest(out/'shibuki_riko.bin')==sha
groups={f'{direction}_{kind}':{} for direction in ['left','right'] for kind in ['run','shoot']};evidence=[]
for f in sorted((ROOT/'work/ver_buki_riko/shibuki_run_runtime').glob('*/verification.local.json')):
 r=json.loads(f.read_text())
 if r['modified_bin_sha256']!=sha or r['idle']:continue
 evidence.append(str(f.relative_to(ROOT)));group=groups[r['direction']+('_shoot' if r['shoot'] else '_run')]
 for n,v in r['frames'].items():
  if not v['verified']:continue
  record={'evidence':str(f.relative_to(ROOT)),'matches':v['matches'],'render_palette_is_base':v.get('render_palette_is_base',True),'display_and_upload_observed_separately':v.get('display_and_upload_observed_separately',False)}
  if n not in group or (not group[n]['render_palette_is_base'] and record['render_palette_is_base']):group[n]=record
for name,g in groups.items():assert set(map(int,g))==set(range(2 if name.endswith('shoot') else 1,33,2)),(name,sorted(g))
runtime={'source_build':str(out.relative_to(ROOT)),'bin_sha256':sha,'groups':groups,'complete_direction_pose_combinations':64,'runtime_verified':True,'all_new_art_accepted_by_user':False,'observations':evidence,'base_idle_frame_zero':str(Path('work/ver_buki_riko/live_poc/20261026T082913305660Z/verification.local.json')),'process_memory_written':False,'save_state_loaded_or_written':False,'shot_palette_flashes_observed':True,'shot_palette_recolor_not_implemented':True,'standing_fire_and_other_actions_not_produced':True,'session':'work/ver_buki_riko/emulator_sessions/20261026T082436050382Z','session_paused':True,'test_notes':'일부 샘플은 전경/총구 섬광/사격 팔레트 변화로 일치하지 않아 다른 시점의 정확한 불투명 픽셀 일치를 수집했다. GPU 표시와 RAM 업로드를 서로 다른 스냅샷에서 검증한 경우 각 증거에 명시했다. 테스트 중 적 공격으로 1회 재등장했으며 사용자 저장은 쓰지 않았다.'}
write_json(out/'runtime_summary.local.json',runtime)
snapshot=out/'previous_pointers';snapshot.mkdir()
for name in ['current_build.json','shibuki_current_build.json','shibuki_run_art_revision.json']:shutil.copy2(ROOT/'projects/ver_buki_riko'/name,snapshot/name)
prior=json.loads((snapshot/'shibuki_current_build.json').read_text(encoding='utf-8'))
pointer={**prior,'kind':manifest['kind'],'build':str(out.relative_to(ROOT)),'cue':str((out/'shibuki_riko.cue').relative_to(ROOT)),'bin_sha256':sha,'session':runtime['session'],'session_closed':False,'session_paused':True,'runtime_summary':str((out/'runtime_summary.local.json').relative_to(ROOT)),'runtime_verified_frames':list(range(1,33)),'both_directions_verified':True,'runtime_verified_directions':['left','right'],'idle_runtime_reverified_frames':[0],'accepted_idle_preserved':True,'moving_shooting_art_applied':True,'new_animation_user_review_pending':True,'current_movement_style_accepted':False,'next_group':'standing_buster_then_air_and_dash','report':'docs/SHIBUKI_HUMAN_RUN.md'}
for name in ['current_build.json','shibuki_current_build.json']:(ROOT/'projects/ver_buki_riko'/name).write_text(json.dumps(pointer,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'projects/ver_buki_riko/shibuki_run_art_revision.json';a=json.loads(p.read_text(encoding='utf-8'));a.update(status='human_run_applied_runtime_verified',native_body='work/ver_buki_riko/shibuki_art/human_run_v1/production04',paired_art='work/ver_buki_riko/shibuki_art/human_run_v1/paired04',candidate_build=str(out.relative_to(ROOT)),game_applied=True,runtime_verified=True,new_art_user_accepted=False,remaining='새 이동 미술 사용자 검토, 정지 버스터 및 공중/대시 등 미제작 동작. 원작 사격 팔레트 섬광의 Shibuki 색상 대응은 후속.')
p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'build':pointer['build'],'sha256':sha,'combinations':64,'runtime_summary':pointer['runtime_summary']}))
