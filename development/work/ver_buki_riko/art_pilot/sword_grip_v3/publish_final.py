"""Publish the eight-pixel joint correction with explicit inherited evidence."""
from assemble_grip import *
from datetime import datetime,timezone
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T060039320512Z'
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T060107975803Z'
M=ROOT/'work/ver_buki_riko/production_master/20261024T060117997478Z'
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def read(p):return json.loads(p.read_text('utf8'))
curpath=ROOT/'projects/ver_buki_riko/current_build.json';prev=read(curpath);pm=read(ROOT/prev['build']/'manifest.json');manifest=read(B/'manifest.json')
assert prev['bin_sha256']=='3f4bc2c8112245817397c9a111f1b18ecd06890dfd06d05a59a866e1fd14ea71'
changed={int(n) for n,r in manifest['frame_inputs'].items() if r['sha256']!=pm['frame_inputs'][n]['sha256']}
assert changed=={111,213,223,232,240,242,244}
prior=read(ROOT/prev['runtime_summary']);data={s:set() for s in ('right','left')};full={s:set() for s in data};visible={s:set() for s in data}
newfull=set();newvisible=set();reports={};folders={}
for label in ('ground_right','ground_left','air_right','air_left'):
 path=Path(read(S/(label+'_capture.stdout'))['output']);folders[label]=path;r=read(path/'verification.local.json');c=read(path/'grip_composite_verification.json');side=label.split('_')[1]
 assert r['pid']==48344 and r['modified_bin_sha256']==manifest['modified_bin']['sha256']
 loaded={int(n) for n,v in r['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in v['samples'])}
 rendered=set(r['verified_frames'])|set(r['pipeline_verified_frames']);seen={v['body_frame'] for v in c['frames'] if v['whole_composite_verified']}
 data[side]|=loaded;full[side]|=rendered;visible[side]|=seen;newfull|=rendered;newvisible|=seen
 reports[label]={'report':rel(path/'verification.local.json'),'composite_report':rel(path/'grip_composite_verification.json'),'data_loaded':sorted(loaded),'full_body_render':sorted(rendered),'visible_composite':sorted(seen)}
for side in data:assert changed<=data[side] and 229 in full[side]
for label,r in prior.items():
 if not isinstance(r,dict) or 'data_loaded' not in r:continue
 side='right' if 'right' in label else 'left'
 data[side]|=set(r['data_loaded'])-changed;full[side]|=set(r['full_body_render'])-changed;visible[side]|=set(r['visible_composite'])-changed
V=B/('grip_validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));V.mkdir()
for name in ('current_build.json','art_selection.json','master_sheet.json'):shutil.copyfile(ROOT/'projects/ver_buki_riko'/name,V/('previous_'+name))
shutil.copyfile(ROOT/'docs/STATUS.md',V/'previous_STATUS.md')
summary={**reports,'build':rel(B),'bin_sha256':manifest['modified_bin']['sha256'],'previous_evidence':prev['runtime_summary'],
 'changed_from_previous':sorted(changed),'changed_pixels':sum(len(r['joint_fills']) for r in read(D/'registration.json')),
 'unchanged_previous_evidence_inherited_only_after_png_hash_comparison':True,'all58_attack_data_verified_both_including_inherited':all(set(BODY)<=v for v in data.values()),
 'current_build_full_body_render':sorted(newfull),'current_build_visible_composite':sorted(newvisible),
 'combined_full_body_render_union':sorted(full['right']|full['left']),'combined_visible_composite_union':sorted(visible['right']|visible['left']),
 'combined_visible_composite_both':sorted(visible['right']&visible['left']),
 'missing_full_body_render':sorted(set(BODY)-(full['right']|full['left'])),'missing_visible_composite':sorted(set(BODY)-(visible['right']|visible['left'])),
 'all50_effect_indices_original':True,'unit_tests_passed':64,'character_id_observed':1,'zero_selected_screen_observed':True,
 'zero_selection_screen_evidence':rel(S/'20261024T060132390867Z.png'),'full_boot_navigation_observed':False,'process_memory_written':False,'save_state_loaded_by_agent':False}
write(V/'runtime_summary.json',summary)
board=Image.new('RGB',(768,704),(35,40,50));draw=ImageDraw.Draw(board);evidence=[]
oldgallery=read(ROOT/'out/ver_buki_riko/riko_motion_20261024T051717203361Z/sword_validation_20261024T052807279613Z/gallery_sources.json')
for row,side in enumerate(('right','left')):
 oldr=next(r for r in oldgallery if r['frame']==229 and r['side']==side)
 board.paste(Image.open(ROOT/oldr['source']).crop(oldr['box']).resize((384,320),Image.Resampling.NEAREST),(0,row*352+32))
 draw.text((8,row*352+10),f'PREVIOUS FULL BLADE {side} 229',fill='white')
 folder=folders['air_'+side];r=next(r for r in read(folder/'grip_composite_verification.json')['frames'] if r['body_frame']==229);e=r['evidence'][0];m=e['matches'][0]
 sprite=Image.open(folder/'grip_composite_expected_229.png');cx=m['x']+sprite.width//2;cy=m['y']+sprite.height//2;box=(cx-48,cy-40,cx+48,cy+40)
 board.paste(Image.open(folder/e['actual']).crop(box).resize((384,320),Image.Resampling.NEAREST),(384,row*352+32))
 draw.text((392,row*352+10),f'ACTUAL SHORT GRIP {side} 229',fill='white');evidence.append({'side':side,'frame':229,'source':rel(folder/e['actual']),'box':box,'integer_scale':4,'one_pixel_corruption_rejected':e['one_pixel_corruption_rejected']})
board.save(V/'actual_229_comparison.png');write(V/'gallery_sources.json',evidence)
recording=S/'grip_air_left_recording';shutil.copyfile(recording/'actual_air_left.gif',V/'actual_air_left.gif');shutil.copyfile(recording/'recording.json',V/'actual_air_left_recording.json')
for name in ('guard_checks.json','packing_checks.json','registration.json','grip_master.json'):shutil.copyfile(D/name,V/name)
inherited=(set(prev['runtime_verified_frames'])|set(prev['runtime_inherited_unchanged_frames']))-changed
ids=set(map(int,manifest['frame_inputs']))-SABER_EFFECT_FRAMES;known=inherited|newfull
cur={**prev,'build':rel(B),'cue':rel(B/'riko_motion.cue'),'bin_sha256':manifest['modified_bin']['sha256'],'previous_build':prev['build'],'previous_bin_sha256':prev['bin_sha256'],
 'session':rel(S),'session_closed':False,'zero_selection_observed':True,'motion_set':rel(Path(manifest['motion_set'])),
 'runtime_summary':rel(V/'runtime_summary.json'),'runtime_previous_summary':prev['runtime_summary'],'runtime_verified_frames':sorted(newfull),'runtime_inherited_unchanged_frames':sorted(inherited),
 'runtime_unverified_current_build_frames':sorted(ids-newfull),'runtime_unverified_any_evidence_frames':sorted(ids-known),
 'runtime_visible_composite_frames':sorted(newvisible),'runtime_inherited_visible_composite_frames':sorted((set(prior['visible_composite_union'])-changed)-newvisible),
 'all_current_frames_preview':rel(M/'riko_master_preview_2x.png'),'sword_art':rel(D),'sword_visible_gallery':rel(V/'actual_229_comparison.png'),'sword_actual_animation':rel(V/'actual_air_left.gif'),
 'session_state_evidence':None,'session_state_at_last_observation':'Paused by final normal input plan; final capture pending',
 'ground_slash_runtime_full_render_unverified':sorted(GROUND_SLASH_BODY_FRAMES-(full['right']|full['left'])),
 'air_slash_full_render_unverified':sorted(AIR_SLASH_BODY_FRAMES-(full['right']|full['left']))}
write(curpath,cur)
artpath=ROOT/'projects/ver_buki_riko/art_selection.json';a=read(artpath);a.update({'runtime_verified_build':rel(B),'runtime_summary':rel(V/'runtime_summary.json'),'historical_selection_snapshot':rel(V/'previous_art_selection.json'),'runtime_verified_frame_scope':sorted(newfull),'sword_art_directory':rel(D),'game_applied_scope':'114body;58 short grips;50 original effects; seven joint corrections verified both directions, other evidence inherited only for identical PNGs'});write(artpath,a)
msp=ROOT/'projects/ver_buki_riko/master_sheet.json';ms=read(msp);ms.update({'source_build':rel(B),'source_bin_sha256':manifest['modified_bin']['sha256'],'directory':rel(M),'master':rel(M/'master.local.json'),'sheet':rel(M/'riko_master_indexed.png'),'preview':rel(M/'riko_master_preview_2x.png'),'roundtrip':'work/ver_buki_riko/master_split/20261024T060148623552Z/validation.local.json','guard_checks':rel(D/'guard_checks.json'),'sword_effects_bound_to_recipe':rel(D/'recipe.json')});write(msp,ms)
write(D/'publication.json',{'build':rel(B),'validation':rel(V),'master':rel(M),'runtime_summary':rel(V/'runtime_summary.json')})
print(json.dumps({'validation':rel(V),'body_verified_with_inheritance':len(set(BODY)&(full['right']|full['left'])),'visible_composite_with_inheritance':len(visible['right']|visible['left']),'visible_composite_both':len(visible['right']&visible['left']),'current_full_body':sorted(newfull)}))
