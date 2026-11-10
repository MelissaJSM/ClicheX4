import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
b=ROOT/'out/ver_rin_nana/nana_wall_20261029T224356693137Z'
sha='6385e1e5ae99e57601a1e8af784a9e22cb509a2cb07542d2b2b00785bc0ef2ab'
assert digest(b/'rin_nana.bin')==sha
quote='벽타기 내가 테스트해봤어 잘되네 다음으로 넘어가도 좋아'
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
runtime={'build_sha256':sha,'user_test_accepted':True,'user_quote':quote,'date':'2026-10-30','automated_wall_frame_audit_complete':False,'session':'work/ver_rin_nana/emulator_sessions/20261029T224416162956Z','limitations':'사용자 직접 벽타기 테스트 수용. 자동 12참조/좌우 전수 대조와 동일 빌드 F1/F3는 미실행.'}
write(b/'runtime_summary.local.json',runtime)
for name in ('manifest.json',):
 p=b/name;m=json.loads(p.read_text('utf8'));m.update(new_animation_user_accepted=True,user_acceptance_quote=quote,cumulative_base_references=94,runtime_summary=(b/'runtime_summary.local.json').relative_to(ROOT).as_posix());write(p,m)
p=ROOT/'projects/ver_rin_nana/current_build.json';m=json.loads(p.read_text('utf8'));assert m['sha256']==sha;m.update(user_test_accepted=True,user_quote=quote,cumulative_base_references=94,report='docs/NANA_WALL.md');write(p,m)
p=ROOT/'projects/ver_rin_nana/project.json';m=json.loads(p.read_text('utf8'));m.update(active_substage='NANA_HURT_PRODUCTION',latest_integrated_build=b.relative_to(ROOT).as_posix());m['nana_wall']={**runtime,'build':b.relative_to(ROOT).as_posix(),'frames':list(range(55,67)),'cumulative_base_references':94};write(p,m)
shutil.copyfile(Path(__file__).parent/'alignment_checks.json',b/'alignment_checks.json')
shutil.copyfile(ROOT/'work/ver_rin_nana/nana_wall/rejection_checks_v1/results.json',b/'rejection_checks.json')
(ROOT/'docs/NANA_WALL.md').write_text('''# 나나 벽 동작

2026-10-30. 벽 붙잡기·벽 점프·미끄러짐과 사격12참조(55..66)를 추가했다. 사용자 “'''+quote+'''”로 실제 벽타기 테스트 수용. 자동 좌우12참조 전수 검사와 새F1/F3는 미실행으로 구분한다. 다음은 기본형 피격 제작이다.

- 적용 [CUE](../out/ver_rin_nana/nana_wall_20261029T224356693137Z/rin_nana.cue)
- BIN SHA-256 `'''+sha+'''`
- PL00 ARC `61b637edc90138fc1b7b0c9cbe282470862d15e5f5c2d45ed40e850db40883e5`
- 기존82참조 보존, 기본형 누적94참조. 애니메이션13/14/15와125/126/127; 공중 연결39/40 보존.

수용 대기·공중 도트와 같은 팔레트/공통 축척으로 제작하고 원작 손 접점에 등록했다. 초기 몸은 총을 든 팔이 길어 보여 폐기하고 벽 쪽으로 손·발을 짚은 몸을 다시 제작했다. 최종 `contact_generated.png` → `normalized02` → `paired03`. 같은 자세의 일반/사격 얼굴·하체·뒷손 픽셀 보존을6쌍 검사했다. 시점에 따른 키43..48픽셀은 자세 차이이며 프레임별 확대/축소는 하지 않았다.

6개 원래 압축 공간에 삽입. 508압축 참조·다른 조립/아머 타일 보존, 독립2회 ARC 재제작 동일, 전체251793섹터 비교와 변경6섹터 EDC/ECC·보호20파일 검사 통과. 관련27단위 검사·잘못된 입력5건 거부·정렬6쌍 통과. 린·공통 한글/로고·사랑이 메뉴 아이콘·실제 탄환·판정·시간표 보존.

원본 미국판 SHA `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`. 현재 세션 `20261029T224416162956Z`, 변경 전 상태/카드는 `work/ver_rin_nana/checkpoints/before_nana_wall_20261030`에 백업했다. 새 부팅 후 시연 화면 관찰은 벽 자동 검사 근거가 아니며 실제 수용의 출처는 사용자 직접 테스트다.

[검사](../out/ver_rin_nana/nana_wall_20261029T224356693137Z/verification.json), [사용자 수용](../out/ver_rin_nana/nana_wall_20261029T224356693137Z/runtime_summary.local.json), [비교 시트](../out/ver_rin_nana/nana_wall_20261029T224356693137Z/art/family_3x.png).
''','utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 벽타기 사용자 수용\n\n사용자 “'+quote+'”. 적용 `6385e1e5…`의 벽타기를 사용자 테스트 완료로 기록하고 피격 제작으로 진행한다. 자동 좌우 전수 검사로 확대하지 않는다. [근거](NANA_WALL.md).\n\n'+p.read_text('utf8'),'utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8');start=s.index('\n\n')+2;end=s.index('\n\n## 현재 적용본');s=s[:start]+'2026-10-30. `EXPANSION`, 활성 `ver_rin_nana/x_nana`. 벽 동작12참조 사용자 테스트 수용, 기본형 누적94참조. 다음 피격 제작 진행. 린·공통 한글/로고·사랑이 권총 아이콘 유지. 풀네임 **아오쿠모 린 / 하나코 나나**. [벽 제작·수용](NANA_WALL.md), [기존 대시](NANA_DASH.md).'+s[end:];s=s.replace('- [CUE](../out/ver_rin_nana/nana_dash_20261029T072609070724Z/rin_nana.cue), BIN SHA-256 `3d0ca518ba91895215069ac4c54867574c7c5b66bc99f0d719078d178c24e6d9`.','- [CUE](../out/ver_rin_nana/nana_wall_20261029T224356693137Z/rin_nana.cue), BIN SHA-256 `'+sha+'`.\n- 벽12참조·6스트림 추가: 독립 ARC 재제작, 508참조 비교, 전체251793섹터/변경6섹터 EDC/ECC·보호20파일·27단위/5거부/6정렬쌍 검사 통과. 사용자 실기 수용, 자동 전수 미실행. [상세](NANA_WALL.md).');p.write_text(s,'utf8')
print('Wall acceptance recorded; current build preserved')
