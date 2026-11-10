"""완료된 실행 증거만 집계하고 작업 포인터를 갱신한다."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import write
from scripts.project import digest
art=Path(__file__).parent;build=ROOT/'out/ver_rin_nana/nana_dash_20261029T072609070724Z';ids=set(range(67,85))
ds=[ROOT/'work/ver_rin_nana/nana_batch_runtime'/v for v in ['20261029T072815288351Z','20261029T072938846438Z']]
ram=set();render=set();groups=[]
for d in ds:
 q=json.loads((d/'verification.local.json').read_text('utf8'));ram|=ids&set(q['ram_vram_verified_frames']);render|=ids&set(q['render_matched_frames'])
 groups.append({'evidence':(d/'verification.local.json').relative_to(ROOT).as_posix(),'ram_vram':sorted(ids&set(q['ram_vram_verified_frames'])),'simultaneous_sample_render':sorted(ids&set(q['render_matched_frames']))})
assert ram==ids
cross=json.loads((art/'crosscheck_runtime.json').read_text('utf8'));assert set(cross['full_matched_frames'])==set(range(69,85))
occluded=[r for r in cross['best_comparisons'] if r['frame'] in (67,68)]
for r in occluded:
 assert r['opaque']-r['hits']==19
 assert all(y>=33 for x,y in r['mismatch_xy'])
 assert all(c[0]==c[1]==c[2] for c in r['actual_mismatch_colors'])
baseline='work/ver_rin_nana/live_poc/20261029T072801889524Z/verification.local.json';reload='work/ver_rin_nana/live_poc/20261029T073206841188Z/verification.local.json'
summary={'build_sha256':digest(build/'rin_nana.bin'),'session':'work/ver_rin_nana/emulator_sessions/20261029T072638086396Z','pid':25864,'baseline':baseline,'groups':groups,'ram_vram_frames':sorted(ram),'full_render_frames':cross['full_matched_frames'],'asynchronous_framebuffer_comparison':(art/'crosscheck_runtime.json').relative_to(ROOT).as_posix(),'occluded_frames':[67,68],'occlusion_scope':'Both facings: 19 rear boot pixels covered by native gray dash dust; remaining body exact. Not a whole-frame pixel match.','process_memory_written':False,'current_f1_sha256':digest(ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000'),'new_f1_then_f3_verified':reload,'checkpoint':'work/ver_rin_nana/checkpoints/nana_dash_verified_20261029T0732','prior_progress_checkpoint':'work/ver_rin_nana/checkpoints/before_nana_dash_20261029T0726','user_art_accepted':False,'known_limits':['No exhaustive special-weapon or armor dash tests','Native blue afterimage color/shape has not been replaced in this step','Shared refs in air dash and other actions do not complete those entire actions']}
write(build/'runtime_summary.local.json',summary);write(build/'dust_occlusion.local.json',occluded)
for f in ('actual_review.png','alignment_checks.json','crosscheck_runtime.json'):shutil.copyfile(art/f,build/f)
for name in ('manifest.json','verification.json'):
 p=build/name;d=json.loads(p.read_text('utf8'));d['runtime_verified']=True;d['runtime_scope']='18 RAM/VRAM refs; 16 full framebuffer refs; 2 dust-occluded rear boots';d['runtime_evidence']='runtime_summary.local.json';write(p,d)
p=ROOT/'projects/ver_rin_nana/current_build.json';d=json.loads(p.read_text('utf8'));d.update(runtime_verified=True,runtime_scope=summary['occlusion_scope'],runtime_evidence=(build/'runtime_summary.local.json').relative_to(ROOT).as_posix(),new_animation_user_accepted=False);write(p,d)
p=ROOT/'projects/ver_rin_nana/project.json';d=json.loads(p.read_text('utf8'));d['active_substage']='NANA_DASH_APPLIED_USER_REVIEW';d['latest_integrated_build']=build.relative_to(ROOT).as_posix();d['nana_air']['continuation_approval']={'quote':'좋아 계속 진행해','date':'2026-10-29','scope':'후속 기본형 제작 진행 승인; 공중 전수 사용자 테스트 발언은 없음'};d['nana_dash']={'build':build.relative_to(ROOT).as_posix(),'status':'applied_runtime_verified_with_dust_occlusion','runtime_evidence':(build/'runtime_summary.local.json').relative_to(ROOT).as_posix(),'user_art_accepted':False,'frames':sorted(ids),'body_and_shot_pairs':8,'cumulative_base_references':82};write(p,d)
write(build/'static_test_summary.json',{'unit_command':'python -m unittest tests.test_psx_frame_edit tests.test_psx_compress tests.test_psx_player tests.test_psx_tile_layout tests.test_psx_paired_layout','unit_tests_passed':27,'negative_cases':json.loads((ROOT/'work/ver_rin_nana/nana_dash/rejection_checks_v1/results.json').read_text('utf8')),'independent_preparations':['work/ver_rin_nana/nana_dash/20261029T072530651677Z','work/ver_rin_nana/nana_dash/20261029T072541377739Z'],'source_generation':'built-in imagegen','prompts':['work/ver_rin_nana/nana_art/dash_v1/prompt.txt','work/ver_rin_nana/nana_art/dash_v1/firing_prompt.txt']})
print(json.dumps({'build':str(build),'ram_vram':sorted(ram),'full':cross['full_matched_frames'],'occluded':[67,68],'f3':reload,'f1_sha256':summary['current_f1_sha256']}))
