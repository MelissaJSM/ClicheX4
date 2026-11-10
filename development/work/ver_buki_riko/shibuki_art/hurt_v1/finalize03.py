import json,sys,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_run import world_canvas
from src.psx_player import graphics_bank,decode_stream,composition_frame
import struct
d=Path(__file__).parent;a=d/'production03';b=ROOT/'out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z'
m=json.loads((b/'manifest.json').read_text());sha=digest(b/'shibuki_riko.bin');assert sha=='b5c27b8dd0b49b15a4205d406bbd9133860fcad2df00b930473c632721bea389'
arc=(b/'modified.arc').read_bytes();assert digest(b/'modified.arc')=='ab41cb67e99057eef6cfd357dfa09bd4501627b80601797e82485df328e45fca'
for run in ('20261026T141623075403Z','20261026T141646623354Z'):assert (ROOT/'work/ver_buki_riko/shibuki_hurt'/run/'modified.arc').read_bytes()==arc
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
files=['generated.png','prompt.txt','compact_generated.png','compact_prompt.txt','tucked_generated.png','tuck_prompt.txt','normalize03.py','prepare_effects03.py','optimize03.py']+[str(p.relative_to(d)) for p in a.iterdir() if p.is_file()]
put(d/'source_manifest.json',{'method':'builtin_imagegen_then_indexed_conversion','files':{n:digest(d/n) for n in files}})
entries=psx_arc(arc)
def entry(t):
 e=next(e for e in entries if int(e['type'],16)==t);return arc[e['offset']:e['offset']+e['size']]
gfx=entry(2);parts=entry(3);pal=struct.unpack('<48H',entry(9)[:96]);bank=graphics_bank(gfx,0,allow_bank_aliases=True)
sheet=Image.new('RGB',(96*5,96*2),'#28394b');dr=ImageDraw.Draw(sheet)
for j,n in enumerate(range(106,115)):
 f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;arr=world_canvas(raw,f['tile_count'],composition_frame(parts,0,n),allowed_cluts={0,2})
 im=save_image(arr.tobytes(),(96,80),pal,a/f'composed_{n:03d}.png').convert('RGBA');x=j%5*96;y=j//5*96;sheet.paste(im,(x,y+16),im);dr.text((x+5,y+2),str(n),fill='white')
sheet.save(b/'final_review_1x.png');sheet.resize((1440,576),Image.Resampling.NEAREST).save(b/'final_review_3x.png')
checks={'unit_tests':161,'negative_checks':json.loads((d/'negative_checks03.json').read_text()),'repeated_arc_identical':True,'full_disc_sectors_compared':m['full_disc_sectors_compared'],'changed_sectors':[s['lba'] for s in m['modified_bin']['changed_sectors']],'original_sha256':digest(ROOT/'MegaMan X4.bin'),'riko_accepted_sha256':digest(ROOT/'out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin'),'accepted94_frames_preserved':True,'armor_and_shared_effect_tiles_parts_preserved':True,'palette_timing_exe_preserved':True}
assert checks['original_sha256']==m['source_sha256'];assert checks['riko_accepted_sha256']=='1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246'
put(b/'static_checks.local.json',checks)
quote='오케이 피격문제없어 다음으로 진행하자';session='work/ver_buki_riko/emulator_sessions/20261026T141743450559Z'
runtime={'build_sha256':sha,'session':session,'launched':True,'automated_hurt_cycle_verified':False,'user_reported_hurt_accepted':True,'user_quote':quote,'process_memory_written':False,'save_state_load_save_keys_sent':False,'limitations':'사용자가 피격에 문제가 없다고 수용했다. 새 빌드 피격9참조의 RAM/VRAM/화면 전수 자동 검사는 수행하지 않았다.'};put(b/'runtime_summary.local.json',runtime)
shutil.copyfile(b/'manifest.json',b/'manifest.before_user_review.json');m.update(hurt_user_accepted=True,user_acceptance_quote=quote,new_animation_user_review_pending=False,base_sprite_references_applied=103,runtime_verified=False,runtime_summary=str((b/'runtime_summary.local.json').relative_to(ROOT)));put(b/'manifest.json',m)
back=b/'previous_pointers';back.mkdir()
for name in ('current_build.json','shibuki_current_build.json'):
 p=ROOT/'projects/ver_buki_riko'/name;shutil.copyfile(p,back/name);ptr=json.loads(p.read_text(encoding='utf-8'))
 ptr.update(kind='shibuki_hurt_accepted',build=str(b.relative_to(ROOT)),cue=str((b/'shibuki_riko.cue').relative_to(ROOT)),bin_sha256=sha,session=session,session_closed=False,session_paused=None,session_pause_capture=None,runtime_summary=m['runtime_summary'],runtime_verified_frames=[],runtime_whole_opaque_matched_frames=[],both_directions_verified=False,new_animation_user_review_pending=False,hurt_user_accepted=True,user_acceptance_quote=quote,hurt_art_applied=True,report='docs/SHIBUKI_HURT.md',next_group='ladder_actions',active_art_study='work/ver_buki_riko/shibuki_art/hurt_v1',base_sprite_references_applied=103);put(p,ptr)
put(ROOT/'projects/ver_buki_riko/shibuki_hurt_accepted_build.json',ptr)
put(ROOT/'projects/ver_buki_riko/shibuki_hurt_art_revision.json',{'source':str(a.relative_to(ROOT)),'build':str(b.relative_to(ROOT)),'style_user_accepted':True,'user_quote':quote,'runtime_automated_full_cycle_verified':False})
report=f'''# Shibuki 피격 동작

2026-10-26, `EXPANSION`, `ver_buki_riko/x_shibuki`. 일반 피격·공중 반동·감전/화염 표현9참조(106..114)를 추가했다. 사용자가 **“{quote}”**라고 수용했다. 누적103참조이며 다음 제작은 사다리 동작이다.

- CUE `{(b/'shibuki_riko.cue').relative_to(ROOT)}`
- BIN SHA-256 `{sha}`
- X ARC SHA-256 `{digest(b/'modified.arc')}`
- 원본 `{checks['original_sha256']}`, Riko `{checks['riko_accepted_sha256']}` 보존.

## 구조와 미술

로컬 미국판 애니메이션33/34/36/37의 몸을 교체했다. 106/107/108은 몸을 공유하고107/108에는 별도 전기선이 추가된다. 110/111은 몸을 공유하고111에는 별도 화염 링이 있다. 별도 효과 타일·파츠는 보존했다. 109/112/113/114의 몸 실루엣은 새 몸에 맞추되 원래 팔레트0/2를 유지했다. 특수 피격35의233..236은 별도 미제작 범위이며 이번 수용을 모든 피격 유형의 완료로 확대하지 않는다.

수용된 사람형 대기·공중 및 원작 피격 포즈를 참고해 내장 imagegen 원화를 제작했다. 같은 축척0.066으로 정규화했다. 일반 피격44픽셀, 굽힌 공중 피격39픽셀 높이는 자세 차이이며 따로 축소하지 않았다. 몸의 파츠가 한 프레임에서 다른 프레임으로 갈라지는 것을 피하도록 완성된 몸을 먼저 만들고 게임 저장 타일을 분할했다. 원화·프롬프트·도구 해시는 `hurt_v1/source_manifest.json`, 최종 인덱스 그림·배치는 `hurt_v1/production03`에 있다.

## 검사와 제한

161개 단위 검사와 잘못된 기본/효과 팔레트, 누락 프레임, 오래된 패킹 해시, 아머 쓰기 거부5건 통과. ARC 두 번 생성 동일. 전체251793섹터 비교 결과 변경은1234..1236,1389의4섹터뿐이다. 기존94참조·아머·Riko·타이밍·EXE·팔레트·리소스 위치를 유지했다. 원래6개 압축 공간 안에 정확한 픽셀로 삽입했다.

사용자 피격 확인은 수용되었다. **미실행:** 피격9참조 전체 RAM/VRAM/화면 자동 대조. 에뮬레이터 세션 `{session}`에서 새 빌드를 실행했다. 사용자 진행 중 포커스 없는 캡처 요청은 입력 없이 거부되었다. F1/F3와 메모리 쓰기를 사용하지 않았다. `capture_shibuki_hurt.py`는 준비만 했으며 이 빌드 자동 검증 근거로 사용하지 않는다.

[1배율](../{(b/'final_review_1x.png').relative_to(ROOT).as_posix()}), [3배율](../{(b/'final_review_3x.png').relative_to(ROOT).as_posix()}). `static_checks.local.json`, `runtime_summary.local.json`, `recipe.json`의 실제 실행 범위를 구분한다.
''';(ROOT/'docs/SHIBUKI_HURT.md').write_text(report,encoding='utf-8')
def prepend(name,txt):
 p=ROOT/'docs'/name;s=p.read_text(encoding='utf-8');i=s.index('\n');p.write_text(s[:i+1]+'\n'+txt+'\n'+s[i+1:],encoding='utf-8')
prepend('STATUS.md','**2026-10-26 최신 — Shibuki 피격 수용, 사다리 제작 착수.** 단계 `EXPANSION`, 활성 `ver_buki_riko/x_shibuki`, PS1 미국판. 현재 `shibuki_hurt_20261026T141724356492Z`, BIN `b5c27b8d…`, 누적103참조. 사용자가 “오케이 피격문제없어 다음으로 진행하자”라고 수용했다. 161검사·부정입력5·ARC 반복 동일·전체251793섹터 비교 통과, 변경4섹터. 기존94참조·원본·Riko·아머·EXE 보존. 피격 전수 자동 대조는 미실행. 특수 피격35는 별도 미제작. 다음은 실제 사다리 참조와 사격을 조사하여 제작한다. 추가 승인 필요 없음. [결과·해시·검증 범위](SHIBUKI_HURT.md). 아래는 이전 기록이다.')
prepend('DECISIONS.md','## 2026-10-26 — Shibuki 피격 수용\n\n사용자 “오케이 피격문제없어 다음으로 진행하자”. `production03`, BIN `b5c27b8d…`의 피격9참조를 수용 기준으로 보존한다. 다음 제작은 사다리와 사다리 사격. 사용자 관찰과 전수 자동 검증은 구분하며, 특수 피격35는 별도 미제작으로 남긴다.')
for name,txt in [('SHIBUKI_SPRITES.md','피격106..114 추가·사용자 수용, 누적103참조.'),('TEST_RESULTS.md','피격 단위161·부정입력5·반복ARC 동일·전체디스크 비교 통과. 변경4섹터. 사용자 실행 수용, 전수 자동 대조 미실행.'),('ART_DIRECTION.md','피격은 수용된 머리 폭과 체격에 맞춰 일반/공중을 같은 축척0.066으로 정규화. 다리를 굽힌 높이 차이를 체격 축소로 보정하지 않는다.'),('VERSION_COMPARISON.md','미국판 PS1 피격9참조를 원래 압축6슬롯에 삽입. 별도 감전/화염 파츠와 아머 보존, 사용자 수용. 플랫폼 변경 없음.')]:prepend(name,'**2026-10-26:** '+txt+' [근거와 한계](SHIBUKI_HURT.md).')
with (ROOT/'docs/COMMANDS.md').open('a',encoding='utf-8') as f:f.write('''\n\n## 2026-10-26 Shibuki 피격 (실행 완료)\n\n```powershell
python scripts/prepare_shibuki_hurt_plan.py
python scripts/prepare_shibuki_hurt.py --art work/ver_buki_riko/shibuki_art/hurt_v1/production03 --parent out/ver_buki_riko/shibuki_wall_20261026T135224131979Z
python scripts/build_shibuki_run.py --recipe work/ver_buki_riko/shibuki_hurt/20261026T141646623354Z/recipe.json
python scripts/emulator_session.py launch --cue out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z/shibuki_riko.cue
```\n''')
print(json.dumps({'accepted':True,'build':str(b),'next':'ladder_actions'}))
