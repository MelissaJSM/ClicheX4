"""공중 대시·호버12참조의 출처·실행 근거와 활성 포인터를 기록한다."""
import json,sys,shutil,gzip,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_fourth_pilot import write,require,render
from scripts.prepare_nana_fourth_hover_reference import FRAMES
from scripts.project import digest
from PIL import Image,ImageDraw
B=ROOT/'out/ver_rin_nana/nana_fourth_hover_20261030T113845331469Z';R=ROOT/'work/ver_rin_nana/nana_fourth_armor';A=R/'hover_art_v2';S=R/'hover_reference_v1';session='work/ver_rin_nana/emulator_sessions/20261030T113921574152Z'
expected='f8b10f3bf16c37f5635f2c652c46dbbab766f858a80d4a4013cf5960b448f1fa';require(digest(B/'rin_nana.bin')==expected,'BIN changed')
shutil.copytree(A,B/'hover_art');shutil.copyfile(R/'hover_verification.json',B/'hover_static_verification.json')
manifest=json.loads((B/'manifest.json').read_text('utf8'));protected=json.loads((B/'preservation.json').read_text('utf8'))
for q in protected['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed')
backup=ROOT/'work/ver_rin_nana/checkpoints/nana_fourth_before_hover_20261030';cards=[]
for i in (0,1):
 p=ROOT/f'work/ver_rin_nana/test_cards/nana_fourth_idle_v1/epsxe00{i}.mcr';require(digest(p)==digest(backup/p.name),'Card changed');cards.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
checkpoint=ROOT/'work/ver_rin_nana/checkpoints/nana_fourth_hover_20261030/SLUS_005.61.000';active=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';require(digest(checkpoint)==digest(active),'Checkpoint not restored')
state=gzip.decompress(active.read_bytes());player=state[442+0x1418c8:442+0x1418c8+0xe4]
evidence=[json.loads((B/f'runtime_{name}_check/verification.json').read_text('utf8')) for name in ('hover','hover_remaining','hover_back_shot')]
observations=[ROOT/q['observation'] for q in evidence];sampled=sorted({n for q in evidence for n in q['active_frames']});require(sampled==FRAMES,'New special references not all sampled')
runtime={'session':session,'pid':34012,'build':B.relative_to(ROOT).as_posix(),'bin_sha256':expected,'backup':backup.relative_to(ROOT).as_posix(),'checkpoint':checkpoint.relative_to(ROOT).as_posix(),'checkpoint_sha256':digest(active),'refresh_report':checkpoint.parent.relative_to(ROOT).as_posix()+'/refresh.json','evidence_kind':'normal key input after graphics-refreshed checkpoint; not fresh disc resource loading','checks':['runtime_hover_check/verification.json','runtime_hover_remaining_check/verification.json','runtime_hover_back_shot_check/verification.json'],'runtime_sampled_frames':sampled,'runtime_assets_verified':True,'full_display_verified_frames':sorted({n for q in evidence for n in q['full_display_verified_frames']}),'upper_body_verified_frames':sorted({n for q in evidence for n in q['upper_body_verified_frames']}),'entire_sprite_runtime_verified':False,'sampled_weapons':sorted({s['weapon'] for q in observations for s in json.loads((q/'observation.json').read_text('utf8'))['samples']}),'current_world_xy':[struct.unpack_from('<i',player,k)[0]//65536 for k in (8,12)],'hp':player[0x5c],'armor':player[0xa7],'arm_type':player[0xb8],'restored_weapon':player[0x93],'checkpoint_restored_exact':True,'memory_cards':cards,'protected_files_verified':len(protected['files']),'notes':[]}
restore=ROOT/'work/ver_rin_nana/nana_armor_hover/20261030T114346883265Z'
restored=json.loads((restore/'observation.json').read_text('utf8'));live=(restore/(restored['samples'][0]['prefix']+'_player.bin')).read_bytes()
require([struct.unpack_from('<i',live,k)[0]//65536 for k in (8,12)]==runtime['current_world_xy'],'Live restored position differs')
require((live[0x5c],live[0xa7],live[0x93])==(48,15,4),'Live restored state differs')
runtime.update(restored_live_observation=restore.relative_to(ROOT).as_posix(),restored_live_progress_verified=True)
runtime['notes']=['일반 점프·재점프·방향·대시·발사 입력으로12참조 실제 RAM/VRAM·팔레트 일치.',
    '전체 화면 픽셀 일치는93/221/224/225/226/227/228/229의8참조. 다른 참조의 전수 화면 검증은 미완료.',
    '전진·후진의 발/불꽃 접속을 실제 화면으로 검토. 양방향 모든 조합·부분 아머·다른 팔 종류·새 디스크 로딩 전수는 미검증.',
    '처음 긴 입력 계획에서는 호버 제한시간 후 발사해 일부 참조 미발생. 짧은 뒤로 사격 계획에서226/228 확인.',
    '작업 직전 새 F1의 위치411/395·HP48·아머15·팔2·선택무기4와 에너지 복원. 두 카드와20보호파일 동일.']
write(B/'hover_runtime_summary.json',runtime)
source={'tool':'built_in_imagegen','generated':(S/'generated.png').relative_to(ROOT).as_posix(),'generated_sha256':digest(S/'generated.png'),'prompt':(S/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(S/'prompt.txt'),'references':[{'path':(S/n).relative_to(ROOT).as_posix(),'sha256':digest(S/n)} for n in ('native_pose_reference.png','original_foot_reference.png','accepted_armor_reference.png')],'native_source_cell_order':[94,221,223,225,227,229],'final_art':A.relative_to(ROOT).as_posix(),'notes':[]}
source['notes']=['내장 imagegen 사용.3열2행 원화와 원작 발 위치·수용 나나 의상 참조.',
    '93은37 의상 전체 재사용. 호버10참조 상체는 대응 수용 공중/사격 의상을 픽셀 그대로 재사용.',
    '94 원화는 수용 얼굴·권총·다리 외곽에 등록. 호버 다리는 생성 원화의 하체만 추출해 발 위치와 허리 접점에 등록.',
    '221/223 하체는 같은 원화를 다른 발 위치에 등록.225/227의 하체만 반전해 원작 후진 발 방향에 맞춤.',
    '호버 기본 몸의 중복 다리만 제거하고 다리 아머가 하체 전체 소유. 다리 비트8 없는 호버는 게임에서 진입 불가.',
    '원래16색·압축 슬롯·효과·로직 보존. 새 리소스 재배치 없음.']
write(S/'source.json',source);write(B/'hover_source.json',source)
arc=(B/'modified.arc').read_bytes();board=Image.new('RGBA',(4*80,4*80));draw=ImageDraw.Draw(board)
for i,n in enumerate([0,37]+FRAMES):
 im=render(arc,n,True)[0].crop((40,40,120,112));board.alpha_composite(im,(i%4*80,i//4*80+8));draw.text((i%4*80+2,i//4*80),str(n),fill='white')
board.save(B/'hover_sheet_1x.png');board.resize((board.width*4,board.height*4),Image.Resampling.NEAREST).save(B/'hover_sheet_4x.png')
paths=['scripts/prepare_nana_fourth_hover_reference.py','scripts/prepare_nana_fourth_hover_art.py','scripts/prepare_nana_fourth_run.py','scripts/build_nana_fourth_idle.py','scripts/verify_nana_fourth_hover.py','scripts/prepare_nana_fourth_checkpoint.py','scripts/observe_nana_armor_hurt_palette.py','scripts/verify_nana_hurt_observation.py','scripts/nana_armor_input_plan.py',Path(__file__).relative_to(ROOT).as_posix()]
write(B/'hover_source_tools.json',[{'path':p,'sha256':digest(ROOT/p)} for p in paths])
pointer=ROOT/'projects/ver_rin_nana/current_build.json';p=json.loads(pointer.read_text('utf8'));require(p['sha256']==expected,'Pointer changed');p.update(current_session=session,hover_report='docs/NANA_FOURTH_HOVER.md',runtime_hover_sampled_frames=sampled,runtime_hover_assets_verified=True,runtime_hover_full_screen_verified=False,runtime_hover_upper_body_verified_frames=runtime['upper_body_verified_frames']);write(pointer,p)
candidate=ROOT/'projects/ver_rin_nana/nana_fourth_candidate.json';q=json.loads(candidate.read_text('utf8'));q.update(stage='ARMOR_HOVER_REVIEW',applied_frames=manifest['fourth_armor_frames']);q['hover_preparation']={'build':B.relative_to(ROOT).as_posix(),'sha256':expected,'art':A.relative_to(ROOT).as_posix(),'packed':(R/'hover_packed_v5').relative_to(ROOT).as_posix(),'frames':FRAMES,'current_game_applied':True,'user_accepted':False,'runtime_sampled_frames':sampled,'runtime_assets_verified':True,'runtime_full_screen_verified':False,'report':'docs/NANA_FOURTH_HOVER.md'};write(candidate,q);shutil.copyfile(candidate,B/'authorization.json')
print(json.dumps({'build':B.relative_to(ROOT).as_posix(),'applied_refs':len(manifest['fourth_armor_frames']),'runtime_frames':sampled,'restored_world_xy':runtime['current_world_xy'],'hp':runtime['hp'],'weapon':runtime['restored_weapon'],'cards_preserved':len(cards),'protected_files':len(protected['files'])}))
