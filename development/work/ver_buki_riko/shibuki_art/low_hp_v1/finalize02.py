import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
d=Path(__file__).parent;a=d/'production02';b=ROOT/'out/ver_buki_riko/shibuki_low_hp_20261026T151338348062Z';m=json.loads((b/'manifest.json').read_text());sha=digest(b/'shibuki_riko.bin');assert sha=='843bd4ae691c7d18e619070fcb9e4c9dafe9d7be02970fd49f1eb78aea6a1981'
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
assert (ROOT/'work/ver_buki_riko/shibuki_low_hp/20261026T151337461659Z/modified.arc').read_bytes()==(b/'modified.arc').read_bytes()
sheet=Image.new('RGB',(4*96,2*96),'#28394b');dr=ImageDraw.Draw(sheet);metrics=[]
for row in range(2):
 for col,n in enumerate([0,120+row,122+row,124+row]):
  path=d.parent/'standing_buster_v1/parent_000.png' if n==0 else a/f'frame_{n:03d}.png';im=Image.open(path).convert('RGBA');sheet.paste(im,(col*96,row*96+16),im);dr.text((col*96+5,row*96+2),str(n),fill='white')
  if n:
   pix=np.array(Image.open(path));yy,xx=np.nonzero(pix);metrics.append({'frame':n,'bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'foot_row':int(yy.max()),'opaque_pixels':int(len(xx))})
sheet.save(b/'final_review_1x.png');sheet.resize((1152,576),Image.Resampling.NEAREST).save(b/'final_review_3x.png');put(a/'body_metrics.json',metrics);shutil.copyfile(a/'breathing_preview.gif',b/'breathing_preview.gif')
files=['generated.png','prompt.txt','normalize01.py','prepare02.py','optimize02.py']+[str(p.relative_to(d)) for p in a.iterdir() if p.is_file()];put(d/'source_manifest02.json',{'method':'builtin_imagegen_then_indexed_breathing_and_mouth_overlay','files':{n:digest(d/n) for n in files}})
checks={'unit_tests':165,'negative_checks':json.loads((d/'negative_checks02.json').read_text()),'repeated_arc_identical':True,'full_disc_sectors_compared':m['full_disc_sectors_compared'],'changed_sectors':[s['lba'] for s in m['modified_bin']['changed_sectors']],'original_sha256':digest(ROOT/'MegaMan X4.bin'),'riko_accepted_sha256':digest(ROOT/'out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin'),'previous117_frames_preserved':True,'armor_palette_timing_exe_preserved':True,'body_metrics':metrics};assert checks['original_sha256']==m['source_sha256'];assert checks['riko_accepted_sha256']=='1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246';put(b/'static_checks.local.json',checks)
session='work/ver_buki_riko/emulator_sessions/20261026T151425524412Z';quote='좋아 체력부족 모션도 충분해';runtime={'build_sha256':sha,'session':session,'pid':46676,'launched':True,'screen_capture':session+'/20261026T151527272805Z.png','capture_observation':'인트로 게임 화면 및 Shibuki 피격 플래시가 보였다. 체력 부족6참조의 자동 실행 대조를 대신하지 않는다.','user_acceptance_quote':quote,'user_accepted_low_hp':True,'automated_low_hp_cycle_verified':False,'ladder_runtime_deferred':True,'process_memory_written':False,'save_state_keys_sent':False};put(b/'runtime_summary.local.json',runtime)
shutil.copyfile(b/'manifest.json',b/'manifest.before_user_review.json');m.update(low_hp_user_accepted=True,user_acceptance_quote=quote,new_animation_user_review_pending=False,base_sprite_references_applied=123,runtime_verified=False,ladder_runtime_deferred=True,runtime_summary=str((b/'runtime_summary.local.json').relative_to(ROOT)));put(b/'manifest.json',m)
back=b/'previous_pointers';back.mkdir()
for name in ('current_build.json','shibuki_current_build.json'):
 p=ROOT/'projects/ver_buki_riko'/name;shutil.copyfile(p,back/name);v=json.loads(p.read_text(encoding='utf-8'));v.update(kind='shibuki_low_hp_accepted',build=str(b.relative_to(ROOT)),cue=str((b/'shibuki_riko.cue').relative_to(ROOT)),bin_sha256=sha,session=session,session_closed=False,session_paused=None,session_pause_capture=None,runtime_summary=m['runtime_summary'],runtime_verified_frames=[],runtime_whole_opaque_matched_frames=[],both_directions_verified=False,new_animation_user_review_pending=False,low_hp_user_accepted=True,user_acceptance_quote=quote,low_hp_art_applied=True,ladder_runtime_deferred=True,ladder_user_review_pending=True,report='docs/SHIBUKI_LOW_HP.md',next_group='beam_in_ready',active_art_study='work/ver_buki_riko/shibuki_art/low_hp_v1',base_sprite_references_applied=123);put(p,v)
put(ROOT/'projects/ver_buki_riko/shibuki_low_hp_accepted_build.json',v)
put(ROOT/'projects/ver_buki_riko/shibuki_low_hp_art_revision.json',{'source':str(a.relative_to(ROOT)),'build':str(b.relative_to(ROOT)),'user_quote':quote,'style_user_accepted':True,'automated_cycle_verified':False})
p=ROOT/'projects/ver_buki_riko/shibuki_ladder_build.json';v=json.loads(p.read_text(encoding='utf-8'));v['user_acceptance_quote']=None;v['ladder_user_review_pending']=True;put(p,v)
report=f'''# Shibuki 체력 부족 대기

2026-10-27, `EXPANSION`, `ver_buki_riko/x_shibuki`. 체력 부족 대기6참조120..125를 추가했다. 사용자 **“{quote}”**로 수용되었다. 사다리14참조도 포함한 누적123참조이며 전체 기본 X 완성은 아니다.

- CUE `{(b/'shibuki_riko.cue').relative_to(ROOT)}`
- BIN `{sha}`
- ARC `{digest(b/'modified.arc')}`
- 부모 사다리 BIN `8d364ddaa12721b4ce383ef1e1b015a7f5d0fbdf1a722f1ea383126e1febf09e`
- 미국판 원본 `{checks['original_sha256']}`, Riko `{checks['riko_accepted_sha256']}` 재확인·보존.

## 확인된 구조와 제작

로컬 미국판 애니메이션6에120..125가 사용된다. 로컬 디컴파일 `player_common.c:1101`에서는 체력이 최대치의1/3 미만일 때6을 고른다. 정수 비교의 경계값을 임의로 변경하지 않았다.120/121,122/123,124/125는 각각 스트림을 공유한다. 일반 몸7파트와 추가 입 타일7을 분리하고 아머 타일8이상은 보존했다. 입 파츠는 원작에서 몸 파츠 사이에 끼어 있으므로 끝에 있다고 가정하지 않고 재조립 결과를 검사했다.

수용된 Shibuki 대기·원작 저체력 자세·설정화를 참고한 내장 imagegen 원화를 만들었다. 공통 축척0.085로 정규화했다. 최종은 첫 포즈를 기준으로 이미 수용된 대기의 `breathe` 변형을 재사용한다. 머리~골반~허벅지가 함께1픽셀씩 움직이고 무릎 아래에서 접지로 이어져 허리만 늘어나지 않는다. 발바닥 행62 및 하단5행은6참조 모두 동일하다. 두 번째 생성 포즈의 입 색1픽셀을 대응 얼굴 위치에 사용해 입을 여는 변화를 별도 타일로 넣었다. 얼굴 전체를 매번 다른 생성 그림으로 바꾸지 않는다.

`low_hp_v1/production02`의 인덱스 이미지·팔레트·레이아웃·패킹·몸 기준점과 `source_manifest02.json`에 원화/도구 해시를 보존했다. 원작 애니메이션16스텝 순서와 유지 시간을 그대로 쓴다.

## 검사와 실행 범위

165개 단위 검사, 잘못된 팔레트·누락 프레임·오래된 패킹 해시·아머 쓰기 거부4건 통과. ARC 반복 생성 동일. 전체251793섹터 비교에서1238/1239/1240/1389의4섹터만 변경되었다. 원래3개 압축 슬롯에1216/1234/1232바이트로 들어간다. 기존117참조·팔레트·아머·EXE·리소스 위치·판정·타이밍을 보존했다. 모든6참조는 최종 PNG와 조립 결과가 동일하다.

이전 피격 세션PID47036은 정상 종료했고 최신 빌드를PID46676, 세션 `{session}`로 실행했다. 인트로 화면 캡처가 있으며 사용자는 체력 부족 모션을 수용했다. **미실행:** 최신 저체력6참조의 좌우 RAM/VRAM/화면 전수 자동 대조. 사용자 수용과 자동 검증을 구분한다. 저장 상태 F1/F3와 메모리 쓰기는 사용하지 않았다. 사다리의 실제 플레이 확인은 사용자 지시에 따라 계속 보류한다.

[1배율](../{(b/'final_review_1x.png').relative_to(ROOT).as_posix()}), [3배율](../{(b/'final_review_3x.png').relative_to(ROOT).as_posix()}), [호흡 합성 미리보기](../{(b/'breathing_preview.gif').relative_to(ROOT).as_posix()}). GIF는 기술 미리보기이며 게임 실행 증거가 아니다. 실행 범위는 `runtime_summary.local.json`, 정적 검사는 `static_checks.local.json`에 기록했다.

다음은 출현·준비 자세(애니메이션1/2의126..142)다. 해당 원작 참조 목록은 확인했으나 신규 미술·재삽입은 아직 하지 않았다. 이후 귀환/승리·특수 피격 등 기본형 잔여 동작도 별도로 확인한다. 아머 제작은 아직 착수하지 않았다.
''';(ROOT/'docs/SHIBUKI_LOW_HP.md').write_text(report,encoding='utf-8')
def prepend(name,txt):
 p=ROOT/'docs'/name;s=p.read_text(encoding='utf-8');i=s.index('\n');p.write_text(s[:i+1]+'\n'+txt+'\n'+s[i+1:],encoding='utf-8')
prepend('STATUS.md','**2026-10-27 최신 — 체력 부족 대기 수용, 누적123참조.** 단계 `EXPANSION`, 활성 `ver_buki_riko/x_shibuki`, PS1 미국판. 현재 `shibuki_low_hp_20261026T151338348062Z`, BIN `843bd4ae…`. 저체력120..125의6참조를 추가했고 사용자 “좋아 체력부족 모션도 충분해”로 수용. 165검사·부정입력4·반복ARC 동일·전체251793섹터 비교 통과, 변경4섹터. 기존117참조·원본·Riko·아머·EXE 보존. 세션 `20261026T151425524412Z`, PID46676 한 창으로 최신 빌드 실행. 저체력 전수 자동 대조는 미실행이며 사용자 수용과 구분한다. **사다리14참조의 플레이/미술 확인은 사용자 요청으로 보류.** 다음 제작은 출현·준비126..142이며 원작 목록만 확인, 미술은 미착수. 기술 차단/추가 승인 요구 없음. [결과·해시·검증 범위](SHIBUKI_LOW_HP.md). 아래는 이전 기록이다.')
prepend('DECISIONS.md','## 2026-10-27 — 체력 부족 대기 수용\n\n사용자 “좋아 체력부족 모션도 충분해”. `production02`, BIN `843bd4ae…`의 저체력6참조를 수용 기준으로 고정한다. 사다리 플레이 검증은 이전 지시에 따라 보류하며 저체력 수용으로 대신하지 않는다. 다음 기본형 작업은 출현·준비 자세다.')
for name,txt in [('TEST_RESULTS.md','저체력6참조: 단위165·거부4·ARC 반복 동일·전체디스크 비교 통과,4섹터 변경. 사용자 모션 수용. 자동 전수 화면 대조 미실행.'),('SHIBUKI_SPRITES.md','저체력6참조 사용자 수용, 누적123참조. 사다리14참조는 적용했으나 사용자 후속 플레이 확인 대기.'),('ART_DIRECTION.md','저체력은 같은 몸의 머리~골반~허벅지가 함께 호흡하고 발을 고정한다. 입은 생성 원화에서 얻은 작은 패치만 교체한다. 사용자가 현재 모션을 수용했다.'),('VERSION_COMPARISON.md','미국판 PS1 저체력6참조를 원래3슬롯에 삽입. 몸과 입 오버레이·아머를 분리했으며 사용자 수용. 좌우 전수 자동 실행 검증은 미실행이다.')]:prepend(name,'**2026-10-27:** '+txt+' [근거](SHIBUKI_LOW_HP.md).')
with (ROOT/'docs/COMMANDS.md').open('a',encoding='utf-8') as f:f.write('''\n\n## 2026-10-27 Shibuki 저체력 (실행 완료)\n\n```powershell
python scripts/prepare_shibuki_low_hp_plan.py
python scripts/prepare_shibuki_low_hp.py --art work/ver_buki_riko/shibuki_art/low_hp_v1/production02 --parent out/ver_buki_riko/shibuki_ladder_20261026T150541813461Z
python scripts/build_shibuki_run.py --recipe work/ver_buki_riko/shibuki_low_hp/20261026T151307075002Z/recipe.json
python scripts/emulator_session.py launch --cue out/ver_buki_riko/shibuki_low_hp_20261026T151338348062Z/shibuki_riko.cue
```
''')
print(json.dumps({'accepted':True,'build':str(b),'next':'beam_in_ready','ladder_runtime_deferred':True}))
