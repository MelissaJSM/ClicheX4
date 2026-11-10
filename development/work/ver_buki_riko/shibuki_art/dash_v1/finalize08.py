"""최종 대시 실행 증거를 검증하고 포인터를 등록하는 일회성 기록."""
import json,sys,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest,write_json
def evidence(path,value):
 if path.exists():assert json.loads(path.read_text(encoding='utf-8'))==value
 else:write_json(path,value)
d=Path(__file__).parent;a=d/'production08'
build=ROOT/'out/ver_buki_riko/shibuki_dash_20261026T113618370649Z'
expected='fb434ef6a229b669cd502520e280fb8453a808af6f38d24cb0a2e2131ee092d5'
m=json.loads((build/'manifest.json').read_text());assert digest(build/'shibuki_riko.bin')==expected
recipe=ROOT/'work/ver_buki_riko/shibuki_dash/20261026T113530897388Z/recipe.json'
rec=json.loads(recipe.read_text());assert rec['paired_manifest_sha256']==digest(a/'pairs.json')
assert (build/'recipe.json').read_bytes()==recipe.read_bytes()
for name in ('20261026T113530897388Z','20261026T113634627821Z'):
 assert (ROOT/'work/ver_buki_riko/shibuki_dash'/name/'modified.arc').read_bytes()==(build/'modified.arc').read_bytes()
for name,sha in json.loads((d/'source_manifest.json').read_text())['files'].items():assert digest(d/name)==sha
runtime_root=ROOT/'work/ver_buki_riko/shibuki_run_runtime'
spec=[('right',False,'20261026T115005094329Z','20261026T115005094329Z'),('left',False,'20261026T114924670680Z','20261026T115328378397Z'),('right',True,'20261026T115142295379Z','20261026T115142295379Z'),('left',True,'20261026T114841008404Z','20261026T115148765596Z')]
groups=[];occlusions=[];actual=Image.new('RGB',(1200,960),'#28394b');draw=ImageDraw.Draw(actual)
for row,(direction,shoot,full_id,partial_id) in enumerate(spec):
 full=runtime_root/full_id;part=runtime_root/partial_id
 r=json.loads((full/'verification.local.json').read_text());p=json.loads((part/'verification.local.json').read_text())
 for q in (r,p):assert q['modified_bin_sha256']==expected and q['dash'] and q['direction']==direction and q['shoot']==shoot and not q['process_memory_written']
 nums=list(range(68 if shoot else 67,85,2));whole=nums[2:];selected={}
 for n in whole:
  f=r['frames'][str(n)];assert f['verified'] and f.get('render_palette_is_base',True)
  assert any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in f['samples'])
  match=f['matches'][0];im=Image.open(full/f'expected_{n:03d}.png');assert match['opaque_pixels_equal']==sum(v!=0 for v in im.tobytes())
  selected[n]=(full/f"actual_{n:03d}_{match['page_y']}.png",im,match['x'],match['y'],match['flip_x'],False)
 for audit in json.loads((part/'best_mismatch.json').read_text()):
  n=audit['frame'];assert n in nums[:2];f=p['frames'][str(n)]
  assert any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in f['samples'])
  assert audit['opaque']-audit['hits']==(47 if n in (67,68) else 20)
  assert all(c[0]==c[1]==c[2] and c[0] in (98,123,156,189,255) for c in audit['actual_colors'])
  assert all(29<=pt[1]<=41 for pt in audit['mismatch_xy'])
  audit.update(evidence=str((part/'verification.local.json').relative_to(ROOT)),screen=str((part/audit['image']).relative_to(ROOT)),whole_opaque_match=False,interpretation='원래 대시 먼지가 뒷부츠를 덮음. 이미지 직접 확인; 차이 전체가 회색 먼지 색이고 나머지 불투명 픽셀은 일치.')
  occlusions.append(audit);im=Image.open(part/f'expected_{n:03d}.png')
  selected[n]=(part/audit['image'],im,audit['x'],audit['y'],direction=='right',True)
 assert set(selected)==set(nums)
 groups.append({'direction':direction,'shoot':shoot,'full_evidence':str((full/'verification.local.json').relative_to(ROOT)),'occlusion_evidence':str((part/'best_mismatch.json').relative_to(ROOT)),'ram_vram_base_palette_matched':nums,'whole_opaque_matched':whole,'dust_occluded_frames':nums[:2]})
 for col,n in enumerate((68,70,72,74,78,84) if shoot else (67,69,71,73,77,83)):
  path,im,x,y,flip,occluded=selected[n];screen=Image.open(path);bb=im.getbbox()
  if flip:bb=(im.width-bb[2],bb[1],im.width-bb[0],bb[3])
  crop=screen.crop((max(0,x+bb[0]-7),max(0,y+bb[1]-7),min(320,x+bb[2]+7),min(240,y+bb[3]+7)))
  crop=crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST);actual.paste(crop,(col*200+(200-crop.width)//2,row*240+28))
  draw.text((col*200+7,row*240+7),f"actual {direction} {n}"+(' / dust' if occluded else ''),fill='white')
actual.save(build/'dash_actual_review.png')
evidence(build/'dust_occlusion.local.json',occlusions)
session='work/ver_buki_riko/emulator_sessions/20261026T113632833180Z'
pause=session+'/20261026T115348882347Z.png';assert (ROOT/pause).exists()
runtime={'build_sha256':expected,'groups':groups,'ram_vram_frame_direction_pairs':36,'whole_opaque_screen_matched_pairs':28,'dust_occluded_pairs':8,'all_frames_whole_opaque_screen_match':False,'base_palette_all_pairs':True,'input_only_normal_keys':True,'process_memory_written':False,'save_state_load_save_keys_sent':False,'session':session,'session_paused':True,'pause_capture':pause,'baseline':'work/ver_buki_riko/live_poc/20261026T114736216912Z/verification.local.json','limitations':'67/68/69/70 화면 전체 일치 아님. 뒷부츠 47/20픽셀을 원래 먼지가 덮는다. 피격/사망으로 인한 미완료 실행은 최종 증거에서 제외했으며 새 게임 Continue 후 메뉴 정지를 확인했다.'}
evidence(build/'runtime_summary.local.json',runtime)
checks={'unit_tests':161,'negative_checks':json.loads((d/'negative_checks08.json').read_text()),'repeated_arc_identical':True,'full_disc_sectors_compared':m['full_disc_sectors_compared'],'changed_sectors':[s['lba'] for s in m['modified_bin']['changed_sectors']],'body_metrics':json.loads((a/'body_metrics.json').read_text()),'original_sha256':digest(ROOT/'MegaMan X4.bin'),'riko_accepted_sha256':digest(ROOT/'out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin'),'palette_timing_exe_preserved':True,'other_bitmaps_compositions_preserved':True,'all_nonselected_tiles_including_armor_preserved':True,'speed_streak_tile_and_extra_parts_preserved':True}
assert checks['original_sha256']==m['source_sha256'] and checks['riko_accepted_sha256']=='1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246'
evidence(build/'static_checks.local.json',checks)
for name in ('final_review_1x.png','final_review_3x.png'):shutil.copyfile(a/name,build/name)
shutil.copyfile(build/'manifest.json',build/'manifest.before_runtime.json')
m.update(recipe=str(recipe.relative_to(ROOT)),runtime_verified=True,full_opaque_screen_match_all_frames=False,runtime_summary=str((build/'runtime_summary.local.json').relative_to(ROOT)),runtime_verified_frames=list(range(67,85)),runtime_dust_occluded_frames=[67,68,69,70],base_sprite_references_applied=82,accepted_air_preserved=True)
(build/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
back=build/'previous_pointers';back.mkdir()
for fn in ('current_build.json','shibuki_current_build.json'):
 path=ROOT/'projects/ver_buki_riko'/fn;shutil.copyfile(path,back/fn);ptr=json.loads(path.read_text(encoding='utf-8'))
 ptr.update(kind='shibuki_dash_candidate',build=str(build.relative_to(ROOT)),cue=str((build/'shibuki_riko.cue').relative_to(ROOT)),bin_sha256=expected,session=session,session_closed=False,session_paused=True,session_pause_capture=pause,runtime_summary=m['runtime_summary'],runtime_verified_frames=list(range(67,85)),runtime_whole_opaque_matched_frames=list(range(71,85)),runtime_dust_occluded_frames=[67,68,69,70],both_directions_verified=True,new_animation_user_review_pending=True,dash_style_user_accepted=False,dash_art_applied=True,air_style_user_accepted=True,accepted_air_preserved=True,report='docs/SHIBUKI_DASH.md',next_group='wall_actions',active_art_study='work/ver_buki_riko/shibuki_art/dash_v1',base_sprite_references_applied=82)
 path.write_text(json.dumps(ptr,ensure_ascii=False,indent=2),encoding='utf-8')
write_json(ROOT/'projects/ver_buki_riko/shibuki_dash_art_revision.json',{'source':str(a.relative_to(ROOT)),'generated_sources':[str((d/n).relative_to(ROOT)) for n in ('generated.png','compact_generated.png','transition_generated.png')],'prompts':[str((d/n).relative_to(ROOT)) for n in ('prompt.txt','compact_prompt.txt','transition_prompt.txt')],'method':'builtin_imagegen_then_indexed_palette_registration','build':str(build.relative_to(ROOT)),'style_user_accepted':False,'runtime_verified':True,'runtime_full_screen_match_exceptions':[67,68,69,70]})
print(json.dumps({'build':str(build),'sha256':expected,'whole_pairs':28,'dust_occluded_pairs':8,'pause':pause}))
