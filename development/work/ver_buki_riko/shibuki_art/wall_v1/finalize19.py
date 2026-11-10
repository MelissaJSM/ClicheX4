import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
d=Path(__file__).parent;a=d/'production19'
build=ROOT/'out/ver_buki_riko/shibuki_wall_20261026T135224131979Z'
m=json.loads((build/'manifest.json').read_text());expected='1019123e5d1a155aed7cb18bc63ef0c574cfeae06eae1b8cf06f321ca1026a30'
assert digest(build/'shibuki_riko.bin')==expected
for run in ('20261026T135213180606Z','20261026T135319202968Z'):
 assert (ROOT/'work/ver_buki_riko/shibuki_wall'/run/'modified.arc').read_bytes()==(build/'modified.arc').read_bytes()
for name,sha in json.loads((d/'source_manifest19.json').read_text())['files'].items():assert digest(d/name)==sha
checks={'unit_tests':161,'negative_checks':json.loads((d/'negative_checks19.json').read_text()),'repeated_arc_identical':True,'full_disc_sectors_compared':m['full_disc_sectors_compared'],'changed_sectors':[s['lba'] for s in m['modified_bin']['changed_sectors']],'body_metrics':json.loads((a/'body_metrics.json').read_text()),'original_sha256':digest(ROOT/'MegaMan X4.bin'),'riko_accepted_sha256':digest(ROOT/'out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin'),'other_bitmaps_compositions_preserved':True,'all_nonselected_tiles_including_armor_preserved':True,'palette_timing_exe_preserved':True}
assert checks['original_sha256']==m['source_sha256'] and checks['riko_accepted_sha256']=='1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246'
def put(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
put(build/'static_checks.local.json',checks)
session='work/ver_buki_riko/emulator_sessions/20261026T135242686561Z'
quote='오케이 사이즈 알맞아 바로 다음작업가자'
runtime={'build_sha256':expected,'session':session,'launched':True,'automated_wall_cycle_verified':False,'user_reported_size_accepted':True,'user_quote':quote,'process_memory_written':False,'save_state_load_save_keys_sent':False,'limitations':'사용자가 수정 크기를 수용하고 바로 다음 작업으로 진행하도록 지시했다. 새 빌드 벽 12참조 전체의 RAM/VRAM/화면 자동 대조는 수행하지 않았다. 사용자 크기 수용과 전체 동작 자동 검증을 구분한다.'}
put(build/'runtime_summary.local.json',runtime)
shutil.copyfile(build/'manifest.json',build/'manifest.before_user_review.json')
m.update(wall_style_user_accepted=True,wall_size_user_accepted=True,user_acceptance_quote=quote,new_animation_user_review_pending=False,base_sprite_references_applied=94,runtime_verified=False,runtime_summary=str((build/'runtime_summary.local.json').relative_to(ROOT)),accepted_dash_preserved=True)
put(build/'manifest.json',m)
back=build/'previous_pointers';back.mkdir()
for name in ('current_build.json','shibuki_current_build.json'):
 p=ROOT/'projects/ver_buki_riko'/name;shutil.copyfile(p,back/name);ptr=json.loads(p.read_text(encoding='utf-8'))
 ptr.update(kind='shibuki_wall_accepted',build=str(build.relative_to(ROOT)),cue=str((build/'shibuki_riko.cue').relative_to(ROOT)),bin_sha256=expected,session=session,session_closed=False,session_paused=None,session_pause_capture=None,runtime_summary=m['runtime_summary'],runtime_verified_frames=[],runtime_whole_opaque_matched_frames=[],runtime_dust_occluded_frames=[],both_directions_verified=False,automated_wall_cycle_verified=False,new_animation_user_review_pending=False,wall_style_user_accepted=True,wall_size_user_accepted=True,user_acceptance_quote=quote,wall_art_applied=True,dash_style_user_accepted=True,accepted_dash_preserved=True,report='docs/SHIBUKI_WALL.md',next_group='hurt_actions',active_art_study='work/ver_buki_riko/shibuki_art/wall_v1',base_sprite_references_applied=94)
 put(p,ptr)
put(ROOT/'projects/ver_buki_riko/shibuki_wall_accepted_build.json',ptr)
put(ROOT/'projects/ver_buki_riko/shibuki_wall_art_revision.json',{'source':str(a.relative_to(ROOT)),'build':str(build.relative_to(ROOT)),'method':'builtin_imagegen_then_indexed_palette_registration','relative_scale_to_first_candidate':0.9,'style_user_accepted':True,'size_user_accepted':True,'user_quote':quote,'runtime_automated_full_cycle_verified':False})
for name in ('final_review_1x.png','final_review_3x.png'):shutil.copyfile(a/name,build/name)
report='''# Shibuki 벽 동작

2026-10-26, `EXPANSION`, `ver_buki_riko/x_shibuki`. 수용된 대시 다음으로 벽 붙기·벽 점프·벽 미끄러지기 및 벽 버스터 12참조를 추가했다. 사용자가 첫 후보의 벽 체격이 크다고 지적했고, 원화를 동일 비율로 다시 정규화한 수정본을 **“오케이 사이즈 알맞아 바로 다음작업가자”**라고 수용했다. 다음 제작은 피격 동작이다.

현재 CUE: `out/ver_buki_riko/shibuki_wall_20261026T135224131979Z/shibuki_riko.cue`.

- BIN SHA-256 `1019123e5d1a155aed7cb18bc63ef0c574cfeae06eae1b8cf06f321ca1026a30`
- X ARC SHA-256 `d1b5960ec1744f904f3527732b619fe7ff7814b392032d97a478c6ba68802982`
- 부모 대시 BIN `fb434ef6a229b669cd502520e280fb8453a808af6f38d24cb0a2e2131ee092d5`
- 미국판 원본 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`
- Riko 수용본 `1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246`

## 확인된 구조

| 동작 | 일반 애니메이션 / 참조 | 사격 애니메이션 / 참조 |
| --- | --- | --- |
| 벽 붙기 | 13: 55,61,63 | 125: 56,62,64 |
| 벽 점프 | 14: 55,57,59,39 | 126: 56,58,60,40 |
| 미끄러지기 | 15: 65 | 127: 66 |

**로컬 검증:** 12참조는 6개의 압축 스트림을 공유한다. 39/40은 수용된 공중 그림을 재사용하며 보존했다. 아머 뱅크5..8의 타일은 쓰기 대상과 겹치지 않는다. 원본은 오른쪽 벽에서 몸을 왼쪽으로 돌린다. 조사 근거는 `scripts/prepare_shibuki_wall_plan.py`, `wall_v1/plan.json`, 미국판 추출 인벤토리와 로컬 디컴파일 `src/main/player.c:304`, `player_enter.c:370`이다.

## 미술과 크기 수정

내장 imagegen으로 원화와 두 차례 자세 보완을 생성했다. `wall_v1/generated.png`, `compact_generated.png`, `contact_generated.png`와 각 프롬프트를 보존했다. 수용된 사람형 Shibuki 대기·공중·원작 X 벽 자세를 기준으로 제작했고, 새 의상이나 아머를 추가하지 않았다.

첫 적용 후보 `production16`은 높이45..51픽셀, 일부 상체와 머리 폭이 기존 공중 자세보다 크게 보였다. **동일 축척이라는 사실만으로 프레임 간 체격이 같다고 판단한 한계**를 사용자 피드백으로 확인했다. 최종 `production19`는 원화 축척0.15→0.135, 공통90%로 다시 픽셀화했다. 높이는40..46픽셀이며 굽힌 다리와 들어 올린 손의 차이가 있으므로 모든 자세의 바깥 높이를 같게 강제하지 않았다. 일반·사격 쌍의 눈 기준점은 일치한다.

벽에 닿는 손바닥과 얼굴 높이를 다시 등록하고, 팔 교체 마스크도 같은 비율로 이동했다. 버스터는 수용된 정지 사격 팔을 원작 총구 좌표에 등록했다. 첫 후보의 압축용 내부 명암10픽셀 수정은 최종19에 전용하지 않았다. 최종19는 재정규화한 픽셀 그대로 원래 압축 공간에 들어간다.

- [최종 1배율](../work/ver_buki_riko/shibuki_art/wall_v1/production19/final_review_1x.png), [3배율](../work/ver_buki_riko/shibuki_art/wall_v1/production19/final_review_3x.png)
- 원화/도구 해시 `wall_v1/source_manifest19.json`, 인덱스 그림·기준점 `production19/art.json`, `pairs.json`, `body_metrics.json`
- 배치 `layout19.json`, `production19/packing.json`
- 최종 recipe `work/ver_buki_riko/shibuki_wall/20261026T135213180606Z/recipe.json`

## 검사와 제한

161개 단위 검사, 잘못된 팔레트·누락 프레임·오래된 패킹 해시·아머 타일 쓰기 거부4건 통과. ARC 재생성 `20261026T135319202968Z`와 바이트 동일. 전체251793섹터를 부모와 비교해 X 데이터와 EDC/ECC의6섹터(1214..1218,1388)만 달라졌다. ARC 크기796672, 파일 위치, 애니메이션 타이밍, 팔레트, EXE, 아머와 비대상 파츠·비트맵을 보존했다. 미국판 원본과 Riko 수용본 해시도 재확인했다. 기존82참조에 벽12를 더한 누적94참조이며 전체 X 완성은 아니다.

**사용자 관찰:** 수정한 벽 동작 크기를 수용했다. **미실행:** 최종 벽12참조의 좌우 RAM·VRAM·화면 전수 자동 대조. 사용자의 바로 다음 작업 지시에 따라 벽 검증을 늘리지 않고 피격 제작으로 진행한다. 전체 자동 검증 완료로 보고하지 않는다.

최종 에뮬레이터 세션 `20261026T135242686561Z`, PID18072. 이전 후보의 idle 관찰은 데모 재생 중 요청 자세가 포착되지 않아 실패했고 성공 근거에 포함하지 않았다. 저장 상태 키 F1/F3, 메모리 쓰기는 사용하지 않았다. 현재 포인터와 수용본 포인터를 갱신했다. [정적 검사](../out/ver_buki_riko/shibuki_wall_20261026T135224131979Z/static_checks.local.json), [실행 범위 기록](../out/ver_buki_riko/shibuki_wall_20261026T135224131979Z/runtime_summary.local.json).
'''
(ROOT/'docs/SHIBUKI_WALL.md').write_text(report,encoding='utf-8')
def prepend(name,text):
 p=ROOT/'docs'/name;old=p.read_text(encoding='utf-8');i=old.find('\n');p.write_text(old[:i+1]+'\n'+text+'\n'+old[i+1:],encoding='utf-8')
prepend('STATUS.md','**2026-10-26 최신 — 벽 체격 수정 수용, 피격 제작 착수.** 단계 `EXPANSION`, 활성 `ver_buki_riko/x_shibuki`. 현재 BIN `1019123e…`, `shibuki_wall_20261026T135224131979Z`, 아트 `wall_v1/production19`. 벽 일반/사격12참조를 추가해 누적94참조. 첫 벽 후보가 크게 보인다는 피드백 후 원화를 공통90%로 재정규화했고 사용자가 “오케이 사이즈 알맞아 바로 다음작업가자”라고 수용했다. 161검사·부정입력4건·ARC 반복 동일·전체251793섹터 비교 통과. 기존82참조·아머·Riko·원본 보존. 벽12참조의 양방향 자동 전수 검사는 미실행이며 사용자 크기 수용과 구분한다. [결과와 해시](SHIBUKI_WALL.md). 다음은 일반/강한 피격 동작의 원본 참조 조사 및 제작이다. 새 피격 미술 수용은 아직 없고, 로직/아머/UI/이름/음성 범위를 확대하지 않는다.')
p=ROOT/'docs/DECISIONS.md';old=p.read_text(encoding='utf-8');marker='## 2026-10-26 — Shibuki 공중 정렬 수용';idx=old.index(marker)
p.write_text('# 결정 기록\n\n## 2026-10-26 — 대시 수용, 벽 제작 및 크기 수정 수용\n\n사용자가 “좋아 다음으로 바로 진행하자”라고 하여 수용된 대시 `fb434ef6…` 다음으로 벽12참조를 제작했다. 첫 벽 후보에 “벽타기가 크기가 큰건가...? 대기모션 - 점프 까지는 사이즈맞는거같은데 유독 벽타기가 사이즈크게느껴진다?”라고 지적했다. 원화 축척을0.15→0.135로 재정규화한 `production19`, BIN `1019123e…`에 대해 “오케이 사이즈 알맞아 바로 다음작업가자”라고 수용했다. 벽 크기를 수용 기준으로 고정하고 일반/강한 피격을 다음 제작 대상으로 선택한다. 사용자 크기 수용을 자동 전수 검증으로 간주하지 않으며 원본 타이밍·판정·아머·기존94참조·Riko를 유지한다.\n\n'+old[idx:],encoding='utf-8')
prepend('SHIBUKI_SPRITES.md','**2026-10-26 최신:** 벽55..66의12참조 추가, 누적94참조. 큰 체격이라는 피드백을 반영해 공통90%로 재정규화했고 사용자가 크기를 수용했다. 현재 `wall_v1/production19`, BIN `1019123e…`. 자동 전수 실행 검사는 미실행이며 다음은 피격이다. [벽 결과·한계](SHIBUKI_WALL.md).')
prepend('TEST_RESULTS.md','**2026-10-26 Shibuki 벽 크기 수정본:** 단위161·부정입력4·ARC 반복 동일·디스크251793섹터 비교 통과. 변경6섹터. 원본/Riko/기존82참조/아머 보존. 사용자가 벽 크기를 수용. 최종 벽 전수 RAM/VRAM/화면 자동 검사는 미실행. [근거](SHIBUKI_WALL.md).')
prepend('ART_DIRECTION.md','**2026-10-26 Shibuki 벽 수용 기준:** `wall_v1/production19`, 원화 공통축척0.135. 첫 후보0.15는 상체와 머리가 커 보였다는 사용자 피드백이 있었다. 전체 축척뿐 아니라 수용 대기·공중과 머리 폭·상체 부피를 직접 비교한다. 손을 든 높이와 굽힌 다리 때문에 전체 바깥 높이를 무조건 같게 강제하지 않는다. 일반/사격은 같은 몸을 쓰며 벽 접점과 총구를 다시 등록했다.')
prepend('VERSION_COMPARISON.md','**2026-10-26 추가 로컬 검증:** 미국판 PS1 경로에서 X 벽12참조를 원래6개 스트림 공간에 넣었다. 원본 파일 크기/주소/타이밍과 아머 타일 보존, 전체 디스크 비교 통과. 사용자 크기 수용은 확인했고 자동 벽 전수 실행 검사는 미실행이다. 플랫폼 비교를 새로 반복하지 않는다. [결과](SHIBUKI_WALL.md).')
with (ROOT/'docs/COMMANDS.md').open('a',encoding='utf-8') as f:f.write('''\n\n## 2026-10-26 Shibuki 벽 크기 수정본\n\n실행 완료 명령이다. 최종 원화/팔레트/타일 결과는 별도 보존한다.\n\n```powershell
python scripts/prepare_shibuki_wall_plan.py
python scripts/prepare_shibuki_run.py --scope wall --art work/ver_buki_riko/shibuki_art/wall_v1/production19 --pairs work/ver_buki_riko/shibuki_art/wall_v1/production19 --layout work/ver_buki_riko/shibuki_art/wall_v1/layout19.json --parent out/ver_buki_riko/shibuki_dash_20261026T113618370649Z
python scripts/build_shibuki_run.py --recipe work/ver_buki_riko/shibuki_wall/20261026T135213180606Z/recipe.json
python scripts/emulator_session.py launch --cue out/ver_buki_riko/shibuki_wall_20261026T135224131979Z/shibuki_riko.cue
```
''')
print(json.dumps({'build':str(build),'accepted':True,'automated_wall_verified':False}))
