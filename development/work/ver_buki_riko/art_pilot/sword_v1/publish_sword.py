from review_sword import *
from scripts.discover_inputs import sha256,psx_arc
from scripts.build_riko_idle import SABER_EFFECT_FRAMES,GROUND_SLASH_BODY_FRAMES,AIR_SLASH_BODY_FRAMES
from datetime import datetime,timezone
import shutil
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T051717203361Z'
M=ROOT/'work/ver_buki_riko/production_master/20261024T051751685069Z'
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T051730386287Z'
V=B/('sword_validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));V.mkdir()
def rel(p):return str(Path(p).relative_to(ROOT)).replace('\\','/')
def read(p):return json.loads(p.read_text('utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
paths={'ground_right':'ground_slash_runtime/20261024T051931592679Z','ground_left':'ground_slash_runtime/20261024T052023314767Z',
 'air_right':'air_slash_runtime/20261024T052140879934Z','air_left':'air_slash_runtime/20261024T052228986527Z','air_left_fill':'air_slash_runtime/20261024T052455338074Z'}
summary={};data={'right':set(),'left':set()};full={'right':set(),'left':set()};composite={'right':set(),'left':set()}
for label,p in paths.items():
 folder=ROOT/'work/ver_buki_riko'/p;r=read(folder/'verification.local.json');c=read(folder/'sword_composite_verification.json');side='right' if 'right' in label else 'left'
 assert r['pid']==36860 and r['modified_bin_sha256']=='3d57273eed913b5894c6a3e8aa1696c30e9c37af533c1ffe2673f4a9b9e85353'
 loaded={int(n) for n,v in r['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in v['samples'])}
 rendered=set(r['verified_frames'])|set(r['pipeline_verified_frames']);visible={v['body_frame'] for v in c['frames'] if v['whole_composite_verified']}
 data[side]|=loaded;full[side]|=rendered;composite[side]|=visible
 summary[label]={'report':rel(folder/'verification.local.json'),'composite_report':rel(folder/'sword_composite_verification.json'),'data_loaded':sorted(loaded),'full_body_render':sorted(rendered),'visible_body_weapon_effect_composite':sorted(visible)}
assert set(BODY)<=data['right'] and set(BODY)<=data['left']
manifest=read(B/'manifest.json');oldcur=read(ROOT/'projects/ver_buki_riko/current_build.json');oldB=ROOT/oldcur['build'];oldmanifest=read(oldB/'manifest.json')
unchanged=[int(n) for n,r in manifest['frame_inputs'].items() if oldmanifest['frame_inputs'][n]['sha256']==r['sha256']]
assert len(unchanged)==90
oldarc=(oldB/'modified.arc').read_bytes();newarc=(B/'modified.arc').read_bytes()
for oe,ne in zip(psx_arc(oldarc),psx_arc(newarc)):
 assert all(oe[k]==ne[k] for k in ('index','type','offset','size'))
 if oe['type']!='0x2':assert oldarc[oe['offset']:oe['offset']+oe['size']]==newarc[ne['offset']:ne['offset']+ne['size']]
summary.update({'build':rel(B),'bin_sha256':manifest['modified_bin']['sha256'],'source_sha256':manifest['source_sha256'],
 'body_weapon_frames':BODY,'body_weapon_loaded_both_directions':True,'full_body_render_union':sorted(full['right']|full['left']),
 'full_body_render_both':sorted(full['right']&full['left']),'visible_composite_union':sorted(composite['right']|composite['left']),
 'visible_composite_both':sorted(composite['right']&composite['left']),'body_full_render_missing':sorted(set(BODY)-(full['right']|full['left'])),
 'visible_composite_missing':sorted(set(BODY)-(composite['right']|composite['left'])),
 'palette_composition_and_non_graphics_arc_entries_identical_to_previous_build':True,'unchanged_png_references':unchanged,
 'no_logic_timing_or_disc_layout_change':True,'unit_tests_passed':64,'process_memory_written':False,'new_art_user_review_pending':True,
 'save_state_loaded_by_agent':False,'character_id_observed':1,'character_selection_screen_observed_this_session':False,
 'prototype_not_published':{'build':'out/ver_buki_riko/riko_motion_20261024T051229895680Z','reason':'Thin blade and several disconnected palm anchors corrected before the final build'}})
# Actual framebuffer crops, never composited into a game background.
board=Image.new('RGB',(5*288,2*264),(35,40,50));draw=ImageDraw.Draw(board);evidence=[]
for row,side in enumerate(('right','left')):
 for col,n in enumerate((71,93,127,229,246)):
  label=('ground_' if n<200 else 'air_')+side;folder=ROOT/'work/ver_buki_riko'/paths[label];c=read(folder/'sword_composite_verification.json')
  r=next(r for r in c['frames'] if r['body_frame']==n);e=r['evidence'][0];m=e['matches'][0];screen=Image.open(folder/e['actual']);sprite=Image.open(folder/f'sword_composite_expected_{n:03d}.png')
  cx=m['x']+sprite.width//2;cy=m['y']+sprite.height//2;box=(cx-48,cy-40,cx+48,cy+40)
  crop=screen.crop(box).resize((288,240),Image.Resampling.NEAREST);board.paste(crop,(col*288,row*264+24));draw.text((col*288+6,row*264+6),f'ACTUAL {side} {n}',fill='white')
  altered=np.array(sprite.convert('RGBA'));ys,xs=np.nonzero(altered[:,:,3]);y,x=ys[len(ys)//2],xs[len(xs)//2];altered[y,x,0]^=127
  assert not match_sprite(screen,Image.fromarray(altered)),'One-pixel corruption accepted'
  evidence.append({'side':side,'frame':n,'source':rel(folder/e['actual']),'box':box,'integer_scale':3,'one_pixel_corruption_rejected':True})
board.save(V/'actual_sword_gallery.png');write(V/'gallery_sources.json',evidence)
write(V/'runtime_summary.json',summary)
for name in ('current_build.json','art_selection.json','master_sheet.json'):shutil.copyfile(ROOT/'projects/ver_buki_riko'/name,V/('previous_'+name))
shutil.copyfile(ROOT/'docs/STATUS.md',V/'previous_STATUS.md')
for name in ('guard_checks.json','attachment_checks.json','packing_checks.json','sword_master.json'):shutil.copyfile(D/name,V/name)
prior_known=set(oldcur['runtime_verified_frames'])|set(oldcur['runtime_inherited_unchanged_frames']);inherited=prior_known&set(unchanged);known=full['right']|full['left']|inherited
cur={**oldcur,'kind':'riko_held_sword_ground_air_slash_candidate','build':rel(B),'cue':rel(B/'riko_motion.cue'),'bin_sha256':manifest['modified_bin']['sha256'],
 'previous_build':oldcur['build'],'previous_bin_sha256':oldcur['bin_sha256'],'session':rel(S),'session_closed':False,
 'boot_navigation_fully_observed':False,'zero_selection_observed':False,'runtime_character_id_verified':1,
 'motion_set':rel(Path(manifest['motion_set'])),'runtime_summary':rel(V/'runtime_summary.json'),'runtime_previous_summary':oldcur['runtime_summary'],
 'runtime_verified_frames':summary['full_body_render_union'],'runtime_inherited_unchanged_frames':sorted(inherited),
 'runtime_unverified_any_evidence_frames':sorted(set(map(int,manifest['frame_inputs']))-SABER_EFFECT_FRAMES-known),
 'runtime_visible_composite_frames':summary['visible_composite_union'],
 'all_current_frames_preview':rel(M/'riko_master_preview_2x.png'),'sword_art':rel(D),'sword_art_user_review_pending':True,
 'sword_body_references':58,'sword_effect_references':16,'existing_96_body_frames_byte_preserved':False,
 'existing_56_frames_byte_preserved':True,'next_task':'Review held sword appearance; then continue ladder/wall saber within Riko scope',
 'report':'docs/RIKO_SWORD.md','session_state_evidence':rel(S/'20261024T052438039832Z.png'),
 'ground_slash_runtime_full_render_unverified':sorted(set(GROUND_SLASH_BODY_FRAMES)-(full['right']|full['left'])),
 'air_slash_full_render_unverified':sorted(set(AIR_SLASH_BODY_FRAMES)-(full['right']|full['left'])),
 'air_slash_body_loaded_both_directions':True,'sword_visible_gallery':rel(V/'actual_sword_gallery.png')}
write(ROOT/'projects/ver_buki_riko/current_build.json',cur)
art=read(ROOT/'projects/ver_buki_riko/art_selection.json');art.update({'status':'held_sword_candidate_user_review_pending','game_applied_scope':'114 body references; sword added to58 body and16 effect references; all58 body data verified both directions',
 'runtime_verified_build':rel(B),'runtime_summary':rel(V/'runtime_summary.json'),'runtime_evidence':'docs/RIKO_SWORD.md','historical_selection_snapshot':rel(V/'previous_art_selection.json'),
 'runtime_verified_frame_scope':summary['full_body_render_union'],'sword_production_implemented':True,'sword_art_directory':rel(D),'sword_style_user_review_pending':True})
write(ROOT/'projects/ver_buki_riko/art_selection.json',art)
ms=read(ROOT/'projects/ver_buki_riko/master_sheet.json');ms.update({'source_build':rel(B),'source_bin_sha256':manifest['modified_bin']['sha256'],'directory':rel(M),'master':rel(M/'master.local.json'),
 'sheet':rel(M/'riko_master_indexed.png'),'preview':rel(M/'riko_master_preview_2x.png'),
 'roundtrip':'work/ver_buki_riko/master_split/20261024T051803315438Z/validation.local.json','guard_checks':rel(D/'guard_checks.json'),
 'report':'docs/RIKO_SWORD.md','preserved_effect_reference_count':34,'custom_sword_effect_reference_count':16,'sword_effects_bound_to_recipe':rel(D/'recipe.json'),
 'sword_art_review_pending':True,'next_group':'held_sword_review_then_ladder_wall_saber'})
write(ROOT/'projects/ver_buki_riko/master_sheet.json',ms)
write(D/'publication.json',{'build':rel(B),'validation':rel(V),'master':rel(M),'summary':rel(V/'runtime_summary.json')})
print(json.dumps({'validation':rel(V),'body_render':len(set(BODY)&set(summary['full_body_render_union'])),'composite':len(summary['visible_composite_union']),'composite_both':len(summary['visible_composite_both']),'missing_body':summary['body_full_render_missing'],'missing_composite':summary['visible_composite_missing']}))
