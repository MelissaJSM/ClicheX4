from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(name):return (ROOT/'docs'/name).read_text(encoding='utf-8')
def write(name,text):(ROOT/'docs'/name).write_text(text,encoding='utf-8')
def prepend(name,section):
 text=read(name);head,tail=text.split('\n',1);write(name,head+'\n\n'+section.strip()+'\n'+tail)
write('STATUS.md','''# 프로젝트 상태

2026-10-23 KST. **ZERO_PRODUCTION — Riko 이동 반복 경계 수정·실행 검증**. 활성 프로젝트 `ver_buki_riko`, 작업 `zero_riko`. 전체 교체 완료는 아니다.

## 수행한 작업

사용자가 직전 이동에서도 끝과 처음의 연결이 어색하다고 지적했다.12/13/19/20 네 프레임을 수정해 앞발을 내미는 중간 자세와 다음 착지를 연결했다.13→14와20→7에서 머리·몸통·골반·뒷다리는 그대로이고 앞발이2픽셀 내려오며 착지한다. 이전에는7픽셀 내려가고 상체도 바뀌었다. 승인 대기와 점프를 포함한 다른34 PNG는 바이트까지 보존했다. 새 결과의 사용자 미술 평가는 아직 없다.

현재 시험판: `out/ver_buki_riko/riko_motion_20261023T143602957663Z/riko_motion.cue`.
BIN SHA-256: `3b7ffb07e1d731ae93c9cc5afa2a67603a8bdd3e763a4f9dec94c9ba0be5bfd4`.

상세 근거: [반복 경계 수정 기록](RIKO_RUN_LOOP_FIX.md). 실행 포인터: `projects/ver_buki_riko/current_build.json`. 현재 빌드의 `loop_before_after.gif`는 미리보기, `run_live_recording.gif`는 실제 게임 녹화다.

## 승인·플랫폼·입력

- PS1 미국판 `SLUS_005.61`, 원본 `MegaMan X4.bin`,592217136bytes. SHA-256 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`.
- Riko 설정화 SHA-256 `0537f596cf21b97916b1b59197890fc15a4460fd36026f560b817da471258796`. 승인 v2 PNG SHA-256 `0b54b9aad6ec09847131023bcbb5716fa696ac912bb4de4b24d85c38d710d81c`.
- 최신 수정 지시 원문은 [DECISIONS.md](DECISIONS.md). 직전 `f60f8a050b1a2b4894e0a09aad986935e34c2396a82635c2d13f9752584ae50a` 이동도 반복 연결 품질이 거부된 이력이다.
- 같은 위치/길이 압축·기존 정상 팔레트·별도 BIN 방식. 원본/설정화 입력 전용. EXE·판정·시간표·파츠·리소스 위치 변경 없음.
- 내장 image_gen에는 기존 Riko 파생물만 입력. 생성 앞다리 영역만 취하고 기존 전신의 나머지 부분을 보존했다. 게임 데이터 외부 전송·설치·공개·배포 없음.
- `ver_buki_riko`:Zero=Riko 우선,이후 X/아머=Buki. `ver_rin_nana`:Zero=Rin,X/아머=Nana 제작 보류. 일반/블랙 제로에 Riko/Rin을 나누지 않는다.

## 검사와 근거

| 검사 | 결과 |
| --- | --- |
| 반복 경계 | 두 경계의 앞다리 밖 변경0. 앞발 하강17→21→23,원래14슬롯/32tick. 파츠 밖·반전 U=0 열·클리핑0 |
| 삽입/보존 | 네 스트림530/546/536/534bytes,모두 원래 공간 안.444개 해제·432개 조립 비교에서 네 참조만 변경. 다른34 PNG·미해석12·모든 팔레트·파츠 동일 |
| 원본/재현 | 두 빌드 BIN 동일. 전체251793섹터 중15개 변경,EDC/ECC 유효. 원본 BIN/CUE/EXE/BIOS·설정화8장 해시 보존 |
| 자동 검사 | 37개 통과/exit0. `work/ver_buki_riko/art_pilot/run_loop_fix/test_result.json`. 기존 두 경계는 연속성 조건 실패,새 두 경계는 통과 |
| 실제 이동 | 3/4,7..20 및 정지5/6 모두 좌우 RAM·VRAM·전체 불투명 렌더 픽셀 일치. 여러 캡처의 성공 결과를 합친 범위 |
| 반복 실행 | 1.6초 방향키 입력의 오른쪽·왼쪽 trace에서7→…→20→7 완전한 주기2회씩 확인. 모든 주기 렌더를60fps 검사한 것은 아님 |
| 기존 동작 회귀 | 대기6개와 관찰 가능한 점프/착지 왼쪽 통과.32 미관찰. 현재 빌드 직접 확인37/38참조 |
| 녹화/종료 | 실제 창179장/4.977초,40fps 요청·실제 약36fps. ePSXe 한 개 사용 후 정상 종료,남은 제공 ePSXe0개 |

세션 `work/ver_buki_riko/emulator_sessions/20261023T143637197949Z/`. `live_poc/20261023T143833515321Z/`에서 character1=Zero와 새 bank를 확인했다. 메뉴 전체는 관찰하지 않아 완전한 콜드 부팅 검증으로 주장하지 않는다. 에이전트 F1/F3·게임 RAM 쓰기 없음. 초기 로딩/대기 캡처 실패와 피격 팔레트/전경 가림으로 실패한 중간 결과도 보존했다. 방향별 성공·반복 trace·실패 범위는 현재 빌드 `runtime_summary.json`에 있다.

## 남은 확인과 다음 작업

새 이동 연결의 미술 검수는 남아 있다. 기술적 픽셀 일치를 자연스러운 보행의 승인으로 취급하지 않는다. 낙하32·긴 낙하·대시 공유 전체·공격·벽·특수 기술·피격·사망·다른 CLUT·장면 전환은 미완료다. 대기/점프의 이번 회귀 방향은 왼쪽이며 이전 오른쪽 증거와 구분한다. 미교체 비트맵은 원본 제로와 새 정상 팔레트를 쓴다.

다음은 이동 연결 검토 결과 반영이다. 현재 Riko 보정에 추가 승인은 필요하지 않다. Buki/두 번째 프로젝트·로직/EXE/재배치 확대는 포함하지 않는다. Python3.13.14/Pillow12.3.0/NumPy2.5.1/ePSXe2.0.18 유지.

직전 상태: [반복 경계 수정 전](history/STATUS_20261023_BEFORE_RUN_LOOP_FIX.md). [명령](COMMANDS.md),[검사](TEST_RESULTS.md),[아트 기준](ART_DIRECTION.md),[플랫폼 비교](VERSION_COMPARISON.md).
''')
prepend('COMMANDS.md','''## 이동 반복 경계 수정 — 2026-10-23

아래 명령을 실제 실행했다. 준비 출력은 `run_loop_frames/20261023T143104731852Z`, 같은 빌드 명령의 두 출력은 `riko_motion_20261023T143602957663Z`, `riko_motion_20261023T143612759180Z`다. 새 실행은 새 시각 폴더를 반환한다.

```powershell
python scripts/prepare_riko_loop.py --extract work/ver_buki_riko/zero_extract/20261023T062408235550Z --previous-motion work/ver_buki_riko/run_revision_frames/20261023T140033413871Z/motion_set.json --art-dir work/ver_buki_riko/art_pilot/run_loop_fix
python -m unittest discover -s tests -v
python scripts/build_riko_idle.py --extract work/ver_buki_riko/zero_extract/20261023T062408235550Z --frames-dir work/ver_buki_riko/coherent_idle_frames/20261023T123358053306Z --motion-set work/ver_buki_riko/run_loop_frames/20261023T143104731852Z/motion_set.json
python scripts/verify_riko_build.py --build out/ver_buki_riko/riko_motion_20261023T143602957663Z --repeat out/ver_buki_riko/riko_motion_20261023T143612759180Z
python work/ver_buki_riko/art_pilot/run_loop_fix/review.py
```

準備 도구는 보존된 생성 앞다리 영역과 이전 프레임을 등록·팔레트 변환한다. 자체 그림 생성은 하지 않는다. 프레임12/13/19/20만 바꾸고 경계·발 하강·파츠·압축을 검사한다. 아래 PID49752/세션은 종료됐다. 재실행에는 새 PID와 기준 JSON을 사용한다.

```powershell
python scripts/emulator_session.py launch --cue out/ver_buki_riko/riko_motion_20261023T143602957663Z/riko_motion.cue
python scripts/capture_poc_memory.py --pid 49752 --build out/ver_buki_riko/riko_motion_20261023T143602957663Z --frame 147 --timeout 15
python scripts/capture_jump_cycle.py --build out/ver_buki_riko/riko_motion_20261023T143602957663Z --baseline work/ver_buki_riko/live_poc/20261023T143833515321Z/verification.local.json --run-direction right --run-hold 1.6
python scripts/capture_jump_cycle.py --build out/ver_buki_riko/riko_motion_20261023T143602957663Z --baseline work/ver_buki_riko/live_poc/20261023T143833515321Z/verification.local.json --run-direction left --run-hold 1.6
python scripts/capture_jump_cycle.py --build out/ver_buki_riko/riko_motion_20261023T143602957663Z --baseline work/ver_buki_riko/live_poc/20261023T143833515321Z/verification.local.json --run-direction left --run-hold 0.75
python scripts/record_riko_run.py --session work/ver_buki_riko/emulator_sessions/20261023T143637197949Z --hold 1.3 --fps 40
python scripts/capture_jump_cycle.py --build out/ver_buki_riko/riko_motion_20261023T143602957663Z --baseline work/ver_buki_riko/live_poc/20261023T143833515321Z/verification.local.json --idle
python scripts/capture_jump_cycle.py --build out/ver_buki_riko/riko_motion_20261023T143602957663Z --baseline work/ver_buki_riko/live_poc/20261023T143833515321Z/verification.local.json
python scripts/emulator_session.py close --session work/ver_buki_riko/emulator_sessions/20261023T143637197949Z
```

`--run-hold` 기본0.75초,허용0.15~2초. `record_riko_run.py --hold`는0.15~1.6초,`--fps`는20/40이다. 실제 시각·입력·프레임 trace를 저장한다. 부분 실패와 위치 이동/검 입력도 있었으므로 위 명령만 연속 실행하면 같은 화면 조건이라고 보장하지 않는다. 성공 범위는 [반복 경계 수정 기록](RIKO_RUN_LOOP_FIX.md)을 따른다. 아래 이전 수정 명령은 이력이다.
'''.replace('準備','준비'))
prepend('TEST_RESULTS.md','''## 2026-10-23 — 이동 반복 경계 수정

새 BIN `3b7ffb07e1d731ae93c9cc5afa2a67603a8bdd3e763a4f9dec94c9ba0be5bfd4`. 자동37개 통과,동일 BIN 재생성,원본251793섹터/설정화8장/EXE/BIOS 보존 검사 통과. 직전 빌드와444개 해제·432개 조립 비교에서12/13/19/20만 바뀌고 다른34 PNG는 동일하다. 기존 두 연결은 경계 검사 실패,새 연결은 통과했다.

현재 적용38참조 중37개 직접 표시 확인,32 미관찰. 이동3/4,7..20와 정지5/6은 여러 캡처를 합쳐 좌우 RAM/VRAM/전체 불투명 렌더 일치. 오른쪽·왼쪽 긴 입력 trace에서 완전한 반복 주기2회씩 관찰했으며,전경 가림 때문에 긴 왼쪽 캡처 전체 렌더 통과와 같은 뜻은 아니다. 대기6개와 관찰된 점프는 이번에 왼쪽 회귀 통과. 실제 녹화179장/4.977초,세션 정상 종료.

정적·실행·실패 로그와 방향별 증거는 [반복 경계 수정 기록](RIKO_RUN_LOOP_FIX.md),현재 빌드 `runtime_summary.json`,`verification_20261023T143622692830Z.local.json`에 있다. 피격 색상과 전경 가림 실패를 유지하고 허용 오차를 늘리지 않았다. 사용자 미술 승인·전체 캐릭터 완성을 뜻하지 않는다.
''')
text=read('ART_DIRECTION.md');head,rest=text.split('\n\n',1);_,tail=rest.split('## 현재 선택',1)
write('ART_DIRECTION.md',head+'''\n\n2026-10-23. 사용자가 선택한 v2와 허리 연결을 고친 대기를 유지한다. 이동 외곽선 수정 뒤에도 반복 끝→처음의 불연속을 지적해12/13/19/20을 다시 수정했다. 새 이동 연결은 사용자 검수 전이며 Buki 제작은 시작하지 않았다.

13→14와20→7에서 머리·몸통·골반·뒷다리를 동일하게 유지하고 앞발이 내려와 다음 착지로 연결되게 했다. 직전12/19에도 중간 발 내림 자세를 추가했다. 생성 출력 중 앞쪽 종아리/부츠 영역만 취하고 나머지는 기존 포즈를 보존했다. 원래14슬롯/32tick과 승인 대기·점프는 그대로다. 과거 공중 전환 포즈를 현재안으로 읽지 않는다. [반복 경계 수정 기록](RIKO_RUN_LOOP_FIX.md)에 생성·등록·픽셀 변화·반복 실행 근거를 기록했다. 수치와 렌더 일치가 자연스러운 움직임의 미술 승인은 아니다.

## 현재 선택'''+tail)
text=read('VERSION_COMPARISON.md');head,rest=text.split('\n\n',1);_,tail=rest.split('\n\n',1)
write('VERSION_COMPARISON.md',head+'''\n\n최신 **로컬 검증**: PS1 미국판 사본의 이동 반복 경계12/13/19/20을 재수정했다. 다른34 PNG와 원작 시간표·파츠·팔레트를 보존하고 좌우 이동 표시 및 여러 주기의 프레임 순서를 확인했다. 현재38참조 적용/37참조 직접 표시 확인,32 미관찰. 동일 BIN 재생성·원본 보존 검사를 통과했다. [반복 경계 수정 기록](RIKO_RUN_LOOP_FIX.md). 새 미술 품질은 사용자 검수 전이다. 추천 플랫폼은 PS1 미국판으로 유지하며 Steam 추가 실행 검증은 하지 않았다. 아래 비교·이전 성공 범위는 조사 이력이다.

'''+tail)
text=read('DECISIONS.md');marker='\n## 2026-10-23 — 이동 외곽선·보행 비대칭 수정 요청'
result='''
이번 결과는 `3b7ffb07e1d731ae93c9cc5afa2a67603a8bdd3e763a4f9dec94c9ba0be5bfd4`다.12/13/19/20만 수정하고 다른34 PNG를 보존했다. 다음 접지와의 몸통·골반을 일치시키고 앞발을 단계적으로 내려놓는다. 좌우 이동 실제 픽셀과 긴 입력의 반복 순서를 확인했으며,현재37/38참조 직접 표시 확인·32 미관찰이다. 새 미술 승인은 아직 없다. [반복 경계 수정 기록](RIKO_RUN_LOOP_FIX.md).
'''
text=text.replace(marker,'\n'+result+marker,1);write('DECISIONS.md',text)
prepend('RIKO_RUN_REVISION.md','''**이전 수정 이력:** 이 문서의 `f60f8a05…` 결과도 사용자가 반복 연결을 지적해 재수정했다. 현재 빌드·확인 범위는 [반복 경계 수정 기록](RIKO_RUN_LOOP_FIX.md)을 따른다. 아래 기술 통과를 사용자 미술 승인으로 읽지 않는다.''')
print('Updated STATUS, COMMANDS, TEST_RESULTS, ART_DIRECTION, VERSION_COMPARISON, DECISIONS, historical revision notice')
