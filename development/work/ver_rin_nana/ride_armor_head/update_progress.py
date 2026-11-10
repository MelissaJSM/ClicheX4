import json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=root/'projects/ver_rin_nana/project.json';m=json.loads(p.read_text('utf-8'));ptr=json.loads((root/'projects/ver_rin_nana/current_build.json').read_text('utf-8'))
m['latest_integrated_build']=ptr['build'];m['active_substage']='RIDE_CHASER_PRODUCTION';m['latest_sprite_collection']='out/ver_rin_nana/sprite_review_20261029T003406253128Z'
m['ride_armor_head_acceptance']={'bin_sha256':ptr['sha256'],'date':'2026-10-29','quote':'오케이 라이드아머 이상없어','status':'user_tested_accepted','visible_refs':19,'preserved_blank':[80],'runtime_automatic_complete':False}
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf-8')
status='''# 프로젝트 상태

2026-10-29. `EXPANSION`, 활성 `ver_rin_nana/zero_rin`. 뇌신격·질풍아 및 라이드 아머 머리 사용자 수용. 다음은 체이서 탑승 자세다.

## 현재 적용본

- [CUE](../out/ver_rin_nana/rin_ride_heads_20261029T003329979054Z/rin_nana.cue), BIN SHA-256 `4514b643d8202b62bc34f2c358c8dda315a87cec450b93e8324294fea4f8b3fe`.
- 기존 몸체266+탑승 머리19=285참조, 낙봉파 별도 잔상2개. 머리80은 원래 빈 타일로 보존한다. 전체 완료 수가 아니다.
- 전송 빛13·사망 구체9·24스테이지 대시 잔상72팔레트 행의 린 청백색 유지.
- [최신 스프라이트 모음](../out/ver_rin_nana/sprite_review_20261029T003406253128Z/index.html), [작업 포인터](../projects/ver_rin_nana/current_build.json).

## 사용자 수용과 검사

217참조 가는 윤곽 질감, 용염인 포함225참조, 낙봉파 X 수정, 뇌신격·질풍아 수정 순서로 사용자 수용했다. [각 승인·변경 범위·해시](RIN_SPECIALS_AND_EFFECTS.md).

탑승 머리는 사용자가 직접 찾아가 검사한 뒤 “오케이 라이드아머 이상없어”로 수용했다. 전체444참조 대조에서19개만 새 머리로 변경되고 다른425개 표시 및 파츠 좌표·팔레트·정적 효과는 보존된다. 부모 대비33변경섹터 EDC/ECC·251793전체섹터·반복 ARC/재추출 동일, 보호18파일 해시 동일. 사용자 검사를 자동 전수 실행 검사로 확대하지 않는다. [상세](RIN_RIDE_PRODUCTION.md).

앞선 특수기술 관련35개 단위 검사 통과. Python3.10의 외부 `tests` 패키지 충돌은 로컬 패키지를 지정하여 재실행했다. 수용 특수기술판의 [대기147 RAM/VRAM/1026픽셀 일치](../work/ver_rin_nana/live_poc/20261029T003459638537Z/verification.local.json). 탑승판은 새 CUE로 부팅했고 현재 세션은 `work/ver_rin_nana/emulator_sessions/20261029T003502709151Z`다.

## 다음 작업과 미확인

체이서14..41의28참조 제작.42..49의8참조는 단일 타일 스트림과 다중 파츠의 연결·별도 로딩을 확인해야 한다. 탈것 기체는 원작 유지. 전체 린 그래픽 완료로 보고하지 않는다.

선택·저장 화면, 초상화·헌터베이스·이름·심볼·UI 개인 색상, 한글·ClichéX4 로고 통합 및 Nana 제작은 후속이다. 현재는 순정 미국판 기반 린 시험판이며 블랙 팔레트·두 번째 모드 풀네임·음성 정책은 미확정이다. 오래된 F3는 이전 그래픽을 복원하므로 새 빌드는 새 부팅/메모리카드로 검사한다.

## 보호 기준

PS1 미국판 `SLUS_005.61`, 원본 `MegaMan X4.bin` SHA-256 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`. 원본·설정화는 입력 전용이다.

첫 모드 [보관 완성본](../completed/ver_buki_riko/v1.0.0/) SHA-256 `8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a`. [완료 범위](FINAL_RELEASE.md), [시행착오](PRODUCTION_LESSONS.md), [제작 지침](NEXT_VARIANT_PLAYBOOK.md).
'''
(root/'docs/STATUS.md').write_text(status,'utf-8')
for name,note in {
 'DECISIONS.md':'## 2026-10-29 — 라이드 아머 사용자 수용\n\n사용자가 검사를 맡은 뒤 “오케이 라이드아머 이상없어”로 `4514b643…` 탑승 머리19참조를 수용했다. 빈80은 보존하며 자동 전수 검증과 구별한다. 다음은 체이서다. [상세](RIN_RIDE_PRODUCTION.md).',
 'COMMANDS.md':'**2026-10-29 탑승 후속:** [라이드 아머 머리 제작의 실제 명령과 결과](RIN_RIDE_PRODUCTION.md).',
 'TEST_RESULTS.md':'**2026-10-29 탑승 머리:** `4514b643…`, 전체444참조·새19/보존425·부모 대비33변경섹터 검사·전체251793섹터·반복/재추출 동일·원작 좌표 및 빈80 보존. 사용자 직접 검사 후 수용. [근거](RIN_RIDE_PRODUCTION.md).',
 'RIN_PRODUCTION.md':'**최신 후속:** 몸체266+탑승 머리19=285참조 적용 및 사용자 수용. 빈80 보존, 다음은 체이서. [현재판·근거](RIN_RIDE_PRODUCTION.md).'
}.items():
 f=root/'docs'/name;text=f.read_text('utf-8');head,rest=text.split('\n',1);f.write_text(head+'\n\n'+note+'\n'+rest,'utf-8')
print('Updated vehicle status and acceptance records')
