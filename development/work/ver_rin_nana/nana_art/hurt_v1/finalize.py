import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from scripts.project import digest
from scripts.prepare_nana_idle_shot import write
d=Path(__file__).parent;b=ROOT/'out/ver_rin_nana/nana_hurt_20261029T225358832150Z';sha='ad17b9c369636a1aab2695be00b1e4f304b405e6b296741ad6db9418de2e0dd5'
assert digest(b/'rin_nana.bin')==sha
assert digest(b/'modified.arc')=='07de2caae1880e52d50e18ac2d01b51484441de67166aea66a00130a7e86ae2d'
board=Image.new('RGB',(5*96,2*96),'#222630');draw=ImageDraw.Draw(board)
for i,n in enumerate([0]+list(range(106,115))):
 p=ROOT/'out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z/art/frame_000.png' if n==0 else b/'art'/f'frame_{n:03d}.png';im=Image.open(p).convert('RGBA');x=i%5*96;y=i//5*96;board.paste(im,(x,y+16),im);draw.text((x+4,y+2),'idle' if n==0 else str(n),fill='white')
board.save(b/'final_review_1x.png');board.resize((1440,576),Image.Resampling.NEAREST).save(b/'final_review_3x.png')
files=[d/'generated.png',d/'prompt.txt',d/'plan.json',d/'production02/art.json',d/'production02/layout.json',d/'production02/packing.json']+[ROOT/'scripts'/n for n in ('normalize_nana_hurt.py','optimize_hurt_art.py','prepare_shibuki_hurt.py','prepare_shibuki_hurt_plan.py','build_nana_run.py','prepare_nana_checkpoint.py','capture_shibuki_hurt.py')]
write(b/'source_manifest.json',{'method':'builtin_imagegen_then_indexed_conversion','files':{p.relative_to(ROOT).as_posix():digest(p)for p in files},'native_body_sizes':[{'frame':106,'size':[26,41]},{'frame':110,'size':[29,38]}],'common_scale':.06155950752393981,'per_frame_scale':False})
for name in ('negative_checks.json','checkpoint_checks.json'):shutil.copyfile(d/name,b/name)
checks=json.loads((b/'verification.json').read_text('utf8'));checks.update(unit_tests=27,art_and_build_rejection_checks=11,checkpoint_rejection_checks=6,checkpoint_reproduced=True,existing_base_references_preserved=94,cumulative_base_references=103);write(b/'static_checks.local.json',checks)
evidence=ROOT/'work/ver_rin_nana/nana_hurt_runtime/20261029T225752180377Z/verification.local.json';r=json.loads(evidence.read_text('utf8'));data_frames=[int(n)for n,v in r['frames'].items()if any(s['ram_equal']and s['vram_equal']for s in v['samples'])];assert data_frames==[106,107,108,109]
runtime={'build_sha256':sha,'session':'work/ver_rin_nana/emulator_sessions/20261029T225516187437Z','pid':21948,'launch_and_refreshed_checkpoint_loaded':True,'checkpoint':'work/ver_rin_nana/checkpoints/nana_hurt_preview_20261030/refresh.json','evidence_kind':'graphics-refreshed checkpoint; not fresh disc loading proof','baseline':'work/ver_rin_nana/live_poc/20261029T225642955977Z/verification.local.json','unchanged_air39_full_screen_equal':True,'hurt_evidence':evidence.relative_to(ROOT).as_posix(),'ram_vram_matched_frames':data_frames,'whole_screen_matched_hurt_frames':r['verified_frames'],'not_observed_hurt_frames':list(range(110,115)),'new_animation_user_accepted':False,'limitations':'일반 피격106..109 RAM/VRAM 일치. 현재 물 전경이 겹치는 위치에서 화면 전체 일치 없음. 공중/화염110..114 실기 미검증, 특수 피격233..236 미제작. 강제 상태/체력/판정/프로그램 변경 없음.'};write(b/'runtime_summary.local.json',runtime)
p=b/'manifest.json';m=json.loads(p.read_text('utf8'));m.update(cumulative_base_references=103,runtime_summary=(b/'runtime_summary.local.json').relative_to(ROOT).as_posix(),new_animation_user_accepted=False,runtime_verified=False);write(p,m)
p=ROOT/'projects/ver_rin_nana/current_build.json';m=json.loads(p.read_text('utf8'));assert m['sha256']==sha;m.update(cumulative_base_references=103,session=runtime['session'],runtime_summary=(b/'runtime_summary.local.json').relative_to(ROOT).as_posix(),runtime_verified_frames=data_frames,runtime_full_screen_hurt_verified=False,report='docs/NANA_HURT.md',next_group='ladder_actions');write(p,m)
p=ROOT/'projects/ver_rin_nana/project.json';m=json.loads(p.read_text('utf8'));m.update(active_substage='NANA_HURT_APPLIED_PARTIAL_RUNTIME',latest_integrated_build=b.relative_to(ROOT).as_posix());m['nana_hurt']={'build':b.relative_to(ROOT).as_posix(),'status':'applied_partial_runtime','frames':list(range(106,115)),'cumulative_base_references':103,'user_art_accepted':False,'runtime_evidence':(b/'runtime_summary.local.json').relative_to(ROOT).as_posix()};m['integration_policy']['current_test_scope']='수용한 린·공통 한글/이름/로고/강지 및 나나 기본형103참조·사랑이 메뉴 아이콘. 나나 나머지 모션·아머는 미제작.';write(p,m)
report='''# 나나 피격 모션

2026-10-30. `EXPANSION`, `ver_rin_nana/x_nana`. 벽타기 사용자 수용 후 일반 피격·공중 반동·감전/화염 몸9참조(106..114)를 추가하여 기본형 누적103참조다. **새 피격 미술은 사용자 수용 전**이다.

- 적용 [CUE](../out/ver_rin_nana/nana_hurt_20261029T225358832150Z/rin_nana.cue)
- BIN SHA-256 `'''+sha+'''`
- PL00 ARC SHA-256 `07de2caae1880e52d50e18ac2d01b51484441de67166aea66a00130a7e86ae2d`
- 부모 벽판 `6385e1e5ae99e57601a1e8af784a9e22cb509a2cb07542d2b2b00785bc0ef2ab`, 수용 기준안 `nana_pilot_v9` 유지.

## 제작과 보존

원작 피격과 수용 나나 대기·공중을 참고하여 내장 imagegen으로 대기 축척 기준/일반 반동/공중 반동의 한 시트를 제작했다. 동일 축척0.0615595와 가로 계수0.9로 정규화했다. 일반26×41, 굽힌 공중29×38픽셀로 자세 차이에 따른 높이를 유지했다. 몸통·다리를 완성된 한 그림에서 나누어 저장하고 프레임별 임의 확대/축소는 하지 않았다.

106/107/108의 공통 몸과110/111의 공통 몸을 교체하고 별도 전기선/불꽃 링 타일·조립은 그대로 유지했다.109는 새 몸 실루엣의 밝은 섬광이다. 원래 인덱스14가 나나 팔레트에서 녹색이라 초기 후보를 폐기하고 밝은13으로 수정했다.112..114의 화염 실루엣은 새 몸에 맞추고 외부 원작 불꽃과 전용 CLUT2를 계승했다. 실제 공격·사랑이 탄환·차지샷·모션 시간표·판정·프로그램은 변경하지 않았다.

기존94참조·린·공통 한글/로고/선택/저장·사랑이 메뉴 아이콘·아머 타일을 보존했다. 이 작업을 나나 모든 피격의 완료로 확대하지 않는다. **애니메이션35의233..236은 별도 미제작**이다.

## 확인된 검사

508압축 참조와 다른1778조립을 비교했다. 원래6개 압축 슬롯 안에 삽입하며 용량/재배치 변경 없음. 독립2회 ARC/9PNG/recipe 동일. 전체251793섹터 비교, 변경4섹터 EDC/ECC·ARC 재추출 동일·보호20파일 유지. 관련27단위 검사, 아트5/빌드6의 총11입력 거부 검사 통과. 체크포인트6거부/독립재생성 동일도 통과했다.

저장한 현재 진행의 그래픽 데이터3955바이트만 사본에서 갱신했다. 플레이어·게임 진행·프로그램·팔레트·VRAM의 다른 바이트는 그대로다. 새 BIN을 실행하고 이 F3를 불러왔으므로 **그래픽 갱신 저장 상태 검사이며 디스크 새 로딩 전수 검사와 구분**한다. 새 실행 세션은 `20261029T225516187437Z`다.

실제 보존 공중39는RAM/VRAM/전체606불투명 픽셀 일치. 자연 피격33에서106/107/108/109를 관찰하고4참조 모두RAM/VRAM 일치를 확인했다. 현재 위치의 물 전경이 겹쳐 전체 화면 비교는 일치하지 않았다.110..114 실제 발동과 좌우 전수 검사는 미완료다. 이 한계를 정적 아트 검사로 대신 완료 처리하지 않는다.

## 보관과 다음 작업

현재 진행 원본 F1 SHA `81a77dabea956a2e9833526a59022cd96d1d4810f2ed3057d5d792b3f03088a7`은 `work/ver_rin_nana/checkpoints/before_nana_hurt_20261030/current`에, 카드도 같은 백업 폴더에 보관했다. 이전 대시 F1 `e8ba2359…`는 `before_nana_wall_20261030/sstates`에도 보존된다. 적용 F3는 `nana_hurt_preview_20261030`의 `432ae93d…`이다. 예전 상태를 직접 덮어 불러오면 예전 그림이 다시 나타날 수 있다.

다음 기본형 제작은 사다리·사다리 사격이다. 개인 UI/일러스트/효과/음성과 아머는 별도 후속 범위다. 원본 미국판 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b` 및 첫 모드 완성본 `8f130c5e…` 보호 유지.

[1배율 시트](../out/ver_rin_nana/nana_hurt_20261029T225358832150Z/final_review_1x.png), [3배율 시트](../out/ver_rin_nana/nana_hurt_20261029T225358832150Z/final_review_3x.png), [정적 검사](../out/ver_rin_nana/nana_hurt_20261029T225358832150Z/static_checks.local.json), [실기 범위](../out/ver_rin_nana/nana_hurt_20261029T225358832150Z/runtime_summary.local.json), [제작 파일/도구 해시](../out/ver_rin_nana/nana_hurt_20261029T225358832150Z/source_manifest.json).
'''
(ROOT/'docs/NANA_HURT.md').write_text(report,'utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8');start=s.index('\n\n')+2;end=s.index('\n\n## 현재 적용본');s=s[:start]+'2026-10-30. `EXPANSION`, 활성 `ver_rin_nana/x_nana`. 벽타기 사용자 테스트 수용 후 피격9참조 추가, 기본형 누적103참조. 일반 피격4참조 RAM/VRAM 일치, 물 전경이 겹친 전체 화면 대조 및 공중/화염 실기는 미완료다. 다음 제작은 사다리·사다리 사격. 린·공통 자산 유지. [피격](NANA_HURT.md), [벽 수용](NANA_WALL.md).'+s[end:];s=s.replace('- [CUE](../out/ver_rin_nana/nana_wall_20261029T224356693137Z/rin_nana.cue), BIN SHA-256 `6385e1e5ae99e57601a1e8af784a9e22cb509a2cb07542d2b2b00785bc0ef2ab`.','- [CUE](../out/ver_rin_nana/nana_hurt_20261029T225358832150Z/rin_nana.cue), BIN SHA-256 `'+sha+'`.\n- 피격9참조·6스트림 추가. 기존94보존, 508참조/1778다른 조립 비교, 전체251793섹터/변경4섹터 EDC/ECC·보호20파일·27단위/11거부 검사 통과. 저장 상태 그래픽 갱신3955바이트만 변경, 6입력 거부/재생성 동일. 피격 사용자 미술 수용 전. [근거](NANA_HURT.md).');s=s.replace('나나 벽 동작 이후 모션과 사랑이 아이콘 이외','나나 사다리 이후 모션과 사랑이 아이콘 이외');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 피격 제작·적용\n\n벽타기 직접 테스트 후 다음으로 진행하라는 사용자 지시를 근거로 승인된 나나 기본형 피격9참조를 누적했다. 기존94참조와 원본 효과·판정·진행을 유지했다. 피격 수용을 미리 기록하지 않으며233..236은 별도 미제작이다. [실기·정적 구분](NANA_HURT.md).\n\n'+p.read_text('utf8'),'utf8')
with (ROOT/'docs/COMMANDS.md').open('a',encoding='utf8')as f:f.write('''\n\n## 2026-10-30 나나 벽 수용·피격 (실행 완료)

```powershell
python scripts/prepare_shibuki_hurt_plan.py --project ver_rin_nana
work/tools/voice_env/Scripts/python.exe scripts/normalize_nana_hurt.py --source work/ver_rin_nana/nana_art/hurt_v1/generated.png --output work/ver_rin_nana/nana_art/hurt_v1/production02
work/tools/voice_env/Scripts/python.exe scripts/optimize_hurt_art.py --art work/ver_rin_nana/nana_art/hurt_v1/production02 --parent out/ver_rin_nana/nana_wall_20261029T224356693137Z
python scripts/prepare_shibuki_hurt.py --project ver_rin_nana --art work/ver_rin_nana/nana_art/hurt_v1/production02 --parent out/ver_rin_nana/nana_wall_20261029T224356693137Z
python scripts/build_nana_run.py --scope hurt --candidate work/ver_rin_nana/nana_hurt/20261029T225320652984Z --reproduced work/ver_rin_nana/nana_hurt/20261029T225348337636Z
python -m unittest tests.test_psx_frame_edit tests.test_psx_compress tests.test_psx_player tests.test_psx_tile_layout tests.test_psx_paired_layout
python work/ver_rin_nana/nana_art/hurt_v1/checks.py
python work/ver_rin_nana/nana_art/hurt_v1/verify_checkpoint.py
python scripts/capture_shibuki_hurt.py --project ver_rin_nana --baseline work/ver_rin_nana/live_poc/20261029T225642955977Z/verification.local.json --seconds 15
```

정규화/검사 출력 경로는 재실행 때 새 경로를 사용한다. 실기 명령은 당시 PID/빌드와 결속된 근거이므로 다른 세션에서 재사용하지 않는다. [결과·제한](NANA_HURT.md).
''')
print(json.dumps({'build':b.relative_to(ROOT).as_posix(),'sha256':sha,'cumulative':103,'runtime_data_frames':data_frames,'next':'ladder_actions'}))
