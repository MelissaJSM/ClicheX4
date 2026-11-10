"""적용 증거와 출처를 묶고 최신 포인터를 기록한다. 게임 파일 쓰기 없음."""
import json,sys,shutil,gzip,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_fourth_pilot import write,require,render
from scripts.prepare_nana_fourth_ceremony_reference import FRAMES,PRESERVED
from scripts.project import digest
from PIL import Image,ImageDraw
B=ROOT/'out/ver_rin_nana/nana_fourth_ceremony_20261030T104630127748Z';R=ROOT/'work/ver_rin_nana/nana_fourth_armor';A=R/'ceremony_art_v3';S=R/'ceremony_v1';session='work/ver_rin_nana/emulator_sessions/20261030T104709375256Z'
expected='a0476173c6c6aec36ff8225021c11f238eb203a94c3dbe9ea3187f3ac4599a8c';require(digest(B/'rin_nana.bin')==expected,'BIN changed')
shutil.copytree(A,B/'ceremony_art');shutil.copyfile(R/'ceremony_verification.json',B/'ceremony_static_verification.json')
manifest=json.loads((B/'manifest.json').read_text('utf8'));protected=json.loads((B/'preservation.json').read_text('utf8'))
for q in protected['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed')
backup=ROOT/'work/ver_rin_nana/checkpoints/nana_fourth_before_ceremony_20261030';cards=[]
for i in (0,1):
 p=ROOT/f'work/ver_rin_nana/test_cards/nana_fourth_idle_v1/epsxe00{i}.mcr';require(digest(p)==digest(backup/p.name),'Card changed');cards.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
checkpoint=ROOT/'work/ver_rin_nana/checkpoints/nana_fourth_ceremony_20261030/SLUS_005.61.000';active=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';require(digest(checkpoint)==digest(active),'Checkpoint not restored')
state=gzip.decompress(active.read_bytes());player=state[442+0x1418c8:442+0x1418c8+0xe4]
runtime={'session':session,'pid':35544,'build':B.relative_to(ROOT).as_posix(),'bin_sha256':expected,'backup':backup.relative_to(ROOT).as_posix(),'checkpoint':checkpoint.relative_to(ROOT).as_posix(),'checkpoint_sha256':digest(active),'refresh_report':checkpoint.parent.relative_to(ROOT).as_posix()+'/refresh.json','evidence_kind':'graphics-refreshed checkpoint; not fresh disc resource loading','idle_check':'runtime_ceremony_idle_check/verification.json','new_ceremony_runtime_frames_verified':[],'new_ceremony_full_screen_verified':False,'runtime_assets_loaded':True,'stage_reentry_attempt':'Pause menu opened; subsequent inputs did not reach stage selection. No arrival/victory/return runtime pass claimed. F3 restored afterwards.','current_world_xy':[struct.unpack_from('<i',player,k)[0]//65536 for k in (8,12)],'hp':player[0x5c],'armor':player[0xa7],'arm_type':player[0xb8],'checkpoint_restored_exact':True,'memory_cards':cards,'protected_files_verified':len(protected['files'])}
write(B/'ceremony_runtime_summary.json',runtime)
source={'tool':'built_in_imagegen','generated':(S/'generated_first.png').relative_to(ROOT).as_posix(),'generated_sha256':digest(S/'generated_first.png'),'prompt':(S/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(S/'prompt.txt'),'references':[{'path':(S/n).relative_to(ROOT).as_posix(),'sha256':digest(S/n)} for n in ('native_pose_reference.png','accepted_armor_reference.png')],'native_source_cell_order':[138,156,204,205,206,207],'final_art':A.relative_to(ROOT).as_posix(),'notes':['생성 원화에서 알파192 이상 연결된 캐릭터만 정규화하여 배경 발광을 배제했다.','기본형 얼굴/손/권총/발 윤곽을 기준으로 등록,141/142는 현재 수용 대기 파츠 그대로 사용.','205 다리3파츠 한계 때문에 기존 구두 밑3행을 보존했다. 흰 옷자락과 베일은 다리 파츠 유지.','공통 빛/변신17참조는 새 아머 제작 수에 포함하지 않는다.']}
write(S/'source.json',source);write(B/'ceremony_source.json',source)
arc=(B/'modified.arc').read_bytes();board=Image.new('RGBA',(4*80,3*80));draw=ImageDraw.Draw(board)
for i,n in enumerate([0]+FRAMES):
 im=render(arc,n,True)[0].crop((40,32,120,104));board.alpha_composite(im,(i%4*80,i//4*80+8));draw.text((i%4*80+2,i//4*80),str(n),fill='white')
board.save(B/'ceremony_sheet_1x.png');board.resize((board.width*4,board.height*4),Image.Resampling.NEAREST).save(B/'ceremony_sheet_4x.png')
paths=['scripts/prepare_nana_fourth_ceremony_reference.py','scripts/prepare_nana_fourth_ceremony_art.py','scripts/prepare_nana_fourth_run.py','scripts/build_nana_fourth_idle.py','scripts/verify_nana_fourth_ceremony.py','scripts/prepare_nana_fourth_checkpoint.py','scripts/verify_nana_fourth_checkpoint.py',str(Path(__file__).relative_to(ROOT)).replace('\\','/')]
write(B/'ceremony_source_tools.json',[{'path':p,'sha256':digest(ROOT/p)} for p in paths])
pointer=ROOT/'projects/ver_rin_nana/current_build.json';p=json.loads(pointer.read_text('utf8'));require(p['sha256']==expected,'Pointer changed');p.update(current_session=session,ceremony_report='docs/NANA_FOURTH_CEREMONY.md',runtime_ceremony_assets_loaded=True,runtime_ceremony_motion_verified=False,runtime_ceremony_full_screen_verified=False);write(pointer,p)
candidate=ROOT/'projects/ver_rin_nana/nana_fourth_candidate.json';q=json.loads(candidate.read_text('utf8'));q.update(stage='ARMOR_CEREMONY_REVIEW',applied_frames=manifest['fourth_armor_frames']);q['ceremony_preparation']={'build':B.relative_to(ROOT).as_posix(),'sha256':expected,'art':A.relative_to(ROOT).as_posix(),'packed':(R/'ceremony_packed_v3').relative_to(ROOT).as_posix(),'frames':FRAMES,'preserved_common_frames':PRESERVED,'current_game_applied':True,'user_accepted':False,'runtime_motion_verified':False,'report':'docs/NANA_FOURTH_CEREMONY.md'};write(candidate,q);shutil.copyfile(candidate,B/'authorization.json')
print(json.dumps({'build':str(B.relative_to(ROOT)),'applied_refs':len(manifest['fourth_armor_frames']),'restored_world_xy':runtime['current_world_xy'],'hp':runtime['hp'],'cards_preserved':len(cards),'protected_files':len(protected['files'])}))
