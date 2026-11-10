"""탑승 의상 적용과 실제 확인 범위를 구분하여 기록한다."""
import gzip,json,shutil,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_pilot import write,require,render,entry
from scripts.prepare_nana_fourth_vehicle_reference import FRAMES,EDITED_FRAMES
from scripts.project import digest
from src.psx_player import composition_frame
from src.psx_sprite_batch import canvas_from_parts
from src.epsxe_state import framebuffer,match_sprite
B=ROOT/'out/ver_rin_nana/nana_fourth_vehicle_20261030T120015393777Z';R=ROOT/'work/ver_rin_nana/nana_fourth_armor';A=R/'vehicle_art_v4';S=R/'vehicle_v1'
expected='5618ee1ab54f16bfee9b0a1b4d3472be3508da4babd8dce2ac7676f7c66d0e6d';session='work/ver_rin_nana/emulator_sessions/20261030T120124114968Z'
require(digest(B/'rin_nana.bin')==expected,'BIN changed');shutil.copytree(A,B/'vehicle_art');shutil.copyfile(R/'vehicle_verification.json',B/'vehicle_static_verification.json')
manifest=json.loads((B/'manifest.json').read_text('utf8'));protected=json.loads((B/'preservation.json').read_text('utf8'))
for q in protected['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed')
backup=ROOT/'work/ver_rin_nana/checkpoints/nana_fourth_before_vehicle_20261030';current=json.loads((backup/'current.json').read_text('utf8'));cards=[]
for i in (0,1):
 p=ROOT/f'work/ver_rin_nana/test_cards/nana_fourth_idle_v1/epsxe00{i}.mcr';require(digest(p)==digest(backup/p.name),'Card changed');cards.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
checkpoint=ROOT/'work/ver_rin_nana/checkpoints/nana_fourth_vehicle_20261030/SLUS_005.61.000';active=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';require(digest(checkpoint)==digest(active),'Checkpoint differs')
observation=ROOT/'work/ver_rin_nana/nana_armor_hover/20261030T120211726012Z';obs=json.loads((observation/'observation.json').read_text('utf8'));require(obs['bin_sha256']==expected and obs['session']==session,'Wrong observation');sample=obs['samples'][0];require(sample['frame']==0 and sample['ram_vram_texture_equal'],'No live baseline')
live=(observation/(sample['prefix']+'_player.bin')).read_bytes();xy=[struct.unpack_from('<i',live,k)[0]//65536 for k in (8,12)];require(xy==current['world_xy'] and (live[0x5c],live[0xa7],live[0xb8],live[0x93])==(current['hp'],current['armor'],current['arm'],current['weapon']),'Live progress differs')
arc=(B/'modified.arc').read_bytes();pal=entry(arc,9);c=entry(arc,3);video=(observation/(sample['prefix']+'_vram.bin')).read_bytes();_,_,f,raw=render(arc,0);colors={};palette_rows={}
upload=bytearray()
for first in range(0,f['tile_count'],16):
 width=min(16,f['tile_count']-first)*8
 for y in range(16):pos=(first//16*16+y)*2048+640;upload.extend(video[pos:pos+width])
require(bytes(upload)==raw,'Captured texture differs')
for b,address in ((0,sample['body_clut']),(5,0x7843),(6,0x7843),(7,0x7844),(8,0x7843)):
 pos=(address>>6)*2048+(address&63)*32;data=video[pos:pos+32];rows=[i for i in range(len(pal)//32) if pal[i*32:i*32+32]==data];require(rows,'Live palette differs');words=struct.unpack('<16H',data);palette_rows[str(b)]=rows;colors[b]=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255 if i else 0] for i,w in enumerate(words)],np.uint8)
im=Image.new('RGBA',(160,160))
for b in (0,8,5,7,6):im.alpha_composite(Image.fromarray(colors[b][canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,0))]))
sprite=im.crop(im.getbbox());matches=[]
for page in (0,240):
 found=match_sprite(framebuffer(video,0,page),sprite)
 if found:matches.append({'page':page,'matches':found})
sprite.resize((sprite.width*4,sprite.height*4),Image.Resampling.NEAREST).save(B/'vehicle_idle_expected_4x.png')
runtime={'build':B.relative_to(ROOT).as_posix(),'bin_sha256':expected,'session':session,'pid':37064,'observation':observation.relative_to(ROOT).as_posix(),'discovery':'work/ver_rin_nana/live_poc/20261030T120131248287Z/discovery.local.json','evidence_kind':'graphics-refreshed F3; not fresh disc resource loading','observed_frames':[0],'new_vehicle_frames_observed':[],'idle_ram_vram_texture_equal':True,'all_ram_assets_2_3_9_equal':True,'palette_arc_rows':palette_rows,'idle_full_frame_matches':matches,'new_vehicle_runtime_verified':False,'backup':backup.relative_to(ROOT).as_posix(),'checkpoint':checkpoint.relative_to(ROOT).as_posix(),'checkpoint_sha256':digest(active),'refresh_report':checkpoint.parent.relative_to(ROOT).as_posix()+'/refresh.json','live_world_xy':xy,'hp':live[0x5c],'armor':live[0xa7],'arm_type':live[0xb8],'weapon':live[0x93],'live_progress_preserved':True,'memory_cards':cards,'protected_files_verified':len(protected['files']),'notes':[]}
runtime['notes']=['현재 웨브 스파이더스 구간에는 탑승 기체가 없어 새32참조 실기는 미실행.','관찰 도구의 hover 모드는 첫 대기 표본만 얻는 데 사용했으며 새 호버나 탑승 시험으로 계산하지 않음.','전체 자원2/3/9의 RAM 동일성과 대기0 텍스처·팔레트를 확인. F1은 그래픽3739바이트만 갱신하고 위치448/395·체력46·아머15·무기0·에너지를 보존.']
write(B/'vehicle_runtime_summary.json',runtime)
source={'tool':'built_in_imagegen','generated':(S/'generated.png').relative_to(ROOT).as_posix(),'generated_sha256':digest(S/'generated.png'),'prompt':(S/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(S/'prompt.txt'),'references':[{'path':(S/n).relative_to(ROOT).as_posix(),'sha256':digest(S/n)} for n in ('native_pose_reference.png','accepted_armor_reference.png')],'cell_order':[162,166,170,174],'final_art':A.relative_to(ROOT).as_posix(),'notes':['내장 imagegen의 체이서4자세를 원래16색과 수용 얼굴·손·다리 외곽에 등록했다.','머리19참조는 수용0/37/94의 머리 도트를 눈 위치에 맞춰 재사용. 대기0의 초록 장식 픽셀을 눈으로 오인하지 않도록 최상단 눈 픽셀만 사용한다.','같은 압축 스트림의 동작은 원래 조립 이동량을 따라 동일 도트를 이동한다.','머리 타일만 교체하며 공용 빈 타일과 빈198은 그대로 유지한다. 기본형·효과·팔레트·게임 로직 보존.','9압축 슬롯 안에서 삽입.193/195 스트림만 이전 압축 끝보다10/12바이트 늘지만 기존 할당 경계 내이며 주소·은행·ARC 크기는 유지한다.']}
write(S/'source.json',source);write(B/'vehicle_source.json',source)
board=Image.new('RGBA',(6*80,6*80));draw=ImageDraw.Draw(board)
for i,n in enumerate([0,37]+EDITED_FRAMES):
 im=render(arc,n,True)[0].crop((40,32,120,104));board.alpha_composite(im,(i%6*80,i//6*80+8));draw.text((i%6*80+2,i//6*80),str(n),fill='white')
board.save(B/'vehicle_sheet_1x.png');board.resize((board.width*4,board.height*4),Image.Resampling.NEAREST).save(B/'vehicle_sheet_4x.png')
paths=['scripts/prepare_nana_fourth_vehicle_reference.py','scripts/prepare_nana_fourth_vehicle_art.py','scripts/prepare_nana_fourth_run.py','scripts/build_nana_fourth_idle.py','scripts/verify_nana_fourth_vehicle.py','scripts/prepare_nana_fourth_checkpoint.py','scripts/observe_nana_armor_hurt_palette.py',Path(__file__).relative_to(ROOT).as_posix()]
write(B/'vehicle_source_tools.json',[{'path':p,'sha256':digest(ROOT/p)} for p in paths])
pointer=ROOT/'projects/ver_rin_nana/current_build.json';p=json.loads(pointer.read_text('utf8'));require(p['sha256']==expected,'Pointer changed');p.update(current_session=session,vehicle_report='docs/NANA_FOURTH_VEHICLES.md',runtime_vehicle_sampled_frames=[],runtime_vehicle_verified=False,runtime_vehicle_baseline_verified=True);write(pointer,p)
candidate=ROOT/'projects/ver_rin_nana/nana_fourth_candidate.json';q=json.loads(candidate.read_text('utf8'));q.update(stage='ARMOR_VEHICLE_REVIEW',applied_frames=manifest['fourth_armor_frames']);q['hover_preparation'].update(packed='work/ver_rin_nana/nana_fourth_armor/hover_packed_v2',user_accepted=True);q['vehicle_preparation']={'build':B.relative_to(ROOT).as_posix(),'sha256':expected,'art':A.relative_to(ROOT).as_posix(),'packed':(R/'vehicle_packed_v1').relative_to(ROOT).as_posix(),'frames':EDITED_FRAMES,'blank_preserved':[198],'current_game_applied':True,'user_accepted':False,'runtime_sampled_frames':[],'runtime_baseline_verified':True,'report':'docs/NANA_FOURTH_VEHICLES.md'};write(candidate,q);shutil.copyfile(candidate,B/'authorization.json')
print(json.dumps({'build':B.relative_to(ROOT).as_posix(),'applied_refs':len(manifest['fourth_armor_frames']),'new_vehicle_runtime_verified':False,'idle_display_matches':matches,'world_xy':xy,'hp':live[0x5c],'weapon':live[0x93],'cards_preserved':len(cards),'protected_files':len(protected['files'])}))
