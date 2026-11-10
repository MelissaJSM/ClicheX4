from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
def read(p):return json.loads(p.read_text('utf8'))
def write(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
def rel(p):return Path(p).relative_to(ROOT).as_posix()
B=Path(read(D/'builds.json')['build']['output']);H=read(B/'manifest.json')['modified_bin']['sha256']
M=Path(read(D/'master_export.json')['output']);split=Path(read(D/'master_split.json')['output'])
S='work/ver_buki_riko/emulator_sessions/20261025T103516397082Z'
R='work/ver_buki_riko/air_spin_runtime/20261025T103921081912Z/verification.local.json'
CS='work/ver_buki_riko/current_build_saves/20261025T103535877155Z'
verify=read(ROOT/R);save=read(ROOT/CS/'manifest.local.json')
ram=[int(n) for n,r in verify['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in r['samples'])]
summary={'build':rel(B),'bin_sha256':H,'session':S,'evidence':R,'ram_vram_palette_frames':ram,'full_screen_frames':verify['verified_frames'],'full_screen_unverified':[169],'user_style_size_accepted':True,'acceptance':'이제 괜찮네 다음으로 진행해도괜찮을거같아','current_save':CS,'save_bank0_equal':True,'save_bank1_present':True,'f3_bank_provenance':rel(D/'live_provenance.local.json'),'next_group':'hyouretsuzan','process_memory_written':False}
write(D/'runtime_summary.json',summary)
backup=D/'publication_backup';backup.mkdir(exist_ok=False)
for p in [ROOT/'projects/ver_buki_riko/current_build.json',ROOT/'projects/ver_buki_riko/master_sheet.json',ROOT/'docs/STATUS.md',ROOT/'docs/RIKO_AIR_SPIN.md']:shutil.copyfile(p,backup/p.name)
p=ROOT/'projects/ver_buki_riko/current_build.json';cur=read(p)
cur.update(kind='riko_air_spin_native_jump_design_v4',build=rel(B),cue=rel(B/'riko_motion.cue'),bin_sha256=H,session=S,session_closed=False,
 runtime_summary=rel(D/'runtime_summary.json'),runtime_verified_frames=verify['verified_frames'],bank1_set=rel(D/'recipe.json'),spin_verified_frames=verify['verified_frames'],
 spin_ram_vram_verified_frames=ram,spin_style_user_review_pending=False,spin_style_size_user_accepted=True,current_build_save=CS,
 original_saber_effect_references_preserved=71,preserved_unedited_body_references=[{'bank':1,'frame':133}],
 spin_body_size_checks=rel(D/'body_size_checks.json'),all_current_frames_preview=rel(M/'riko_master_preview_2x.png'),
 session_state_at_last_observation='Current bank0 and bank1 loaded; spin tested; ice originals captured',
 session_state_evidence='work/ver_buki_riko/save_validation/20261025T103853320633Z/progress.local.json',
 next_task='Hyouretsuzan body16 and shared recovery frames; effect animation121 uses separate parts6',
 save_roundtrip=rel(D/'live_provenance.local.json'),agent_loaded_save_state=True,
 spin_previous_candidates_rejected=['air_spin_v1: style','air_spin_v2: body size','air_spin_v3: body size and clothing design'])
write(p,cur)
p=ROOT/'projects/ver_buki_riko/master_sheet.json';cur=read(p);cur.update(source_build=rel(B),source_bin_sha256=H,directory=rel(M),master=rel(M/'master.local.json'),sheet=rel(M/'riko_master_indexed.png'),preview=rel(M/'riko_master_preview_2x.png'),roundtrip=rel(split/'validation.local.json'),spin_art_review_pending=False,spin_body_size_checks=rel(D/'body_size_checks.json'),next_group='hyouretsuzan');write(p,cur)
report=f'''# Riko 공중 회전 베기

2026-10-25. PS1 미국판 `SLUS_005.61`, `ver_buki_riko/zero_riko`, ZERO_PRODUCTION.

## 현재 결과와 사용자 검토

현재는 **v4 — 기존 점프21의 디자인·체격을 기준으로 다시 만든 회전 베기**다. 사용자 “이제 괜찮네 다음으로 진행해도괜찮을거같아”를 이번 디자인·체격 수용과 다음 기술 진행 지시로 기록했다. v1은 스타일, v2는 작은 몸, v3는 여전히 작은 몸과 의상 표현 때문에 거부됐다.

새 머리를 만들지 않고 기존23×19 기준의 불투명309픽셀을 보존한다. 몸통·접힌 다리·긴 부츠·흰 의상의 명암·청록 망토는 실제 기존 Riko 점프와 비교했다. v3의 회전 기본형33×40/몸437픽셀에서 v4의41×42/몸541픽셀로 바뀌었다. 기준 점프21은 몸586픽셀이다. 면적 검사는 축소 재발을 거르는 보조 검사이며 체형·그림체의 자동 품질 증명이 아니다.

원본 제로 회전 그림은 로컬에서 자세·실루엣을 비교했다. 내장 image_gen 입력은 기존 Riko 파생 그림뿐이다. 기존 점프 직접 편집과 부츠 접기 편집2회, 원출력·프롬프트는 `work/ver_buki_riko/art_pilot/air_spin_v4/`에 보존했다. 원본 게임·설정화는 수정하지 않았다.

몸 참조 `132,160,161,163,165,167,169,171,173,175`. 회전8장은 같은 배율·중심에서45도 간격으로 만들고 원래 파츠 안에 배치했다. 프레임별 축소·몸 잘라내기·파츠/원점/시간표/판정/EXE/리소스 재배치는 하지 않았다. 준비132와 회수160은 기존 공중 공격229/213을 재사용한다.

**분류 정정:** 원본으로 보존한133은 효과가 아니라 빙열참97의 몸이다. 앞선 레시피의 `preserved_effect_frames`라는 역사적 필드에는133도 포함돼 있지만 바이트 보존 목적이며, 현 마스터에서는 미제작 몸으로 구분한다. 회전 효과는162..176 짝수8참조이며 그대로다. 누적 제작183몸/섬광 + 보존71효과 + 보존 미제작 몸133 한 참조다.132는 빙열참,160은 용염인 회수에서도 쓰인다.

## 빌드·정적 검사

- CUE: `{rel(B/'riko_motion.cue')}`
- BIN SHA-256: `{H}`
- 원본 BIN SHA-256: `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`
- 103개 자동 검사 통과. 기존236 PNG 동일, 새 몸10참조만 조립 그림 변경, 보존9참조(효과8+몸133) 동일.
- 같은 입력의 두 BIN 동일. 원본19참조의 무변경 왕복은 그래픽 엔트리 바이트 동일.70개 변경 섹터 EDC/ECC 확인. 최소 압축 여유116바이트.
- 마스터 `{rel(M)}`.183 PNG·ARC 무변경 왕복 동일: `{rel(split/'validation.local.json')}`.
- 아트 폴더 `art_checks.json`, `head_checks.json`, `body_size_checks.json`, `preservation_audit.json`, `verify_result.json`에 검사 근거가 있다.

## 실제 실행과 저장

세션 `{S}`, PID16108. 에이전트가 새 BIN/CONTINUE/카드 선택을 진행한 뒤 사용자가 게임 진입을 마쳤다. 그 중간 입력은 전부 관찰하지 못했으므로 완전한 자동 카드 로드 기록으로 주장하지 않는다. 이후 읽기 전용 검사에서 **현 bank0 전체 일치 및 현 bank1 전체의 RAM 내 존재**를 확인했다. 검증된 bank1로 실행되는 애니메이션100만 관찰 도구가 수집한다.

`{R}`: 몸10참조 모두 RAM·VRAM·팔레트 일치.132/160/161/163/165/167/171/173/175는 같은 표본의 전체 불투명 화면도 일치했다. **169는 전체 화면 일치 미확인**이며 성공으로 세지 않는다. 일반 입력 재생 기록은 `input_playback/20261025T103921744839Z/`다. 이전 v3의 HUD 가림 표본·포커스 중단은 현 성공 증거에서 제외한다.

현재 빌드용 F1 `{CS}`. SHA-256 `{save['state_sha256']}`.제로·8보스0xFF·HP48·Jungle707.5/426, 메뉴에서 저장. 저장 안의bank0 전체·bank1 전체 존재 확인 후 F3에서도 같은 은행을 확인했다. 원본 카드 SHA-256 `b0a596dba2e0e6ba6cdaaf87a894990365f0a33ee2b8d6536f6a5eb2298d77f9` 보존. 그림이 달라지는 다음 빌드에는 이 F1을 그대로 로드하지 않는다.

사용자 지시에 따라 한 방향을 우선한다. 미관찰 반대 방향·모든 지형/취소/피격 조합을 완료로 표시하지 않는다. 다음은 빙열참97/98과 공유 회수 자세다.
'''
(ROOT/'docs/RIKO_AIR_SPIN.md').write_text(report,'utf8')
status=f'''# 프로젝트 상태

2026-10-25 KST. **ZERO_PRODUCTION — 회전 베기 v4 디자인·체격 수용, 빙열참 조사·제작 진행.** 활성 `ver_buki_riko/zero_riko`, PS1 미국판.

현재 CUE `{rel(B/'riko_motion.cue')}`, BIN SHA-256 `{H}`.

회전 베기는 기존 Riko 점프의 옷·부츠·체격으로 재제작했다. 사용자 “이제 괜찮네 다음으로 진행해도괜찮을거같아”에 따라 이 버전을 유지한다. 이전236 PNG 보존, 누적183몸/섬광·71효과 보존.133은 미제작 빙열참 몸으로 분류를 정정했다. 전체 캐릭터 완성은 아니다.

103개 검사·반복 BIN 동일·70섹터 EDC/ECC·183 PNG/ARC 마스터 왕복 통과. 회전 몸10참조 RAM/VRAM/팔레트 일치,9참조 전체 화면 일치.169 전체 화면 및 반대 방향은 미확인이다. [전체 근거](RIKO_AIR_SPIN.md).

공통 마스터 `{rel(M)}`. 현재 작업용 F1 `{CS}`, 저장 해시 `{save['state_sha256']}`.새 bank0/bank1 로딩과 F3 복귀 확인. 메뉴 저장→F3→V로 재개 가능하다. 원본 카드·저장은 보존했다. 현재 실행 세션 `{S}`.

## 다음 작업과 확인 범위

빙열참97/98의 몸16참조를 실제 게임에서 포착했다. `work/ver_buki_riko/ice_identification/20261025T104446387845Z/identification.local.json`. 공중 아래+특수D로 발동하며 일반 베기S와 다르다. 무기ID0x21/애니메이션121은 실제 조립bank6을 사용한다. 과거 준비 시트의bank1/parts5 효과0/1 그림은 이 기술의 효과 증거로 사용할 수 없다. 공유133·회수86/87/95/98와 압축 공유 묶음을 포함해 그림 제작·왕복·실기 확인을 이어간다. 빙열참 Riko 전체 적용은 아직 미완료다.

사용자 추가 세이브는 필요 없다. Buki/Rin/Nana·아머·로직·판정·EXE·파츠·리소스 배치 변경으로 확대하지 않는다. 남은 사다리/벽 전체 화면, 기절·사망, 다른 특수 공격과 전체 지형 조합은 별도 미완료다.

미국판 원본 `SLUS_005.61`,592217136 bytes,SHA-256 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`. 설정화 SHA-256 `0537f596cf21b97916b1b59197890fc15a4460fd36026f560b817da471258796`.

기존80개에 더해 오래된 출력9개를 복원 해시 확인 후 차이 ZIP으로 정리했다. 추가 약4.96GiB 절약; 로그 `work/ver_buki_riko/art_pilot/air_spin_v3/compact_results.jsonl`. 최신 v4와 반복 빌드는 이후 추가됐다. [복원 방법](STORAGE_MAINTENANCE.md). 이전 STATUS/포인터는 현재 아트의 `publication_backup/`에 보존했다.
'''
(ROOT/'docs/STATUS.md').write_text(status,'utf8')
def prepend(path,title,text):
 p=ROOT/path;s=p.read_text('utf8');first,rest=s.split('\n',1);p.write_text(first+'\n\n'+title+'\n\n'+text+'\n'+rest.lstrip('\n'),'utf8')
prepend('docs/DECISIONS.md','## 2026-10-25 — 회전 베기 체격·도트 재수정과 v4 수용',
 '사용자가 작은 몸과 기존 스프라이트와 다른 디자인을 다시 지적했다. 머리/면적만으로 품질을 판단하던 v3를 폐기하고 기존 점프21을 직접 편집 기준으로 v4를 제작했다. 이어 “이제 괜찮네 다음으로 진행해도괜찮을거같아”에 따라 v4 디자인·체격을 수용하고 빙열참 작업으로 진행한다. 미국판 원본 해시·제로·같은 길이 그래픽 교체 범위는 그대로이며 이번 지시가 전체 특수 기술 완성 승인은 아니다. [결과](RIKO_AIR_SPIN.md).\n')
prepend('docs/TEST_RESULTS.md','## 2026-10-25 — 회전 베기 v4와 빙열참 실행 식별',
 '103개 검사, 반복 BIN 동일,70개 수정 섹터 EDC/ECC, 기존236 PNG 보존,183 PNG·ARC 마스터 왕복 동일. 회전10몸 RAM/VRAM/팔레트 일치,9몸 전체 화면 일치,169 전체 화면 미확인. 현 bank0/bank1을 F1 및 F3에서 확인했다. [전체 해시·근거](RIKO_AIR_SPIN.md). 빙열참97/98의16몸과 무기ID0x21의parts6 연결은 별도 읽기 전용 실기 관찰로 확인했다.\n')
prepend('docs/COMMANDS.md','## 2026-10-25 — 회전 베기 v4',
 f'''다음 명령을 실행했다. PID/기준점은 해당 세션에만 유효하다.

```powershell
python -m unittest discover -s tests -q
python scripts/capture_jump_cycle.py --build {rel(B)} --baseline work/ver_buki_riko/live_poc/20261025T103853924418Z/bank_baseline.local.json --air-spin --observe
python work/ver_buki_riko/art_pilot/hyouretsuzan_v1/inspect_runtime.py
```

아트·빌드·마스터 재현 스크립트와 프롬프트는 `work/ver_buki_riko/art_pilot/air_spin_v4/`에 있다. `build_and_verify.py`는 이미 있는 `builds.json`의 덮어쓰기를 거부한다. [실행 결과](RIKO_AIR_SPIN.md).\n''')
print(json.dumps({'build':rel(B),'master':rel(M),'runtime':rel(D/'runtime_summary.json')}))
