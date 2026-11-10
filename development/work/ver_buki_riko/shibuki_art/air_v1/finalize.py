"""실행 증거를 검증한 뒤 이 시험본을 현재 포인터에 등록한다. 일회성 기록."""
import sys,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest,write_json
d=Path(__file__).parent;a=d/'production03';build=ROOT/'out/ver_buki_riko/shibuki_air_20261026T101950094985Z';m=json.loads((build/'manifest.json').read_text());expected='817cef402adbc05b9fecce6e28eb1a7b2749ac724bd2becd7896e55520d3b120'
assert digest(build/'shibuki_riko.bin')==expected
recipe=ROOT/'work/ver_buki_riko/shibuki_air/20261026T102325213749Z/recipe.json'
for name in ('20261026T101929411084Z','20261026T101950879409Z','20261026T102325213749Z'):assert (ROOT/'work/ver_buki_riko/shibuki_air'/name/'modified.arc').read_bytes()==(build/'modified.arc').read_bytes()
rec=json.loads(recipe.read_text());assert rec['paired_manifest_sha256']==digest(a/'pairs.json')
shutil.copyfile(build/'recipe.json',build/'recipe.before_metadata_correction.json');shutil.copyfile(recipe,build/'recipe.json')
groups=[];actual=Image.new('RGB',(6*200,4*240),'#28394b');draw=ImageDraw.Draw(actual)
for row,name in enumerate(('20261026T102204455893Z','20261026T102219835450Z','20261026T102242670321Z','20261026T102228169450Z')):
 path=ROOT/'work/ver_buki_riko/shibuki_run_runtime'/name/'verification.local.json';r=json.loads(path.read_text());nums=list(range(34 if r['shoot'] else 33,55,2))
 assert r['modified_bin_sha256']==expected and r['air'] and r['verified_frames']==nums and not r['unverified_frames']
 for n,f in r['frames'].items():
  assert f['verified'] and f.get('render_palette_is_base',True)
  assert any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in f['samples'])
  im=Image.open(path.parent/f'expected_{int(n):03d}.png');assert f['matches'][0]['opaque_pixels_equal']==sum(v!=0 for v in im.tobytes())
 groups.append({'direction':r['direction'],'shoot':r['shoot'],'evidence':str(path.relative_to(ROOT)),'whole_opaque_matched':nums,'base_palette':True})
 for col,n in enumerate((34,40,46,50,52,54) if r['shoot'] else (33,39,45,49,51,53)):
  match=r['frames'][str(n)]['matches'][0];screen=Image.open(path.parent/f"actual_{n:03d}_{match['page_y']}.png");im=Image.open(path.parent/f'expected_{n:03d}.png');bb=im.getbbox()
  if match['flip_x']:bb=(im.width-bb[2],bb[1],im.width-bb[0],bb[3])
  x,y=match['x'],match['y'];crop=screen.crop((max(0,x+bb[0]-7),max(0,y+bb[1]-7),min(320,x+bb[2]+7),min(240,y+bb[3]+7)));crop=crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST);actual.paste(crop,(col*200+(200-crop.width)//2,row*240+28));draw.text((col*200+8,row*240+7),f"actual {r['direction']} {n}",fill='white')
actual.save(build/'air_actual_review.png')
session='work/ver_buki_riko/emulator_sessions/20261026T102010847930Z';captures=sorted((ROOT/session).glob('*.png'));pause=str(captures[-1].relative_to(ROOT))
runtime={'build_sha256':expected,'groups':groups,'verified_frame_direction_pairs':44,'all_frames_whole_opaque_screen_match':True,'base_palette_all_pairs':True,'input_only_normal_keys':True,'process_memory_written':False,'save_state_load_save_keys_sent':False,'session':session,'session_paused':True,'pause_capture':pause}
write_json(build/'runtime_summary.local.json',runtime)
checks={'unit_tests':154,'negative_checks':json.loads((d/'negative_checks.json').read_text()),'search_cost_checks':json.loads((d/'fast_cost_checks.json').read_text()),'repeated_arc_identical':True,'full_disc_sectors_compared':m['full_disc_sectors_compared'],'changed_sectors':[q['lba'] for q in m['modified_bin']['changed_sectors']],'body_metrics':json.loads((a/'body_metrics.json').read_text()),'original_sha256':digest(ROOT/'MegaMan X4.bin'),'riko_accepted_sha256':digest(ROOT/'out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin'),'palette_timing_exe_preserved':True,'other_bitmaps_compositions_preserved':True,'all_nonselected_tiles_including_armor_preserved':True}
assert checks['original_sha256']==m['source_sha256'] and checks['riko_accepted_sha256']=='1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246'
write_json(build/'static_checks.local.json',checks)
for name in ('final_review_1x.png','final_review_3x.png'):shutil.copyfile(a/name,build/name)
shutil.copyfile(build/'manifest.json',build/'manifest.before_runtime.json');m.update(recipe=str(recipe.relative_to(ROOT)),runtime_verified=True,full_opaque_screen_match_all_frames=True,runtime_summary=str((build/'runtime_summary.local.json').relative_to(ROOT)),runtime_verified_frames=list(range(33,55)),standing_frames_preserved=True,base_sprite_references_applied=64)
(build/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
back=build/'previous_pointers';back.mkdir()
for fn in ('current_build.json','shibuki_current_build.json'):
 path=ROOT/'projects/ver_buki_riko'/fn;shutil.copyfile(path,back/fn);ptr=json.loads(path.read_text(encoding='utf-8'))
 ptr.pop('runtime_flash_occluded_frame',None)
 ptr.update(kind='shibuki_air_candidate',build=str(build.relative_to(ROOT)),cue=str((build/'shibuki_riko.cue').relative_to(ROOT)),bin_sha256=expected,session=session,session_closed=False,session_paused=True,session_pause_capture=pause,runtime_summary=m['runtime_summary'],runtime_verified_frames=list(range(33,55)),runtime_whole_opaque_matched_frames=list(range(33,55)),both_directions_verified=True,new_animation_user_review_pending=True,air_style_user_accepted=False,air_art_applied=True,standing_continuation_authorized=True,accepted_idle_preserved=True,accepted_movement_preserved=True,standing_frames_preserved=True,report='docs/SHIBUKI_AIR.md',next_group='dash_and_wall',active_art_study='work/ver_buki_riko/shibuki_art/air_v1',base_sprite_references_applied=64)
 path.write_text(json.dumps(ptr,ensure_ascii=False,indent=2),encoding='utf-8')
write_json(ROOT/'projects/ver_buki_riko/shibuki_air_art_revision.json',{'source':str(a.relative_to(ROOT)),'generated_sources':[str((d/f).relative_to(ROOT)) for f in ('generated_with_backdrop.png','landing_generated.png')],'prompts':[str((d/f).relative_to(ROOT)) for f in ('prompt.txt','landing_prompt.txt')],'method':'builtin_imagegen_then_palette_registration','build':str(build.relative_to(ROOT)),'style_user_accepted':False,'runtime_verified':True})
print(json.dumps({'build':str(build),'sha256':expected,'verified_pairs':44,'pause':pause}))
