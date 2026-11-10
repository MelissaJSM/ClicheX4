"""탑승·별도 피격의 정적 검증과 실제 회귀 범위를 분리해 기록한다. 게임 조작 없음."""
import json,sys,gzip,struct
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_nana_idle_shot import write,shifted
from scripts.project import digest
from scripts.prepare_nana_checkpoint import refresh
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.extract_zero import save_image
D=ROOT/'work/ver_rin_nana/nana_art/vehicle_hurt_v1';B=ROOT/'out/ver_rin_nana/nana_vehicle_hurt_20261030T014147573781Z';P=ROOT/'out/ver_rin_nana/nana_air_clone_20261030T012148509868Z';rel=B.relative_to(ROOT).as_posix();m=json.loads((B/'manifest.json').read_text('utf8'));recipe=json.loads((B/'art/recipe.json').read_text('utf8'));art=json.loads((D/'production03/art.json').read_text('utf8'));frames=art['remaining_frames']
def decoded(arc):
 es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True)
 def get(n):
  f=bank['frames'][n];return canvas_from_parts(decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'],composition_frame(es[3],0,n))
 return es,get
old,og=decoded((P/'modified.arc').read_bytes());new,ng=decoded((B/'modified.arc').read_bytes());assert old[9]==new[9];proofs=[]
for q in art['groups']:
 for k in q['aliases']:
  if k==198:assert not np.any(ng(k));assert composition_frame(old[3],0,k)==composition_frame(new[3],0,k);continue
  assert np.array_equal(ng(k),np.array(Image.open(D/'production03'/f'frame_{k:03d}.png')))
  assert np.array_equal(ng(k),shifted(ng(q['frame']),*q['translations'][str(k)]))
for q in art['heads']:
 x,y=q['original_slot'];a,b,c,d=q['source_box'];assert np.array_equal(ng(q['frame'])[y:y+16,x:x+16],og(q['source'])[b:d,a:c]);proofs.append({'head':q['frame'],'source':q['source'],'source_pixels_reused_without_resizing':True})
grips=[]
for q in art['registrations']:
 if not q['grip']:continue
 v=ng(q['frame']);ys,xs=np.nonzero(np.isin(v,[10,11,12])&(np.indices(v.shape)[0]>q['eye'][1]+2));x=int(xs.min());y=int(np.median(ys[xs<=x+1]));assert [x,y]==q['grip']['original'];grips.append({'frame':q['frame'],'final_grip':[x,y],'original_glove_anchor_identical':True})
for n in(235,236):
 v=og(n);body=og(234);mask=(v!=0)&(v!=body)&(body==0)&(ng(234)==0);assert np.array_equal(ng(n)[mask],v[mask]);assert np.array_equal(ng(n)[ng(234)!=0],ng(234)[ng(234)!=0])
write(B/'registration_effect_checks.json',{'heads':proofs,'grips':grips,'all_alias_translations_exact':True,'blank198_display_and_composition_preserved':True,'damage_aura_outside_new_body_indices_and_coordinates_identical':True,'all_palette_rows_identical':True})
pal=list(struct.unpack('<16H',new[9][:32]));board=Image.new('RGB',(400,300),'#222630');dr=ImageDraw.Draw(board)
for i,n in enumerate([0,162,166,170,174,233,234,235,236,184,193,195,196,199]):
 path=B/'art'/f'frame_{n:03d}.png'
 if n==0:path=B/'accepted_idle.png';save_image(ng(n).tobytes(),(160,160),pal,path)
 pic=Image.open(path).convert('RGBA').crop((40,32,120,112));x,y=i%5*80,i//5*100;board.paste(pic,(x,y+20),pic);dr.text((x+3,y+4),str(n),fill='white')
board.save(B/'final_review_1x.png');board.resize((800,600),Image.Resampling.NEAREST).save(B/'final_review_2x.png')
run=ROOT/'work/ver_rin_nana/nana_batch_runtime/20261030T014317641789Z';r=json.loads((run/'verification.local.json').read_text('utf8'));assert r['capture_completed']and r['failure']is None and r['modified_bin_sha256']==m['modified_bin']['sha256'];assert not set(frames)&set(r['observed_frames']);assert set(r['ram_vram_verified_frames'])==set(r['observed_frames'])
partial=ROOT/'work/ver_rin_nana/nana_batch_runtime/20261030T014303102563Z';pr=json.loads((partial/'verification.local.json').read_text('utf8'));assert not pr['capture_completed']and 'Focus changed'in pr['failure']
backup=ROOT/'work/ver_rin_nana/checkpoints/before_nana_vehicle_hurt_20261030';statepath=backup/'current/SLUS_005.61.000';afterpath=ROOT/'work/ver_rin_nana/checkpoints/nana_vehicle_hurt_preview_20261030/SLUS_005.61.000';updated,proof=refresh(gzip.decompress(statepath.read_bytes()),(P/'modified.arc').read_bytes(),(B/'modified.arc').read_bytes(),442);assert updated==gzip.decompress(afterpath.read_bytes());proof['independent_refresh_equal']=True;write(B/'checkpoint_reproduction.local.json',proof)
runtime={'session':'work/ver_rin_nana/emulator_sessions/20261030T014218504706Z','pid':3772,'cue':rel+'/rin_nana.cue','checkpoint_refresh':'work/ver_rin_nana/checkpoints/nana_vehicle_hurt_preview_20261030/refresh.json','backup':backup.relative_to(ROOT).as_posix(),'whole_bank_audit':rel+'/live_bank_audit.local.json','regression_evidence':(run/'verification.local.json').relative_to(ROOT).as_posix(),'interrupted_attempt':(partial/'verification.local.json').relative_to(ROOT).as_posix(),'regression_ram_vram_verified_frames':r['ram_vram_verified_frames'],'regression_full_framebuffer_verified_frames':r['render_matched_frames'],'target_ram_vram_verified_frames':[],'target_full_framebuffer_verified_frames':[],'target_not_observed':frames,'whole_base_graphics_bank_equal':True,'fresh_disc_action_loading_verified':False,'all_target_pixels_runtime_verified':False,'process_memory_written':False,'final_position_before_handoff':'latest user waterfall-floor position restored via F3; default weapon','user_takes_control':True,'user_quote':'그럼 아머 테스트는 내가 해보고말해줄게','notes':['기존 F1·카드와 현재 진행을 별도 백업. 활성 대기118의 그래픽이 같은 상태에서 자산2/3만9073바이트 갱신','첫 회귀 시도는 포커스 변경으로 중지하고 키를 해제했다. 완료 검사로 계산하지 않았다','F3 복원 뒤 별도 재시도에서 걷기·점프·사격35참조 RAM/VRAM과 공중5참조 전체화면 일치','이번 탑승·별도 피격37참조의 발동 증거는 없다. 특정 피격원도 미확인','테스트 뒤F3로 저장 위치·기본무기·에너지·HP 복원. 이후 사용자가 아머 테스트를 맡겠다고 하여 조작을 넘겼다']};write(B/'runtime_summary.local.json',runtime)
v=json.loads((B/'verification.json').read_text('utf8'));v.update(unit_tests={'sprite_tests':34,'passed':True},negative_checks=json.loads((D/'negative_checks.json').read_text('utf8')),checked_other_compositions=recipe['checked_other_compositions'],independent_frame_pngs_and_recipe_identical=True,independent_checkpoint_refresh_identical=True);write(B/'static_checks.local.json',v)
for f in json.loads((B/'preservation.json').read_text('utf8'))['files']:assert digest(ROOT/f['path'])==f['expected_sha256']
cards={n:{'current_sha256':digest(ROOT/'work/ver_rin_nana/test_cards/nana_vehicle_hurt_v1'/n),'backup_sha256':digest(backup/'cards'/n)}for n in('epsxe000.mcr','epsxe001.mcr')};unchanged=all(q['current_sha256']==q['backup_sha256']for q in cards.values());assert digest(B/'rin_nana.bin')==m['modified_bin']['sha256']
write(backup/'inventory.json',[{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':digest(p)}for p in backup.rglob('*')if p.is_file()and p.name!='inventory.json'])
sources=[D/n for n in('generated.png','prompt.txt','plan.json','production03/art.json','production03/layout.json','checks.py','regression_plan.json')]+sorted((D/'production03').glob('packing_*.json'))+[ROOT/'scripts'/n for n in('prepare_nana_vehicle_hurt_art.py','optimize_nana_vehicle_hurt.py','optimize_nana_arrival.py','prepare_shibuki_remaining.py','build_nana_run.py','prepare_nana_checkpoint.py','capture_shibuki_batch.py')]
write(B/'source_manifest.json',{'image_tool':'built-in imagegen','prompt':(D/'prompt.txt').relative_to(ROOT).as_posix(),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in sources],'generated_images_are_not_runtime_evidence':True})
write(B/'final_preservation.local.json',{'protected_files_verified':20,'original_and_first_mode_verified':True,'test_cards_unchanged_at_audit':unchanged,'cards':cards,'output_bin_sha256':digest(B/'rin_nana.bin'),'user_control_handed_back_before_finalization':True})
m.update(runtime_verified=False,target_frames_loaded_and_uploaded=[],new_animation_user_accepted=False,runtime_summary=rel+'/runtime_summary.local.json',user_ride_test_pending=True);write(B/'manifest.json',m)
p=ROOT/'projects/ver_rin_nana/current_build.json';j=json.loads(p.read_text('utf8'));j.update(cumulative_base_references=220,session=runtime['session'],report='docs/NANA_VEHICLE_HURT.md',runtime_summary=rel+'/runtime_summary.local.json',next_group='user_vehicle_review_then_nana_ui',runtime_verified=False,target_frames_loaded_and_uploaded=[],user_ride_test_pending=True);write(p,j)
p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j.update(latest_integrated_build=rel,active_substage='NANA_VEHICLE_HURT_APPLIED_USER_RIDE_TEST');j['nana_vehicle_hurt']={'build':rel,'sha256':m['modified_bin']['sha256'],'frames':frames,'cumulative_base_references':220,'new_visible_references':36,'shared_blank_reference':198,'user_accepted':False,'runtime_verified':False,'target_frames_loaded_and_uploaded':[],'runtime_evidence':rel+'/runtime_summary.local.json','user_ride_test_pending':True,'user_test_quote':runtime['user_quote'],'continuation_quote':'좋아 계속 진행하자'};write(p,j)
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8');old=s.split('\n\n')[1];s=s.replace(old,'2026-10-30. `EXPANSION`, 활성 `ver_rin_nana/x_nana`. **체이서13·라이드 아머 머리19·별도 피격4개를 적용했다. 공유 빈198 보존까지37참조 처리, 누적220참조**. 기존183참조·팔레트·공격 효과·아머 의상·노바를 보존했다. 원래13압축 슬롯을 사용하며 재배치 없다. 새 은행 전체RAM 일치, 기존 걷기·점프·사격35참조 RAM/VRAM과 공중5참조 전체화면 일치. 이번 탑승·피격의 실제 발동은 미검증이다. 사용자가 아머 테스트를 맡겠다고 하여 조작을 넘겼으며 추가 입력은 하지 않는다. 적용본 한 개 실행 중. 남은 미술은 Nova8(아머 단계), 나나 UI/일러스트·개인 효과·음성이다. [제작·검사·사용자 테스트](NANA_VEHICLE_HURT.md).',1)
s=s.replace('## 현재 적용본\n\n','## 현재 적용본\n\n- [탑승·별도 피격 CUE](../'+rel+'/rin_nana.cue), BIN SHA-256 `'+m['modified_bin']['sha256']+'`. 508참조/다른1750조립·독립2회 ARC/37PNG/recipe·전체251793섹터/변경9섹터 EDC/ECC·보호20파일·34단위/15거부 검사 통과. [실행 범위](NANA_VEHICLE_HURT.md).\n',1);p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 탑승·별도 피격 적용, 사용자 아머 테스트\n\n사용자 “좋아 계속 진행하자”에 따라 체이서13·라이드 아머 머리19·별도 피격4개와 공유 빈198 보존을 처리했다. 이전 공중·분신17개의 미검증 발동을 이번 지시로 수용/검증 완료 처리하지 않는다. 기존183참조와 아머 의상을 보존한 `ae3a01b1…`를 적용했고 사용자가 “그럼 아머 테스트는 내가 해보고말해줄게”라고 하여 조작을 넘겼다. 탑승/피격의 실기 결과는 아직 없다. [근거](NANA_VEHICLE_HURT.md).\n\n'+p.read_text('utf8'),'utf8')
p=ROOT/'docs/COMMANDS.md';p.write_text('# 나나 탑승·별도 피격 (2026-10-30)\n\n실행한 제작·검사·적용 명령은 [NANA_VEHICLE_HURT.md](NANA_VEHICLE_HURT.md#실행한-명령)에 있다. 준비 범위 `base_nana_vehicle_hurt_37`, 빌더 범위 `vehicle_hurt`. 현재 사용자 조작 중이므로 실기 명령을 자동 재실행하지 않는다.\n\n'+p.read_text('utf8'),'utf8')
print(json.dumps({'build':rel,'new_visible':36,'shared_blank':198,'new_runtime_verified':[],'regression_verified_count':len(r['ram_vram_verified_frames']),'regression_framebuffer':r['render_matched_frames'],'other_compositions':recipe['checked_other_compositions'],'protected':20,'cards_unchanged_at_audit':unchanged}))
