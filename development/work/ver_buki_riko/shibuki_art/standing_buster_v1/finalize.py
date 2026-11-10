import json,sys,shutil,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest,write_json
from scripts.extract_zero import save_image
d=Path(__file__).parent;artdir=d/'production03';build=ROOT/'out/ver_buki_riko/shibuki_standing_20261026T093104097708Z';m=json.loads((build/'manifest.json').read_text());art=json.loads((artdir/'art.json').read_text())
assert digest(build/'shibuki_riko.bin')=='4d3b6c3ffd9f20f39ca426f312d4ec95cbc73b008b48056cfd39676117bafe8c'
assert (ROOT/'work/ver_buki_riko/shibuki_standing/20261026T093052216982Z/modified.arc').read_bytes()==(ROOT/'work/ver_buki_riko/shibuki_standing/20261026T093109481092Z/modified.arc').read_bytes()
base=np.array(Image.open(artdir/'standing_000.png'));metrics=[]
for n in (85,86,87,92):
 a=np.array(Image.open(artdir/f'standing_{n:03d}.png'));ys,xs=np.nonzero(a)
 assert np.array_equal(a[:20],base[:20]) and np.array_equal(a[20:36,42:],base[20:36,42:]) and np.array_equal(a[55:],base[55:])
 metrics.append({'frame':n,'visible_height':int(ys.max()-ys.min()+1),'visible_width':int(xs.max()-xs.min()+1),'foot_row':int(ys.max()),'foot_center':float(np.nonzero(a[ys.max()])[0].mean()),'face_and_boot_regions_identical_to_idle':True})
arm=np.array(Image.open(artdir/'isolated_arm_092.png'));yy,xx=np.nonzero(arm);shifted=np.zeros_like(arm);shifted[yy+1,xx+6]=arm[yy,xx];save_image(shifted.tobytes(),(96,80),art['palette_words'],artdir/'registered_arm_092.png')
im=Image.open(artdir/'review_3x.png');im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST).save(artdir/'review_6x.png')
reports=[]
for suffix in ('20261026T093239392898Z','20261026T093250205909Z'):
 path=ROOT/'work/ver_buki_riko/shibuki_run_runtime'/suffix/'verification.local.json';r=json.loads(path.read_text());assert r['modified_bin_sha256']==m['modified_bin']['sha256']
 assert r['verified_frames']==[85,87,92] and any(q['ram_equal'] and q['vram_equal'] for q in r['frames']['86']['samples'])
 reports.append({'direction':r['direction'],'evidence':str(path.relative_to(ROOT)),'whole_opaque_screen_match_frames':r['verified_frames'],'ram_vram_match_frames':[85,86,87,92]})
flash=json.loads((d/'flash_diagnostics.json').read_text());assert all(r['different_pixels']==11 and r['opaque_pixels']==791 for r in flash)
# Actual framebuffer crops, separate from generated previews.
sheet=Image.new('RGB',(4*320,2*280),'#222630');draw=ImageDraw.Draw(sheet)
for row,r in enumerate(reports):
 runtime=(ROOT/r['evidence']).parent;vr=json.loads((runtime/'verification.local.json').read_text())
 for col,n in enumerate((85,86,87,92)):
  if n==86:
   f=next(q for q in flash if q['direction']==r['direction']);screen=Image.open(runtime/'flash_actual_086.png');x,y=f['origin'];w,h=Image.open(runtime/'expected_086.png').size
  else:
   match=vr['frames'][str(n)]['matches'][0];screen=Image.open(runtime/f"actual_{n:03d}_{match['page_y']}.png");x,y=match['x'],match['y'];w,h=Image.open(runtime/f'expected_{n:03d}.png').size
  crop=screen.crop((max(0,x-10),max(0,y-8),min(320,x+w+10),min(240,y+h+8)));crop=crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST)
  sheet.paste(crop,(col*320,row*280+32));draw.text((col*320+8,row*280+10),f"actual {r['direction']} {n}"+(' muzzle flash' if n==86 else ''),fill='white')
sheet.save(build/'standing_actual_review.png')
runtime={'build_sha256':m['modified_bin']['sha256'],'groups':reports,'frame86_flash_diagnostics':flash,'frame86_visible_pixels_equal':780,'frame86_pixels_covered_by_flash_visual_review':11,'all_frames_whole_opaque_screen_match':False,'input_only_normal_keys':True,'process_memory_written':False,'save_state_loaded_or_saved':False,'session':'work/ver_buki_riko/emulator_sessions/20261026T093124217049Z','session_paused':True,'pause_capture':'work/ver_buki_riko/emulator_sessions/20261026T093124217049Z/20261026T093517738166Z.png'}
write_json(build/'runtime_summary.local.json',runtime)
checks={'unit_tests':154,'negative_checks':json.loads((d/'negative_checks.json').read_text()),'repeated_arc_identical':True,'full_disc_sectors_compared':m['full_disc_sectors_compared'],'changed_sectors':[q['lba'] for q in m['modified_bin']['changed_sectors']],'body_metrics':metrics,'original_sha256':digest(ROOT/'MegaMan X4.bin'),'riko_accepted_sha256':digest(ROOT/'out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin')}
assert checks['original_sha256']==m['source_sha256'] and checks['riko_accepted_sha256']=='1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246'
write_json(build/'static_checks.local.json',checks);shutil.copyfile(artdir/'review_3x.png',build/'standing_preview_3x.png');shutil.copyfile(artdir/'transition_preview.gif',build/'standing_transition_preview.gif')
shutil.copyfile(build/'manifest.json',build/'manifest.before_runtime.json');m.update(runtime_verified=True,full_opaque_screen_match_all_frames=False,runtime_summary=str((build/'runtime_summary.local.json').relative_to(ROOT)),runtime_whole_opaque_matched_frames=[85,87,92],runtime_flash_occluded_frame=86)
(build/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
back=build/'previous_pointers';back.mkdir()
for fn in ('current_build.json','shibuki_current_build.json'):
 path=ROOT/'projects/ver_buki_riko'/fn;shutil.copyfile(path,back/fn);ptr=json.loads(path.read_text(encoding='utf-8'))
 ptr.update(kind='shibuki_standing_candidate',build=str(build.relative_to(ROOT)),cue=str((build/'shibuki_riko.cue').relative_to(ROOT)),bin_sha256=m['modified_bin']['sha256'],session=runtime['session'],session_closed=False,session_paused=True,session_pause_capture=runtime['pause_capture'],runtime_summary=m['runtime_summary'],runtime_verified_frames=[85,86,87,92],runtime_whole_opaque_matched_frames=[85,87,92],runtime_flash_occluded_frame=86,both_directions_verified=True,new_animation_user_review_pending=True,standing_style_user_accepted=False,standing_buster_art_applied=True,current_movement_style_accepted=True,accepted_idle_preserved=True,accepted_movement_preserved=True,report='docs/SHIBUKI_STANDING_BUSTER.md',next_group='air_and_dash',active_art_study='work/ver_buki_riko/shibuki_art/standing_buster_v1')
 path.write_text(json.dumps(ptr,ensure_ascii=False,indent=2),encoding='utf-8')
write_json(ROOT/'projects/ver_buki_riko/shibuki_standing_art_revision.json',{'source':str(artdir.relative_to(ROOT)),'generated_source':str((d/'generated.png').relative_to(ROOT)),'prompt':str((d/'prompt.txt').relative_to(ROOT)),'method':'builtin_imagegen_then_palette_registration','build':str(build.relative_to(ROOT)),'style_user_accepted':False})
print(json.dumps({'build':str(build),'sha256':m['modified_bin']['sha256'],'checks':checks}))
