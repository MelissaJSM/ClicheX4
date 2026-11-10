"""특수 자세7참조의 최종 출처·실행 근거와 활성 포인터를 기록한다."""
import json,sys,shutil,gzip,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_fourth_pilot import write,require,render
from scripts.prepare_nana_fourth_special_reference import FRAMES
from scripts.project import digest
from PIL import Image,ImageDraw
B=ROOT/'out/ver_rin_nana/nana_fourth_special_20261030T110429756883Z';R=ROOT/'work/ver_rin_nana/nana_fourth_armor';A=R/'special_art_v5';S=R/'special_v1';session='work/ver_rin_nana/emulator_sessions/20261030T110532195324Z'
expected='3c95814cca35499b47c96152c30a15e7791ec062fedd54a19eba50ba368bdb23';require(digest(B/'rin_nana.bin')==expected,'BIN changed')
shutil.copytree(A,B/'special_art');shutil.copyfile(R/'special_verification.json',B/'special_static_verification.json')
manifest=json.loads((B/'manifest.json').read_text('utf8'));protected=json.loads((B/'preservation.json').read_text('utf8'))
for q in protected['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed')
backup=ROOT/'work/ver_rin_nana/checkpoints/nana_fourth_before_special_20261030';cards=[]
for i in (0,1):
 p=ROOT/f'work/ver_rin_nana/test_cards/nana_fourth_idle_v1/epsxe00{i}.mcr';require(digest(p)==digest(backup/p.name),'Card changed');cards.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
checkpoint=ROOT/'work/ver_rin_nana/checkpoints/nana_fourth_special_20261030/SLUS_005.61.000';active=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';require(digest(checkpoint)==digest(active),'Checkpoint not restored')
state=gzip.decompress(active.read_bytes());player=state[442+0x1418c8:442+0x1418c8+0xe4]
evidence=[json.loads((B/f'runtime_{name}_check/verification.json').read_text('utf8')) for name in ('charge','cyclone')]
observations=[ROOT/q['observation'] for q in evidence];sampled=sorted({n for q in evidence for n in q['active_frames']});require(sampled==FRAMES,'New special references not all sampled')
runtime={'session':session,'pid':35148,'build':B.relative_to(ROOT).as_posix(),'bin_sha256':expected,'backup':backup.relative_to(ROOT).as_posix(),'checkpoint':checkpoint.relative_to(ROOT).as_posix(),'checkpoint_sha256':digest(active),'refresh_report':checkpoint.parent.relative_to(ROOT).as_posix()+'/refresh.json','evidence_kind':'normal key input after graphics-refreshed checkpoint; not fresh disc resource loading','checks':['runtime_charge_check/verification.json','runtime_cyclone_check/verification.json'],'runtime_sampled_frames':sampled,'runtime_assets_verified':True,'full_display_verified_frames':sorted({n for q in evidence for n in q['full_display_verified_frames']}),'upper_body_verified_frames':sorted({n for q in evidence for n in q['upper_body_verified_frames']}),'entire_sprite_runtime_verified':False,'sampled_weapons':sorted({s['weapon'] for q in observations for s in json.loads((q/'observation.json').read_text('utf8'))['samples']}),'current_world_xy':[struct.unpack_from('<i',player,k)[0]//65536 for k in (8,12)],'hp':player[0x5c],'armor':player[0xa7],'arm_type':player[0xb8],'restored_weapon':player[0x93],'checkpoint_restored_exact':True,'memory_cards':cards,'protected_files_verified':len(protected['files']),'notes':['차지2초 후 해제와 추가 발사1회로88..91 실제 재생.','일반 메뉴에서 아래4회/확인/닫기로 더블 사이클론 선택,3회 발사로97..99 재생.','상체89 401픽셀/90 386픽셀/98과99의 같은 상체405픽셀 일치. 전체 몸은 물 전경 때문에 미검증.','좌우 전수·공중 사이클론·다른 팔 종류·새 디스크 자원 로딩은 이번 실기에 포함하지 않는다.']}
write(B/'special_runtime_summary.json',runtime)
source={'tool':'built_in_imagegen','generated':(S/'generated.png').relative_to(ROOT).as_posix(),'generated_sha256':digest(S/'generated.png'),'prompt':(S/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(S/'prompt.txt'),'references':[{'path':(S/n).relative_to(ROOT).as_posix(),'sha256':digest(S/n)} for n in ('native_pose_reference.png','accepted_armor_reference.png')],'native_source_cell_order':[89,90,91,97,98,0],'final_art':A.relative_to(ROOT).as_posix(),'notes':['배경 발광은 알파192 이상 캐릭터 연결 성분 정규화에서 배제.','원래 얼굴/손/권총/발 외곽 기준점 보존.88과99는 같은 의상의 수평 이동 재사용.','97은 다리3파츠에 맞춰 기존 구두 밑3행 보존. 흰 치맛단과 베일은 다리 파츠 유지.','생성6번째 대기는 참고용이며 수용 대기를 덮어쓰지 않음.']}
write(S/'source.json',source);write(B/'special_source.json',source)
arc=(B/'modified.arc').read_bytes();board=Image.new('RGBA',(3*80,3*80));draw=ImageDraw.Draw(board)
for i,n in enumerate([0,85]+FRAMES):
 im=render(arc,n,True)[0].crop((40,32,120,104));board.alpha_composite(im,(i%3*80,i//3*80+8));draw.text((i%3*80+2,i//3*80),str(n),fill='white')
board.save(B/'special_sheet_1x.png');board.resize((board.width*4,board.height*4),Image.Resampling.NEAREST).save(B/'special_sheet_4x.png')
paths=['scripts/prepare_nana_fourth_special_reference.py','scripts/prepare_nana_fourth_special_art.py','scripts/prepare_nana_fourth_run.py','scripts/build_nana_fourth_idle.py','scripts/verify_nana_fourth_special.py','scripts/prepare_nana_fourth_checkpoint.py','scripts/observe_nana_armor_hurt_palette.py','scripts/verify_nana_hurt_observation.py',Path(__file__).relative_to(ROOT).as_posix()]
write(B/'special_source_tools.json',[{'path':p,'sha256':digest(ROOT/p)} for p in paths])
pointer=ROOT/'projects/ver_rin_nana/current_build.json';p=json.loads(pointer.read_text('utf8'));require(p['sha256']==expected,'Pointer changed');p.update(current_session=session,special_report='docs/NANA_FOURTH_SPECIALS.md',runtime_special_sampled_frames=sampled,runtime_special_assets_verified=True,runtime_special_full_screen_verified=False,runtime_special_upper_body_verified_frames=runtime['upper_body_verified_frames']);write(pointer,p)
candidate=ROOT/'projects/ver_rin_nana/nana_fourth_candidate.json';q=json.loads(candidate.read_text('utf8'));q.update(stage='ARMOR_SPECIAL_REVIEW',applied_frames=manifest['fourth_armor_frames']);q['special_preparation']={'build':B.relative_to(ROOT).as_posix(),'sha256':expected,'art':A.relative_to(ROOT).as_posix(),'packed':(R/'special_packed_v5').relative_to(ROOT).as_posix(),'frames':FRAMES,'current_game_applied':True,'user_accepted':False,'runtime_sampled_frames':sampled,'runtime_assets_verified':True,'runtime_full_screen_verified':False,'report':'docs/NANA_FOURTH_SPECIALS.md'};write(candidate,q);shutil.copyfile(candidate,B/'authorization.json')
print(json.dumps({'build':B.relative_to(ROOT).as_posix(),'applied_refs':len(manifest['fourth_armor_frames']),'runtime_frames':sampled,'restored_world_xy':runtime['current_world_xy'],'hp':runtime['hp'],'weapon':runtime['restored_weapon'],'cards_preserved':len(cards),'protected_files':len(protected['files'])}))
