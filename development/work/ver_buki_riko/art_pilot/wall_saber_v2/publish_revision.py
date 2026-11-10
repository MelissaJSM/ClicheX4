"""Publish this specific revision once, preserving previous pointers and evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from src.epsxe_state import match_sprite
D=Path(__file__).parent;L=D.parent/'low_hp_v1';B=ROOT/'out/ver_buki_riko/riko_bank1_20261024T074353134413Z';OLD=ROOT/'out/ver_buki_riko/riko_bank1_20261024T072210847890Z'
M=ROOT/'work/ver_buki_riko/production_master/20261024T074522966534Z';SPLIT=ROOT/'work/ver_buki_riko/master_split/20261024T074530467893Z/validation.local.json'
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T074619623607Z'
LOW=[ROOT/'work/ver_buki_riko/low_hp_idle_runtime'/n for n in ['20261024T075217998526Z','20261024T075308211385Z']]
WALL=ROOT/'work/ver_buki_riko/wall_saber_runtime/20261024T080232751248Z'
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
if (D/'publication.json').exists():raise ValueError('Already published; use a new evidence revision')
manifest=json.loads((B/'manifest.json').read_text());assert digest(B/'riko_motion.bin')==manifest['modified_bin']['sha256']
split=json.loads(SPLIT.read_text());assert split['archive_byte_identical'] and len(split['png_byte_identical_frames'])==162
V=B/('wall_low_hp_validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));V.mkdir()
for path in ['projects/ver_buki_riko/current_build.json','projects/ver_buki_riko/art_selection.json','projects/ver_buki_riko/master_sheet.json','docs/STATUS.md']:
 p=ROOT/path;shutil.copyfile(p,V/('previous_'+p.name))
for name in ['recipe.json','guard_checks.json','packing_checks.json','art_checks.json','preservation_audit.json','unit_tests.log','generation_prompt.txt','transition_review.png','wall_transition_offline.gif','render_diagnostic.png','render_diagnostic.json','reach_low_hp.json','controlled_right_high_inputs.json']:
 shutil.copyfile(D/name,V/name)
for name in ['body_review.png','low_hp_offline.gif','generation_prompt.txt','packing_checks.json','art_checks.json','original_roundtrip.json']:
 shutil.copyfile(L/name,V/('low_hp_'+name))
directions={};negative=[];board=Image.new('RGB',(960,520),(25,32,42));draw=ImageDraw.Draw(board)
for i,p in enumerate(LOW):
 report=json.loads((p/'verification.local.json').read_text());assert report['modified_bin_sha256']==manifest['modified_bin']['sha256']
 for n in range(149,155):
  rec=report['frames'][str(n)];assert rec['verified'];directions.setdefault(str(n),set()).update(m['flip_x'] for m in rec['matches'])
  page=rec['matches'][0]['page_y'];actual=Image.open(p/f'actual_{n:03d}_{page}.png').convert('RGB');expected=Image.open(p/f'expected_{n:03d}.png').convert('RGBA');assert match_sprite(actual,expected)
  altered=expected.copy();xy=next((x,y) for y in range(altered.height) for x in range(altered.width) if altered.getpixel((x,y))[3]);altered.putpixel(xy,(255,0,255,255));assert not match_sprite(actual,altered)
  negative.append({'runtime':rel(p),'frame':n,'one_pixel_corruption_rejected':True})
  if n in (149,151,152):
   j=(149,151,152).index(n);board.paste(actual,(j*320,i*260+20));draw.text((j*320+4,i*260+3),f'Actual low HP {n}, flip={rec["matches"][0]["flip_x"]}',fill='white')
assert all(v=={False,True} for v in directions.values());board.save(V/'actual_low_hp_both_directions.png')
wr=json.loads((WALL/'verification.local.json').read_text());assert wr['modified_bin_sha256']==manifest['modified_bin']['sha256']
loaded=sorted(int(n) for n,r in wr['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in r['samples']))
assert loaded==[50,51,53,54,56,57,59,61,63,65]
summary={'build':rel(B),'bin_sha256':manifest['modified_bin']['sha256'],'body_references':162,'preserved_effect_references':63,
 'previous_bank0_png_count_unchanged':203,'new_low_hp_body_frames':list(range(149,155)),'revised_wall_body_frames':loaded,
 'master':rel(M),'master_roundtrip':rel(SPLIT),'unit_tests_passed':74,'bank1_guard_cases_rejected':10,
 'low_hp_runtime_reports':[rel(p/'verification.local.json') for p in LOW],'low_hp_full_opaque_verified_flip_flags':{n:sorted(v) for n,v in directions.items()},
 'low_hp_negative_controls':negative,'wall_runtime_report':rel(WALL/'verification.local.json'),'wall_ram_vram_palette_verified':loaded,
 'wall_full_opaque_verified':wr['verified_frames'],'wall_pipeline_verified':wr['pipeline_verified_frames'],'wall_left_surface_verified':False,
 'wall_visual_review':'Matches side-view identity and common compact body; wall dust occludes boots. Full opaque verification remains incomplete.',
 'failed_or_partial_attempts':['low_hp_idle_runtime/20261024T075010395063Z','wall_saber_runtime/20261024T075731875040Z','wall_saber_runtime/20261024T075818702897Z','wall_saber_runtime/20261024T075920767031Z','wall_saber_runtime/20261024T080134442996Z'],
 'additional_wall_loading_evidence':'work/ver_buki_riko/wall_saber_runtime/20261024T080048583249Z/verification.local.json',
 'session':rel(S),'agent_loaded_save_state':False,'process_memory_written':False,'boot_navigation_continuously_observed':False,
 'excluded_x_session':'work/ver_buki_riko/emulator_sessions/20261024T074419112233Z','style_review_pending':True,'whole_character_completed':False}
write(V/'runtime_summary.json',summary)
pointer=json.loads((ROOT/'projects/ver_buki_riko/current_build.json').read_text('utf8'));old=json.loads((OLD/'manifest.json').read_text())
pointer.update(kind='riko_wall_continuity_and_low_hp_revision',build=rel(B),cue=rel(B/'riko_motion.cue'),bin_sha256=manifest['modified_bin']['sha256'],
 previous_build=rel(OLD),previous_bin_sha256=old['modified_bin']['sha256'],previous_pointer_snapshot=rel(V/'previous_current_build.json'),
 runtime_summary=rel(V/'runtime_summary.json'),runtime_verified_frames=[147,*range(149,155)],session=rel(S),session_closed=False,
 riko_reference_count=162,original_saber_effect_references_preserved=63,motion_set=rel(L/'motion_set.json'),bank1_set=rel(D/'recipe.json'),
 all_current_frames_preview=rel(M/'riko_master_preview_2x.png'),bank1_ram_vram_verified_frames=loaded,bank1_full_framebuffer_verified_frames=wr['verified_frames'],
 wall_saber_style_user_review_pending=True,user_flagged_wall_transition_quality=True,wall_transition_revision_applied=True,
 low_hp_idle_original_frames=[],low_hp_runtime_verified_frames=list(range(149,155)),low_hp_both_directions_verified=True,
 next_task='Verify opposite wall and occluded wall rendering; continue ladder runtime and remaining Riko damage/death/special groups',
 report='docs/RIKO_WALL_LOW_HP_REVISION.md',session_state_at_last_observation='Paused Zero menu after wall verification; HP17',session_state_evidence=None)
write(ROOT/'projects/ver_buki_riko/current_build.json',pointer)
master=json.loads((ROOT/'projects/ver_buki_riko/master_sheet.json').read_text('utf8'));master.update(source_build=rel(B),source_bin_sha256=manifest['modified_bin']['sha256'],
 directory=rel(M),master=rel(M/'master.local.json'),sheet=rel(M/'riko_master_indexed.png'),preview=rel(M/'riko_master_preview_2x.png'),roundtrip=rel(SPLIT),
 guard_checks=rel(V/'guard_checks.json'),riko_references=162,low_hp_idle_frames_missing=[],next_group='remaining_runtime_damage_death_specials',report='docs/RIKO_WALL_LOW_HP_REVISION.md')
write(ROOT/'projects/ver_buki_riko/master_sheet.json',master)
selection=json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text('utf8'));selection.update(latest_candidate_build=rel(B),wall_saber_art_directory=rel(D),
 wall_saber_style_user_review_pending=True,wall_saber_runtime_summary=rel(V/'runtime_summary.json'),wall_saber_transition_revision_applied=True,
 low_hp_art_directory=rel(L),low_hp_style_user_review_pending=True,low_hp_runtime_summary=rel(V/'runtime_summary.json'))
selection['runtime_limitations']['low_hp_idle_original_remaining']=[];selection['runtime_limitations']['wall_saber_full_render_unverified']=loaded
write(ROOT/'projects/ver_buki_riko/art_selection.json',selection)
write(D/'publication.json',{'build':rel(B),'validation':rel(V),'master':rel(M),'split':rel(SPLIT)})
print(json.dumps({'validation':rel(V),'body':162,'low_hp_both_directions':True,'wall_loaded':loaded}))
