import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from scripts.prepare_nana_idle_shot import write
from scripts.project import digest
d=Path(__file__).parent;b=ROOT/'out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z';parent=ROOT/'out/ver_rin_nana/nana_hurt_20261029T225358832150Z';sha='8addc7ebcddc359b8fc828296d684f8909b771df7549bea40f3c8ea16d22adf2';assert digest(b/'rin_nana.bin')==sha
assert digest(b/'modified.arc')=='e0b488b1c099588125dd2f0bd964168bd3ebbf866aafba7310c43b265b241ba9'
paths=[d/'generated.png',d/'current_fall.png',d/'prompt.txt',d/'production02/body/art.json',d/'production02/pairs/pairs.json',d/'production02/pairs/packing.json']+[ROOT/'scripts'/n for n in ('prepare_nana_fall_legs.py','prepare_shibuki_run.py','solve_nana_run_cover.py','optimize_shibuki_pairs.py','build_nana_run.py','prepare_nana_checkpoint.py')];write(b/'source_manifest.json',{'method':'builtin_imagegen_leg_edit_then_indexed_mask_composite','files':{p.relative_to(ROOT).as_posix():digest(p)for p in paths},'outside_leg_masks_pixel_identical':True})
shutil.copyfile(d/'negative_checks.json',b/'negative_checks.json');shutil.copyfile(d/'production02/leg_checks.json',b/'leg_checks.json')
sequence=[39,41,43,45,47,49,51,53];frames=[]
for n in sequence:
 bg=Image.new('RGB',(768,352),'#222630');draw=ImageDraw.Draw(bg)
 for side in (0,1):
  p=b/'art'/f'frame_{n:03d}.png' if side==1 and n in (43,45,47)else ROOT/'out/ver_rin_nana/nana_air_20261029T070014731019Z/art'/f'frame_{n:03d}.png';im=Image.open(p).convert('RGBA').resize((384,320),Image.Resampling.NEAREST);bg.paste(im,(side*384,32),im);draw.text((side*384+12,8),('before' if side==0 else 'revised')+f' {n}',fill='white')
 frames.append(bg)
frames[0].save(b/'fall_transition_comparison.gif',save_all=True,append_images=frames[1:],duration=[150,67,67,67,350,50,50,150],loop=0,disposal=2)
# This slowed side-by-side display is for visual review, not native timing evidence.
ev=ROOT/'work/ver_rin_nana/nana_batch_runtime/20261029T231000974622Z/verification.local.json';report=json.loads(ev.read_text('utf8'));runtime={'build_sha256':sha,'session':'work/ver_rin_nana/emulator_sessions/20261029T230856562709Z','pid':50452,'evidence_kind':'graphics-refreshed checkpoint; not fresh disc loading proof','checkpoint':'work/ver_rin_nana/checkpoints/nana_fall_legs_preview_20261030/refresh.json','baseline':'work/ver_rin_nana/live_poc/20261029T230913720949Z/verification.local.json','batch':ev.relative_to(ROOT).as_posix(),'changed_ram_vram_frames':sorted(set(report['ram_vram_verified_frames'])&set(range(43,49))),'changed_whole_screen_frames':sorted(set(report['render_matched_frames'])&set(range(43,49))),'user_art_accepted':False,'limitations':'일반 하강43/45/47 실제 전체 화면 확인. 사격48 RAM/VRAM 확인,44/46 미관찰 및 사격3자세 전체 화면 비교 미완료. 좌우 전수 미검사. 준비된 저장 상태의 그래픽만 갱신하여 게임 진행/프로그램 보존.'};assert runtime['changed_whole_screen_frames']==[43,45,47];write(b/'runtime_summary.local.json',runtime)
static=json.loads((b/'verification.json').read_text('utf8'));static.update(unit_tests=27,rejection_checks=9,leg_mask_checks=6,cumulative_base_references=103,unchanged_existing_frames=97);write(b/'static_checks.local.json',static)
p=b/'manifest.json';m=json.loads(p.read_text('utf8'));m.update(cumulative_base_references=103,runtime_summary=(b/'runtime_summary.local.json').relative_to(ROOT).as_posix(),runtime_verified=False,new_animation_user_accepted=False);write(p,m)
p=ROOT/'projects/ver_rin_nana/current_build.json';m=json.loads(p.read_text('utf8'));assert m['sha256']==sha;m.update(cumulative_base_references=103,session=runtime['session'],runtime_summary=(b/'runtime_summary.local.json').relative_to(ROOT).as_posix(),runtime_whole_screen_verified_frames=[43,45,47],runtime_ram_vram_verified_frames=runtime['changed_ram_vram_frames'],report='docs/NANA_FALL_LEGS.md',next_group='ladder_actions');write(p,m)
p=ROOT/'projects/ver_rin_nana/project.json';m=json.loads(p.read_text('utf8'));m.update(active_substage='NANA_FALL_LEGS_APPLIED_USER_REVIEW',latest_integrated_build=b.relative_to(ROOT).as_posix());m['nana_fall_leg_revision']={'build':b.relative_to(ROOT).as_posix(),'frames':list(range(43,49)),'only_legs_changed':True,'user_accepted':False,'runtime':(b/'runtime_summary.local.json').relative_to(ROOT).as_posix()};write(p,m)
text='''# 나나 하강 다리 수정

2026-10-30. 사용자 “점프후 하강할때 다리가 너무 쫙펴져있어서 … 다리만 좀 수정” 요청을 반영했다. 하강 후반43/45/47과 사격44/46/48의 **다리 픽셀만** 바꾸었다. 다음 사다리 작업을 앞두고 진행한 수정이며 누적 기본형은103참조 그대로다.

- [적용 CUE](../out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z/rin_nana.cue)
- BIN SHA-256 `'''+sha+'''`
- PL00 ARC SHA-256 `e0b488b1c099588125dd2f0bd964168bd3ebbf866aafba7310c43b265b241ba9`
- 부모 피격판 `ad17b9c369636a1aab2695be00b1e4f304b405e6b296741ad6db9418de2e0dd5`

## 수정 내용

기존 하강 도트3장을 내장 imagegen 편집 입력으로 사용했다. 무릎을 앞쪽으로 굽히고 종아리·발을 뒤로 보내 하강을 유지할 때도 다리가 완전히 펴지지 않게 했다. 생성 결과 전체를 교체하지 않고 새 다리만 기존 팔레트로 변환해 합성했다. 치마 아래 원래 연결 행을 남기고 일반/사격에 같은 다리를 사용한다. 머리·상체·치마·팔·총·몸 기준점은 기존 픽셀과 동일하다. 상승·최초 하강41/42·착지와 나머지97참조는 그대로다. 물리 좌표·판정·속도·애니메이션 시간표는 변경하지 않았다.

편집 영역은 월드 캔버스96×80에서X37..63, Y는43/45의45이후 및47의47이후다. 범위 밖은 부모 ARC에서 복원한 실제 그림과 픽셀 동일성을 다시 검사했다. 일반/사격의 다리도 동일하다. 통합 전에6참조 모두 재조립 그림이 의도한 그림과 같은지 검사했다.

## 검사와 한계

원래3압축 슬롯에1214/1220/1286바이트로 삽입했다. 재배치·길이·아머 타일 변경 없음.508압축 참조 비교·독립2회 ARC/6PNG/recipe 동일·전체251793섹터 비교·변경4섹터 EDC/ECC·재추출 동일·보호20파일 유지. 관련27단위 검사 및 아트/빌드/저장 상태 거부9건 통과.

현재 진행을 백업하고 눈깜빡임115 상태의 그래픽3562바이트만 사본에서 갱신하여 새 BIN 실행 후F3로 불러왔다. 프로그램·플레이어·진행·팔레트·활성VRAM 보존. **그래픽 갱신 저장 상태 실기이며 디스크 새 로딩 전수 확인과 구분한다.** 원래 저장 SHA `ef14e74517c6ad387214081eb80bf3ab4531797593ffa92caab30d933149e4e1`, 갱신 저장 SHA `f8bbb195bd34d2ec0627420022ce127a5bff00bc4217d5071c00f876b947789d`. 백업은 `work/ver_rin_nana/checkpoints/before_nana_fall_legs_20261030`이다.

실기 일반 하강43/45/47의RAM/VRAM·전체 불투명 화면 픽셀 일치. 사격48은RAM/VRAM 일치,44/46은 이번 짧은 재생에서 관찰하지 못했고 사격 전체 화면·좌우 전수 검사는 미완료다. 자동 재생 첫 시도는 포커스 변경으로 중단되어 키를 모두 해제했고 완료 근거로 세지 않았다. 이후 성공한 관찰에 움직임/벽 동작도 포함되어 있으므로 단독 수직 점프 좌표 검사로 해석하지 않는다.

새 미술의 사용자 수용은 아직 없다. 사다리 제작은 다음 작업이며 이번 수정에 포함하지 않았다. 원본 게임·설정화·첫 모드 완성본은 변경하지 않았다.

[전후/사격 비교](../out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z/art/paired_4x.png), [전환 비교 GIF](../out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z/fall_transition_comparison.gif), [정적 검사](../out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z/static_checks.local.json), [실기 범위](../out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z/runtime_summary.local.json). GIF는 느린 비교용 합성이며 원래 타이밍이나 실제 게임 영상의 증거가 아니다.
''';(ROOT/'docs/NANA_FALL_LEGS.md').write_text(text,'utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8');start=s.index('\n\n')+2;end=s.index('\n\n## 현재 적용본');s=s[:start]+'2026-10-30. `EXPANSION`, 활성 `ver_rin_nana/x_nana`. 사용자 요청으로 하강 후반/사격6참조의 다리만 굽힌 자세로 수정했다. 일반 하강3참조 실제 전체 화면 일치, 사격48 데이터 확인, 사격44/46·좌우 전수 미완료. 누적103참조, 다른97자세 보존. 다음은 사다리 제작이며 현재 수정 미술 사용자 수용 전이다. [하강 다리 수정](NANA_FALL_LEGS.md), [피격](NANA_HURT.md), [벽 수용](NANA_WALL.md).'+s[end:];s=s.replace('- [CUE](../out/ver_rin_nana/nana_hurt_20261029T225358832150Z/rin_nana.cue), BIN SHA-256 `ad17b9c369636a1aab2695be00b1e4f304b405e6b296741ad6db9418de2e0dd5`.','- [CUE](../out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z/rin_nana.cue), BIN SHA-256 `'+sha+'`.\n- 하강 다리6참조 수정: 상체/총/좌표 보존, 508참조 비교·ARC 독립 재제작·전체251793섹터/변경4섹터 EDC/ECC·보호20파일·27단위/9거부 검사 통과. 저장 상태 그래픽만 갱신하여3일반 자세 전체 화면 일치. [범위](NANA_FALL_LEGS.md).');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 하강 다리만 수정\n\n사용자가 다음 작업 전에 하강 때 뻣뻣하게 펴지는 다리만 수정해 달라고 요청했다. 하강43..48의 다리만 변경하고 상체·총·등록 좌표·다른97참조 및 진행/시간표는 유지했다. 이번 지시를 피격 미술 수용으로 해석하지 않는다. [수정과 실기](NANA_FALL_LEGS.md).\n\n'+p.read_text('utf8'),'utf8')
p=ROOT/'docs/NANA_AIR.md';s=p.read_text('utf8');p.write_text(s.split('\n',1)[0]+'\n\n**2026-10-30 후속 수정:** 하강43..48의 다리만 굽힌 자세로 변경했다. 현재 적용본과 사용자 지적은 [하강 다리 수정](NANA_FALL_LEGS.md)을 따른다. 아래는 최초 제작 이력이다.\n'+s.split('\n',1)[1],'utf8')
with (ROOT/'docs/COMMANDS.md').open('a',encoding='utf8')as f:f.write('''\n\n## 2026-10-30 나나 하강 다리만 수정 (실행 완료)

```powershell
work/tools/voice_env/Scripts/python.exe scripts/prepare_nana_fall_legs.py --output work/ver_rin_nana/nana_art/fall_legs_v1/production02
work/tools/voice_env/Scripts/python.exe scripts/solve_nana_run_cover.py --scope fall_legs --pairs work/ver_rin_nana/nana_art/fall_legs_v1/production02/pairs --timeout 5
work/tools/voice_env/Scripts/python.exe scripts/optimize_shibuki_pairs.py --project ver_rin_nana --pairs work/ver_rin_nana/nana_art/fall_legs_v1/production02/pairs --layout work/ver_rin_nana/nana_art/fall_legs_v1/production02/pairs/layout.json --parent out/ver_rin_nana/nana_hurt_20261029T225358832150Z --plan work/ver_rin_nana/nana_art/fall_legs_v1/plan.json --fast-cost --steps 3500
python scripts/prepare_shibuki_run.py --project ver_rin_nana --scope fall_legs --art work/ver_rin_nana/nana_art/fall_legs_v1/production02/body --pairs work/ver_rin_nana/nana_art/fall_legs_v1/production02/pairs --layout work/ver_rin_nana/nana_art/fall_legs_v1/production02/pairs/layout.json --parent out/ver_rin_nana/nana_hurt_20261029T225358832150Z
python scripts/build_nana_run.py --scope fall_legs --candidate work/ver_rin_nana/nana_fall_legs/20261029T230719464749Z --reproduced work/ver_rin_nana/nana_fall_legs/20261029T230743487792Z
python work/ver_rin_nana/nana_art/fall_legs_v1/checks.py
```

이미 존재하는 출력 경로에는 다시 쓰지 않는다. [실제 검사와 한계](NANA_FALL_LEGS.md).
''')
print(json.dumps({'build':b.relative_to(ROOT).as_posix(),'sha256':sha,'only_legs_changed':True,'runtime_whole_screen':runtime['changed_whole_screen_frames']}))
