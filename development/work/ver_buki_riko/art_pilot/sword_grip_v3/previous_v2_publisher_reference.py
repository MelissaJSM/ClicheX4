"""Publish this validated candidate and retain the replaced candidate's pointers."""
from assemble_grip import *
from datetime import datetime,timezone
from scripts.discover_inputs import psx_arc
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T054713269447Z'
M=ROOT/'work/ver_buki_riko/production_master/20261024T054745798487Z'
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T054724185163Z'
EXPECTED_HASH='3f4bc2c8112245817397c9a111f1b18ecd06890dfd06d05a59a866e1fd14ea71'
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def read(p):return json.loads(p.read_text('utf8'))
paths={'ground_right':'ground_slash_runtime/20261024T054929205819Z','ground_left':'ground_slash_runtime/20261024T055142791150Z',
 'air_right':'air_slash_runtime/20261024T055322538263Z','air_left':'air_slash_runtime/20261024T055431431533Z','air_left_fill':'air_slash_runtime/20261024T055539801705Z'}
manifest=read(B/'manifest.json');previous=read(ROOT/'projects/ver_buki_riko/current_build.json');prev_manifest=read(ROOT/previous['build']/'manifest.json')
assert manifest['modified_bin']['sha256']==EXPECTED_HASH
assert previous['bin_sha256']=='3d57273eed913b5894c6a3e8aa1696c30e9c37af533c1ffe2673f4a9b9e85353'
unchanged=[int(n) for n,r in manifest['frame_inputs'].items() if prev_manifest['frame_inputs'][n]['sha256']==r['sha256']]
assert len(unchanged)==90 and not manifest.get('sword_effect_edits')
oldarc=(ROOT/previous['build']/'modified.arc').read_bytes();newarc=(B/'modified.arc').read_bytes()
for a,b in zip(psx_arc(oldarc),psx_arc(newarc)):
 assert all(a[k]==b[k] for k in ('index','type','offset','size'))
 if a['type']!='0x2':assert oldarc[a['offset']:a['offset']+a['size']]==newarc[b['offset']:b['offset']+b['size']]
data={'right':set(),'left':set()};full={'right':set(),'left':set()};visible={'right':set(),'left':set()};summary={}
for label,path in paths.items():
 folder=ROOT/'work/ver_buki_riko'/path;r=read(folder/'verification.local.json');c=read(folder/'grip_composite_verification.json');side='right' if 'right' in label else 'left'
 assert r['pid']==14460 and r['modified_bin_sha256']==EXPECTED_HASH and c['bin_sha256']==EXPECTED_HASH
 loaded={int(n) for n,v in r['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in v['samples'])}
 rendered=set(r['verified_frames'])|set(r['pipeline_verified_frames']);seen={r['body_frame'] for r in c['frames'] if r['whole_composite_verified']}
 data[side]|=loaded;full[side]|=rendered;visible[side]|=seen
 summary[label]={'report':rel(folder/'verification.local.json'),'composite_report':rel(folder/'grip_composite_verification.json'),'data_loaded':sorted(loaded),'full_body_render':sorted(rendered),'visible_composite':sorted(seen)}
assert set(BODY)<=data['right'] and set(BODY)<=data['left']
assert 229 in full['right'] and 229 in full['left']
V=B/('grip_validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));V.mkdir()
summary.update({'build':rel(B),'bin_sha256':EXPECTED_HASH,'source_sha256':manifest['source_sha256'],'changed_body_frames':BODY,
 'all_attack_body_data_verified_both_directions':True,'full_body_render_union':sorted(full['right']|full['left']),
 'full_body_render_both':sorted(full['right']&full['left']),'visible_composite_union':sorted(visible['right']|visible['left']),
 'visible_composite_both':sorted(visible['right']&visible['left']),
 'attack_body_full_render_missing':sorted(set(BODY)-(full['right']|full['left'])),
 'visible_composite_missing':sorted(set(BODY)-(visible['right']|visible['left'])),
 'all_50_effect_indices_identical_to_game_original':True,'unchanged_from_previous_candidate_png_references':unchanged,
 'non_graphics_arc_entries_identical_to_previous_candidate':True,'no_logic_timing_palette_composition_layout_change':True,
 'unit_tests_passed':64,'process_memory_written':False,'save_state_loaded_by_agent':False,'character_id_observed':1,
 'character_selection_screen_fully_observed':False,'new_art_user_review_pending':True})
write(V/'runtime_summary.json',summary)
board=Image.new('RGB',(3*384,2*352),(35,40,50));draw=ImageDraw.Draw(board);evidence=[]
for row,side in enumerate(('right','left')):
 for col,n in enumerate((101,127,229)):
  label=('air_' if n>=200 else 'ground_')+side;folder=ROOT/'work/ver_buki_riko'/paths[label];report=read(folder/'grip_composite_verification.json')
  r=next(r for r in report['frames'] if r['body_frame']==n);e=r['evidence'][0];match=e['matches'][0]
  screen=Image.open(folder/e['actual']);sprite=Image.open(folder/f'grip_composite_expected_{n:03d}.png')
  cx=match['x']+sprite.width//2;cy=match['y']+sprite.height//2;box=(cx-48,cy-40,cx+48,cy+40)
  board.paste(screen.crop(box).resize((384,320),Image.Resampling.NEAREST),(col*384,row*352+32))
  draw.text((col*384+8,row*352+10),f'ACTUAL {side} {n} / SHORT GRIP',fill='white')
  evidence.append({'side':side,'frame':n,'source':rel(folder/e['actual']),'box':box,'integer_scale':4,'one_pixel_corruption_rejected':e['one_pixel_corruption_rejected']})
board.save(V/'actual_grip_gallery.png');write(V/'gallery_sources.json',evidence)
recording=S/'grip_air_left_fill_recording';assert read(recording/'recording.json')['bin_sha256']==EXPECTED_HASH
shutil.copyfile(recording/'actual_air_left.gif',V/'actual_air_left.gif');shutil.copyfile(recording/'recording.json',V/'actual_air_left_recording.json')
for name in ('current_build.json','art_selection.json','master_sheet.json'):shutil.copyfile(ROOT/'projects/ver_buki_riko'/name,V/('previous_'+name))
shutil.copyfile(ROOT/'docs/STATUS.md',V/'previous_STATUS.md')
for name in ('guard_checks.json','packing_checks.json','registration.json','grip_master.json'):shutil.copyfile(D/name,V/name)
known_before=set(previous['runtime_verified_frames'])|set(previous['runtime_inherited_unchanged_frames']);inherited=known_before&set(unchanged)
body_ids=set(map(int,manifest['frame_inputs']))-SABER_EFFECT_FRAMES;known=full['right']|full['left']|inherited
cur={**previous,'kind':'riko_short_grip_original_trail_candidate','build':rel(B),'cue':rel(B/'riko_motion.cue'),'bin_sha256':EXPECTED_HASH,
 'previous_build':previous['build'],'previous_bin_sha256':previous['bin_sha256'],'session':rel(S),'session_closed':False,
 'boot_navigation_fully_observed':False,'zero_selection_observed':False,'runtime_character_id_verified':1,
 'motion_set':rel(Path(manifest['motion_set'])),'runtime_summary':rel(V/'runtime_summary.json'),'runtime_previous_summary':previous['runtime_summary'],
 'runtime_verified_frames':summary['full_body_render_union'],'runtime_inherited_unchanged_frames':sorted(inherited),
 'runtime_unverified_current_build_frames':sorted(body_ids-(full['right']|full['left'])),
 'runtime_unverified_any_evidence_frames':sorted(body_ids-known),'runtime_visible_composite_frames':summary['visible_composite_union'],
 'all_current_frames_preview':rel(M/'riko_master_preview_2x.png'),'sword_art':rel(D),'sword_art_user_review_pending':True,
 'sword_body_references':58,'sword_effect_references':0,'original_saber_effect_references_preserved':50,
 'existing_56_frames_byte_preserved':True,'next_task':'Review short grip and original trail connection; then continue Riko ladder/wall saber',
 'report':'docs/RIKO_SWORD_GRIP.md','session_state_evidence':None,'session_state_at_last_observation':'Paused by final normal input plan; final window capture pending',
 'ground_slash_runtime_full_render_unverified':sorted(set(GROUND_SLASH_BODY_FRAMES)-(full['right']|full['left'])),
 'air_slash_full_render_unverified':sorted(set(AIR_SLASH_BODY_FRAMES)-(full['right']|full['left'])),
 'sword_visible_gallery':rel(V/'actual_grip_gallery.png'),'sword_actual_animation':rel(V/'actual_air_left.gif')}
write(ROOT/'projects/ver_buki_riko/current_build.json',cur)
art=read(ROOT/'projects/ver_buki_riko/art_selection.json');art.update({'status':'short_grip_candidate_user_review_pending',
 'game_applied_scope':'114 body references; short grip on58 attack bodies; all50 original saber effects restored;58 body data verified both directions',
 'runtime_verified_build':rel(B),'runtime_summary':rel(V/'runtime_summary.json'),'runtime_evidence':'docs/RIKO_SWORD_GRIP.md',
 'historical_selection_snapshot':rel(V/'previous_art_selection.json'),'runtime_verified_frame_scope':summary['full_body_render_union'],
 'sword_art_directory':rel(D),'sword_style_user_review_pending':True,'full_sword_candidate_rejected_by_user':True})
write(ROOT/'projects/ver_buki_riko/art_selection.json',art)
ms=read(ROOT/'projects/ver_buki_riko/master_sheet.json');ms.update({'source_build':rel(B),'source_bin_sha256':EXPECTED_HASH,'directory':rel(M),
 'master':rel(M/'master.local.json'),'sheet':rel(M/'riko_master_indexed.png'),'preview':rel(M/'riko_master_preview_2x.png'),
 'roundtrip':'work/ver_buki_riko/master_split/20261024T054758983759Z/validation.local.json','guard_checks':rel(D/'guard_checks.json'),
 'report':'docs/RIKO_SWORD_GRIP.md','preserved_effect_reference_count':50,'custom_sword_effect_reference_count':0,
 'sword_effects_bound_to_recipe':rel(D/'recipe.json'),'sword_art_review_pending':True,'next_group':'short_grip_review_then_ladder_wall_saber'})
write(ROOT/'projects/ver_buki_riko/master_sheet.json',ms)
write(D/'publication.json',{'build':rel(B),'validation':rel(V),'master':rel(M),'runtime_summary':rel(V/'runtime_summary.json')})
print(json.dumps({'validation':rel(V),'body_render':len(set(BODY)&(full['right']|full['left'])),'visible_composite':len(visible['right']|visible['left']),
 'visible_composite_both':len(visible['right']&visible['left']),'missing_body':summary['attack_body_full_render_missing']}))
