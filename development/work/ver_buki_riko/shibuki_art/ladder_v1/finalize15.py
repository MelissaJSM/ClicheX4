import json,sys,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
d=Path(__file__).parent;a=d/'production15';b=ROOT/'out/ver_buki_riko/shibuki_ladder_20261026T150541813461Z';m=json.loads((b/'manifest.json').read_text());sha=digest(b/'shibuki_riko.bin');assert sha=='8d364ddaa12721b4ce383ef1e1b015a7f5d0fbdf1a722f1ea383126e1febf09e'
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
assert (ROOT/'work/ver_buki_riko/shibuki_ladder/20261026T150532768823Z/modified.arc').read_bytes()==(b/'modified.arc').read_bytes()
sheet=Image.new('RGB',(5*96,3*96),'#28394b');dr=ImageDraw.Draw(sheet)
for i,n in enumerate([0]+list(range(143,156))+[183]):
 path=d.parent/'standing_buster_v1/parent_000.png' if n==0 else a/f'frame_{n:03d}.png';im=Image.open(path).convert('RGBA');x=i%5*96;y=i//5*96;sheet.paste(im,(x,y+16),im);dr.text((x+5,y+2),str(n),fill='white')
sheet.save(b/'final_review_1x.png');sheet.resize((1440,864),Image.Resampling.NEAREST).save(b/'final_review_3x.png')
files=['generated.png','prompt.txt','compact_generated.png','compact_prompt.txt','tucked_generated.png','tuck_prompt.txt','tail_generated.png','tail_prompt.txt','normalize02.py','assemble03.py','prepare04.py','prepare13.py','optimize13.py','consolidate15.py']+[str(p.relative_to(d)) for p in a.iterdir() if p.is_file()];put(d/'source_manifest15.json',{'files':{n:digest(d/n) for n in files}})
checks={'unit_tests':165,'negative_checks':json.loads((d/'negative_checks15.json').read_text()),'repeated_arc_identical':True,'full_disc_sectors_compared':m['full_disc_sectors_compared'],'changed_sectors':[s['lba'] for s in m['modified_bin']['changed_sectors']],'original_sha256':digest(ROOT/'MegaMan X4.bin'),'riko_accepted_sha256':digest(ROOT/'out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin'),'accepted103_frames_preserved':True,'armor_palette_timing_exe_preserved':True,'native_palette_consolidation':json.loads((a/'palette_consolidation.json').read_text())};assert checks['original_sha256']==m['source_sha256'];assert checks['riko_accepted_sha256']=='1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246';put(b/'static_checks.local.json',checks)
quote='일단 인트로 스테이지에는 사다리 잡는게 없어. 그러니까 완성하고 바로 다음으로 넘어가자. 나중에 내가 사다리있는곳가면 한번 테스트해볼게'
runtime={'build_sha256':sha,'launched':False,'ladder_runtime_verified':False,'user_visual_acceptance':False,'runtime_deferred_at_user_request':True,'user_quote':quote,'save_states_or_memory_writes_used':False};put(b/'runtime_summary.local.json',runtime)
m.update(base_sprite_references_applied=117,runtime_verified=False,runtime_deferred_at_user_request=True,runtime_summary=str((b/'runtime_summary.local.json').relative_to(ROOT)));put(b/'manifest.json',m)
back=b/'previous_pointers';back.mkdir()
for name in ('current_build.json','shibuki_current_build.json'):
 p=ROOT/'projects/ver_buki_riko'/name;shutil.copyfile(p,back/name);v=json.loads(p.read_text(encoding='utf-8'));v.update(kind='shibuki_ladder_candidate',build=str(b.relative_to(ROOT)),cue=str((b/'shibuki_riko.cue').relative_to(ROOT)),bin_sha256=sha,session=None,session_closed=None,session_paused=None,session_pause_capture=None,previous_running_session='work/ver_buki_riko/emulator_sessions/20261026T141743450559Z',runtime_summary=m['runtime_summary'],runtime_verified_frames=[],runtime_whole_opaque_matched_frames=[],both_directions_verified=False,new_animation_user_review_pending=True,ladder_art_applied=True,ladder_runtime_deferred=True,report='docs/SHIBUKI_LADDER.md',next_group='low_hp_idle',active_art_study='work/ver_buki_riko/shibuki_art/low_hp_v1',base_sprite_references_applied=117);put(p,v)
put(ROOT/'projects/ver_buki_riko/shibuki_ladder_build.json',v)
report=f'''# Shibuki 사다리 동작

2026-10-27, `EXPANSION`, `ver_buki_riko/x_shibuki`. 일반 X의 사다리 진입·상승·하강·상단 이탈·사격14참조를 제작하여 미국판 작업용 BIN에 넣었다. 사용자 요청으로 사다리 인게임 검사는 보류하고 체력 부족 대기 제작으로 진행한다. **미술 수용·인게임 성공으로 기록하지 않는다.**

- CUE `{(b/'shibuki_riko.cue').relative_to(ROOT)}`
- BIN `{sha}`
- ARC `{digest(b/'modified.arc')}`
- 원본 `{checks['original_sha256']}`, Riko `{checks['riko_accepted_sha256']}` 보존.

## 확인한 구조

실제 미국판 애니메이션27..32와92/93이다. 참조143..155 및183을 교체했다. 상단 이탈에서 재사용하는 이동1은 기존 수용 그림을 유지했다. 전체15참조 중 신규 교체14,9개 압축 스트림이다. 144/145,146/147,148/149,151/152는 원작의 반전을 유지한다. 반전 중심은144/145와 나머지가1픽셀 다르므로 원작 파츠 관계를 검사해 재현했다. 148/149/150은 같은 스트림을 공유하며 일반/사격 몸을 공동으로 배치했다. 아머 뱅크5..8의 모든 타일과 파츠를 보존했다.

근거: `scripts/prepare_shibuki_ladder_plan.py`, `ladder_v1/plan.json`, 미국판 추출 인벤토리, 로컬 디컴파일 `player_enter.c:462`, `player.c:704`, `player_special.c:506`. 디컴파일의 조건 해석과 실제 실행 증거를 구분한다.

## 미술

설정화 뒷면과 수용 대기·공중·원작 사다리 포즈를 참고한 내장 imagegen 원화를 사용했다. 머리가 작았던 초안을 보완했고, 최종 원화 축척은 공통0.14다. 손을 든 높이·무릎 굽힘 때문에 전체 높이를 동일 사각형으로 강제하지 않았다. 반전 자세는 같은 픽셀을 재사용한다. 사격은149의 몸과 기존 수용 버스터 팔을 함께 사용하며 원작 총구 좌표에 등록했다.

상단 포즈153은 소매를 몸에 붙였다. 154는 체격을 줄이지 않고 꼬리를 다리 뒤에 접은 원화로 보완했다. 마지막 원래906바이트 공간을 맞추기 위해154의 의상 내부 명암2픽셀만 근접 색으로 정리했다. 알파·얼굴·외곽은 보존했다. 이전5..12의 명암/저장 실험은 채택하지 않았다. 최종 `ladder_v1/production15`, 원화/도구 해시 `source_manifest15.json`. 기존103참조를 유지하여 누적117참조다.

## 검사와 남은 확인

165개 단위 검사, 잘못된 팔레트·누락 프레임·오래된 패킹 해시·아머 쓰기 거부4건 통과. ARC 두 번 생성 동일. 전체251793섹터 비교에서 X 데이터와 EDC/ECC의9섹터(1245..1249,1254,1255,1389,1390)만 변경. 모든14참조의 재조립 결과가 최종 인덱스 PNG와 동일하다. 비대상 비트맵508참조, 비대상 조립, 타이밍, 팔레트, 아머, EXE 및 파일 위치를 검사했다.

**미실행:** 실제 사다리에서 손발 접점, 상단 진입/이탈 좌표 전환, 좌우 사격·반동의 화면 확인. 사용자 지시: “{quote}”. 새 빌드를 아직 실행하지 않았으며 이전 피격 빌드의 실행 결과를 대신 사용하지 않는다. 저장 상태·메모리 쓰기 없음. 후일 사다리가 있는 곳에서 이14참조를 테스트한다.

[1배율](../{(b/'final_review_1x.png').relative_to(ROOT).as_posix()}), [3배율](../{(b/'final_review_3x.png').relative_to(ROOT).as_posix()}). 상세 검사 `static_checks.local.json`, 보류 이유 `runtime_summary.local.json`.
''';(ROOT/'docs/SHIBUKI_LADDER.md').write_text(report,encoding='utf-8')
def prepend(name,txt):
 p=ROOT/'docs'/name;s=p.read_text(encoding='utf-8');i=s.index('\n');p.write_text(s[:i+1]+'\n'+txt+'\n'+s[i+1:],encoding='utf-8')
prepend('STATUS.md','**2026-10-27 최신 — 사다리14참조 적용, 사용자 요청으로 실행 검사 보류.** 단계 `EXPANSION`, 활성 `ver_buki_riko/x_shibuki`, PS1 미국판. 현재 `shibuki_ladder_20261026T150541813461Z`, BIN `8d364dda…`, 누적117참조. 165검사·부정입력4·반복ARC 동일·전체디스크 비교 통과. 사다리 플레이·미술 수용은 미확인이다. 사용자가 나중에 사다리 있는 곳에서 검사하겠다고 지시하여 장소 탐색/실행을 하지 않았다. 현재 진행은 체력 부족 대기6참조120..125이며 원화와 정규화 초안을 준비했다. 기존103참조·아머·Riko·원본·EXE 보존. [결과·해시·한계](SHIBUKI_LADDER.md).')
prepend('DECISIONS.md','## 2026-10-27 — 사다리 실행 검사 보류와 다음 동작 진행\n\n사용자 “'+quote+'”. 사다리를 정적 검사 및 작업용 BIN 적용까지 마치고, 실제 플레이 검사는 사용자 후속 확인으로 남긴다. 이는 미술 수용/전체 실행 검증 승인이 아니다. 체력 부족 대기6참조를 다음 기본형 제작으로 선택했다. 아머 작업 질문에는 기본형 기준과 도구를 재사용할 수 있으나 파츠별 부분 장착·공유·별도 동작 검수는 남는다고 설명했다. 아머 신규 제작을 착수하지 않았다.')
for name,txt in [('TEST_RESULTS.md','사다리14참조: 단위165·거부4·ARC 반복 동일·전체251793섹터 비교 통과. 실제 실행은 사용자 요청으로 보류.'),('SHIBUKI_SPRITES.md','사다리14참조 추가, 누적117. 현재 production15. 실행/미술 수용은 보류, 다음은 체력 부족 대기.'),('ART_DIRECTION.md','사다리는 뒷모습 매듭·꼬리와 수용된 사람형 체격을 유지. 공통 원화 축척0.14, 상단 자세는 소매/꼬리를 접어 저장 범위를 맞추었다. 사격 몸을 공유한다.'),('VERSION_COMPARISON.md','미국판 PS1 사다리14참조를 원래9슬롯에 재삽입. 반전/아머 공유 보존 및 정적 검사 완료. 실행 미검증이며 플랫폼 변경 없음.')]:prepend(name,'**2026-10-27:** '+txt+' [근거](SHIBUKI_LADDER.md).')
with (ROOT/'docs/COMMANDS.md').open('a',encoding='utf-8') as f:f.write('''\n\n## 2026-10-27 Shibuki 사다리 (실행 완료 명령)\n\n```powershell
python scripts/prepare_shibuki_ladder_plan.py
python scripts/prepare_shibuki_ladder.py --art work/ver_buki_riko/shibuki_art/ladder_v1/production15 --parent out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z
python scripts/build_shibuki_run.py --recipe work/ver_buki_riko/shibuki_ladder/20261026T150502986653Z/recipe.json
python -m unittest discover -s tests
```
\n사용자 지시로 사다리 실행 명령은 수행하지 않았다.\n''')
print(json.dumps({'build':str(b),'runtime_deferred':True,'next':'low_hp_idle'}))
