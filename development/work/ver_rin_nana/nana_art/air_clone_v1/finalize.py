import json,sys,gzip,struct
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_nana_idle_shot import write
from scripts.project import digest
from scripts.prepare_nana_checkpoint import refresh
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.extract_zero import save_image
D=ROOT/'work/ver_rin_nana/nana_art/air_clone_v1';B=ROOT/'out/ver_rin_nana/nana_air_clone_20261030T012148509868Z';P=ROOT/'out/ver_rin_nana/nana_special_remaining_20261030T010327624138Z';rel=B.relative_to(ROOT).as_posix();m=json.loads((B/'manifest.json').read_text('utf8'));recipe=json.loads((B/'art/recipe.json').read_text('utf8'));art=json.loads((D/'production01/art.json').read_text('utf8'));frames=art['remaining_frames']
def decode(arc):
 es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True)
 def get(n):
  f=bank['frames'][n];return canvas_from_parts(decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'],composition_frame(es[3],0,n))
 return es,get
old,og=decode((P/'modified.arc').read_bytes());new,ng=decode((B/'modified.arc').read_bytes());assert old[9]==new[9]
reused=[]
for n,source in art['reused_accepted_frames'].items():
 assert np.array_equal(ng(int(n)),og(source));reused.append({'new':int(n),'accepted':source,'indexed_pixels_and_registration_identical':True})
for n in (211,212):
 assert np.array_equal(ng(n),np.array(art['effect_index_mapping'],np.uint8)[og(n)]);assert composition_frame(old[3],0,n)==composition_frame(new[3],0,n)
assert np.array_equal(ng(208)!=0,og(0)!=0)and np.array_equal(ng(209)!=0,og(0)!=0)
write(B/'reuse_and_effect_checks.json',{'reused':reused,'clone208_209_use_accepted_idle_silhouette':True,'beam211_212_native_shape_coordinates_preserved':True,'all_palette_rows_identical':True})
pal=list(struct.unpack('<16H',new[9][:32]));board=Image.new('RGB',(480,285),'#222630');dr=ImageDraw.Draw(board)
for i,n in enumerate([0,*frames]):
 path=B/'art'/f'frame_{n:03d}.png'
 if n==0:path=B/'accepted_idle.png';save_image(ng(n).tobytes(),(160,160),pal,path)
 pic=Image.open(path).convert('RGBA').crop((45,37,125,112));x,y=i%6*80,i//6*95;board.paste(pic,(x,y+20),pic);dr.text((x+3,y+4),str(n),fill='white')
board.save(B/'final_review_1x.png');board.resize((960,570),Image.Resampling.NEAREST).save(B/'final_review_2x.png')
# 원작 시간표로 만든 오프라인 조립 프리뷰이며 실제 발동 증거가 아니다.
inv=json.loads((ROOT/art['source_inventory']).read_text('utf8'));preview=[]
for aid,name in((18,'air_dash'),(23,'hover'),(98,'clone_vanish')):
 pics=[];times=[]
 for s in inv['animations'][aid]['steps']:
  n=s['frame'];path=B/'art'/f'preview_anim_{n:03d}.png';save_image(ng(n).tobytes(),(160,160),pal,path);im=Image.open(path).convert('RGBA').crop((40,32,120,112));bg=Image.new('RGB',(80,80),'#222630');bg.paste(im,(0,0),im);pics.append(bg.resize((320,320),Image.Resampling.NEAREST));times.append(max(20,round(s['duration_ticks']*1000/60)))
 pics[0].save(B/(name+'_preview.gif'),save_all=True,append_images=pics[1:],duration=times,loop=0,disposal=2);preview.append({'animation':aid,'file':name+'_preview.gif','kind':'offline table order, 60 ticks/sec display assumption, event branches/loops not simulated; runtime timing unverified'})
run=ROOT/'work/ver_rin_nana/nana_batch_runtime/20261030T012305853255Z';r=json.loads((run/'verification.local.json').read_text('utf8'));assert r['capture_completed']and r['failure']is None and r['modified_bin_sha256']==m['modified_bin']['sha256'];assert not set(frames)&set(r['observed_frames']);assert set(r['ram_vram_verified_frames'])==set(r['observed_frames'])
backup=ROOT/'work/ver_rin_nana/checkpoints/before_nana_air_clone_20261030';statepath=backup/'current/SLUS_005.61.000';afterpath=ROOT/'work/ver_rin_nana/checkpoints/nana_air_clone_preview_20261030/SLUS_005.61.000';updated,proof=refresh(gzip.decompress(statepath.read_bytes()),(P/'modified.arc').read_bytes(),(B/'modified.arc').read_bytes(),442);assert updated==gzip.decompress(afterpath.read_bytes());proof['independent_refresh_equal']=True;write(B/'checkpoint_reproduction.local.json',proof)
runtime={'session':'work/ver_rin_nana/emulator_sessions/20261030T012245486914Z','pid':29008,'cue':rel+'/rin_nana.cue','checkpoint_refresh':'work/ver_rin_nana/checkpoints/nana_air_clone_preview_20261030/refresh.json','backup':backup.relative_to(ROOT).as_posix(),'whole_bank_audit':rel+'/live_bank_audit.local.json','regression_evidence':(run/'verification.local.json').relative_to(ROOT).as_posix(),'regression_ram_vram_verified_frames':r['ram_vram_verified_frames'],'regression_full_framebuffer_verified_frames':r['render_matched_frames'],'target_ram_vram_verified_frames':[],'target_full_framebuffer_verified_frames':[],'target_not_observed':frames,'whole_base_graphics_bank_equal':True,'fresh_disc_action_loading_verified':False,'all_target_pixels_runtime_verified':False,'process_memory_written':False,'final_position':'latest user waterfall-floor position restored via F3; default weapon','notes':[]}
runtime['notes']=['메뉴를 닫은 뒤 현재 위치에서 F1 저장. 이전 F1·카드와 현재 진행을 각각 백업','자산2/3의9022바이트만 갱신. 플레이어/진행/프로그램/활성VRAM/모든 팔레트 보존','일반 점프·사격24참조의RAM/VRAM,공중5참조의전체화면 일치. 이번17참조 발동 증거로 계산하지 않음','원작 소스상 공중 대시·호버는 armor_parts &8, 특수무기 차지는 &4. 현재 저장 아머0이므로 조건 조작 없이 미검증 유지','테스트 후F3로 최신 저장 위치·기본무기·에너지·HP 복원. 카드 쓰기 없음'];write(B/'runtime_summary.local.json',runtime)
v=json.loads((B/'verification.json').read_text('utf8'));v.update(unit_tests={'sprite_tests':34,'passed':True},negative_checks=json.loads((D/'negative_checks.json').read_text('utf8')),checked_other_compositions=recipe['checked_other_compositions'],independent_frame_pngs_and_recipe_identical=True,independent_checkpoint_refresh_identical=True);write(B/'static_checks.local.json',v)
for f in json.loads((B/'preservation.json').read_text('utf8'))['files']:assert digest(ROOT/f['path'])==f['expected_sha256']
for n in('epsxe000.mcr','epsxe001.mcr'):assert digest(ROOT/'work/ver_rin_nana/test_cards/nana_air_clone_v1'/n)==digest(backup/'cards'/n)
assert digest(B/'rin_nana.bin')==m['modified_bin']['sha256'];assert digest(ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000')==digest(afterpath)
write(backup/'inventory.json',[{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':digest(p)}for p in backup.rglob('*')if p.is_file()and p.name!='inventory.json'])
sources=[D/n for n in('generated.png','prompt.txt','inventory_plan.json','production01/art.json','production01/layout.json','checks.py','air_regression_plan.json')]+sorted((D/'production01').glob('packing_*.json'))+[ROOT/'scripts'/n for n in('prepare_nana_air_clone_art.py','optimize_nana_air_clone.py','optimize_nana_arrival.py','prepare_shibuki_remaining.py','build_nana_run.py','prepare_nana_checkpoint.py','capture_shibuki_batch.py')]+[ROOT/'work/research/decomp/src/main'/n for n in('player_check.c','player_weapon.c','player_enter.c','player_special.c')]
write(B/'source_manifest.json',{'image_tool':'built-in imagegen','prompt':(D/'prompt.txt').relative_to(ROOT).as_posix(),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in sources],'previews':preview,'generated_images_are_not_runtime_evidence':True})
write(B/'final_preservation.local.json',{'protected_files_verified':20,'original_and_first_mode_verified':True,'test_cards_unchanged':True,'output_bin_sha256':digest(B/'rin_nana.bin')})
m.update(runtime_verified=False,target_frames_loaded_and_uploaded=[],new_animation_user_accepted=False,runtime_summary=rel+'/runtime_summary.local.json');write(B/'manifest.json',m)
p=ROOT/'projects/ver_rin_nana/current_build.json';j=json.loads(p.read_text('utf8'));j.update(cumulative_base_references=183,session=runtime['session'],report='docs/NANA_AIR_CLONE.md',runtime_summary=rel+'/runtime_summary.local.json',next_group='extra_damage_and_vehicle',runtime_verified=False,target_frames_loaded_and_uploaded=[]);write(p,j)
p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j.update(latest_integrated_build=rel,active_substage='NANA_AIR_CLONE_APPLIED_RUNTIME_PENDING_ARMOR');j['nana_air_clone']={'build':rel,'sha256':m['modified_bin']['sha256'],'frames':frames,'cumulative_base_references':183,'user_accepted':False,'runtime_verified':False,'target_frames_loaded_and_uploaded':[],'runtime_evidence':rel+'/runtime_summary.local.json','armor_costume_production_started':False};write(p,j)
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8');old=s.split('\n\n')[1];s=s.replace(old,'2026-10-30. `EXPANSION`, 활성 `ver_rin_nana/x_nana`. 프로스트 타워·라이징 파이어는 사용자 직접 테스트 후 수용했다. **추가 공중12·분신 소멸5참조 적용, 기본형 누적183참조**. 기존166참조·팔레트·공격 효과·아머·노바를 보존했다. 원래12압축 슬롯에 들어가며 재배치 없다. 새 은행 전체RAM 일치, 기존 일반 점프·사격24참조 RAM/VRAM과공중5참조 전체화면 일치. 현재 아머0 저장에서 이번17참조 발동은 미검증이며 신규 미술 수용 전이다. 공중 대시/호버는 다리, 차지 분신은 팔 파츠 조건이므로 아머 단계에서 실기 확인한다. 최신 사용자 진행의 그래픽만 갱신한F3로 복원하고 적용본 한 개를 켜 두었다. 다음은 추가 피격·탑승. [제작·검사·제한](NANA_AIR_CLONE.md).',1)
s=s.replace('## 현재 적용본\n\n','## 현재 적용본\n\n- [추가 공중·분신 CUE](../'+rel+'/rin_nana.cue), BIN SHA-256 `'+m['modified_bin']['sha256']+'`. 508참조/다른1770조립·독립2회 ARC/17PNG/recipe·전체251793섹터/변경10섹터 EDC/ECC·보호20파일·34단위/13거부 검사 통과. [실행 범위](NANA_AIR_CLONE.md).\n',1);p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 추가 공중·분신17참조 적용\n\n사용자 “좋아 테스트 해봤어 다음 작업으로 넘어가도 돼”로 이전 프로스트·라이징 파이어 결과를 수용하고 다음 기본형 제작을 진행했다. 기존 공중11참조를 좌표까지 동일하게 재사용하고94만 새로 그렸으며,208..212 소멸은 나나 실루엣/분홍색으로 변경했다. Nova213..220·아머 의상 제작은 제외했다. 원작 슬롯과 기존166참조를 보존한 `4f82fba9…`를 적용했다. 이번17참조의 실기 발동은 파츠 조건이 갖춰진 뒤 검증한다. 일반 공중 회귀24참조 확인은 이 발동을 증명하지 않는다. [근거](NANA_AIR_CLONE.md).\n\n'+p.read_text('utf8'),'utf8')
p=ROOT/'docs/COMMANDS.md';p.write_text('# 나나 추가 공중·분신17참조 (2026-10-30)\n\n실행한 제작·검사·적용 명령은 [NANA_AIR_CLONE.md](NANA_AIR_CLONE.md#실행한-명령)에 있다. 준비 범위 `base_nana_air_clone_17`, 빌더 범위 `air_clone`. 그래픽 갱신 체크포인트는 자산2/3만 변경하고 팔레트·진행을 보존한다.\n\n'+p.read_text('utf8'),'utf8')
print(json.dumps({'build':rel,'new_references':len(frames),'new_runtime_verified':[],'regression_verified':r['ram_vram_verified_frames'],'regression_framebuffer':r['render_matched_frames'],'other_compositions':recipe['checked_other_compositions'],'protected':20,'cards_unchanged':True}))
