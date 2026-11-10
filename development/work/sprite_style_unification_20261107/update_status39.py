from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix='''**2026-11-08 / EXPANSION — 네 캐릭터 모든 의상의 대기 기준 세부 묘사 통일 작업 진행 중. 전체 미완료.** 진행도 질문은 중단 지시가 아니다. 리코·시부키·나나·린의 일반/블랙, 기본/포스/Ultimate 전후, 등장·승리·귀환·UI 사본을 범위에 유지한다.

최신 검증 통합 시험본은 [BR25](../out/ver_buki_riko/sprite_style_unification_20261107_v25/shibuki_riko.cue) / [RN39](../out/ver_rin_nana/sprite_style_unification_20261107_v39/rin_nana.cue)다. BIN SHA-256은 BR `21696e9bae002ef6c9f95fed683e7cd531fd6cdfc6c0fdae97529c3b28a09636`, RN `8eb84afaa7c201dfcaee8e5cbf4c2fef152d423b10b501e8238362f9b5cca5b2`. 각251,793섹터·EDC/ECC·재추출·EXE 보존·원MIPS/GPU 검사 통과. 활성 배포 포인터·v1.0.0 출시본·사용자 F1/카드와 원본 미국판 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`는 보존한다.

[전체 모음집 v30](../out/sprite_style_unification_20261107/review_v30/ALL_SPRITES_CURRENT.html)은 BR25/RN39의28폼·4,510표시 중2,757변경(리코491/시부키781/나나845/린640)을 수록했다. **약61.1%는 중복 의상·색상·UI 포함 변경 표시 비율이며 고유 원화나 품질 완료율이 아니다.** 2,757픽셀 비교와4재생루프 검사를 통과했다. [검사](../out/sprite_style_unification_20261107/review_v30/browser_checks.json).

**최근 반영한 작업과 근거**

- 시부키 기본/포스 사격85..92와 선택화면1..8에 이어 Ultimate85..92를 BR25에 통합했다. 새40층과 원래88의 별도 효과를 보존하고390입력·독립검사·원순서 재생·원코드 검사까지 결속했다. [Ultimate 동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_standing_fire_ultimate01/FROZEN.json), [직접 검토140](../work/sprite_style_unification_20261107/root_review_checkpoint140.json).
- 나나 기본/포스 사격85/86·87/92와 선택화면1..8을 동기화했다. UI는 실제 원점 X0/Y0·무반전을 유지하며 원코드/모든 소비자 조사 후 미참조14타일을 사용했다. 이것은 단순0패딩이 아니다. 나머지155타일·공유5타일·비대상72프레임은 동일하다. [선택 사본 동결](../work/sprite_style_unification_20261107/root_nana_selection8/prepared01/FROZEN.json), [직접 검토141](../work/sprite_style_unification_20261107/root_review_checkpoint141.json). 빌더v5는 RN8 원점과 기존BR8 회귀·7거부검사를 포함한다.
- 나나 Ultimate 호버10을 RN39에 통합했다. 새몸5·사격팔5를 대기 디테일에 맞추고 사랑이 총구를 원래 탄환 발생점에 정합했다. 원래 추진 불꽃15단계·탄환7·발접점·코드·동작시간은 보존한다. 원코드가221..230에서 아머마스크15를 강제하므로 도달 불가능한 마스크0 반쪽 미리보기를 실제 결함으로 취급하지 않는다. [동결](../work/sprite_style_unification_20261107/nana_audit/ultimate_hover_repaint/FROZEN.json), [직접 검토142](../work/sprite_style_unification_20261107/root_review_checkpoint142.json)·[143](../work/sprite_style_unification_20261107/root_review_checkpoint143.json).
- RN35/36의 기본/포스·Ultimate 차량13, 특수95/96/98/99, 선택18..21 승리/귀환은 유지한다. 선택19/20의 반전Y0와 기존 미참조40B 사용 검증도 보존한다.

**실제 게임 검증**

- BR25 새 부팅·복사 카드 DATA3로 획득 후 Ultimate 일반 사격·차지·반동·복귀를 양방향224캡처로 기록하고9판을 직접 열람했다. 추가 확정 절단·큰 크기 도약을 찾지 못했다. [근거와 한계](../work/sprite_style_unification_20261107/runtime/br25_shot_summary.json).
- RN39 선택 화면 자동 사격·복귀240캡처와4판, Ultimate 전진·후진·정지 호버 및 사격336캡처와14판을 직접 확인했다. 추가 확정 팔/총구·발/불꽃 분리나 큰 크기 도약을 찾지 못했다. [선택](../work/sprite_style_unification_20261107/runtime/rn39_selection_summary.json), [호버](../work/sprite_style_unification_20261107/runtime/rn39_hover_summary.json). 마지막 네 번째 점프는 이전 호버가 끝나지 않아 별도 새 발동으로 세지 않는다.
- RN37 포스 사격224캡처·9판 및 이전 실제 등장/특수기/양방향 검증도 보존한다. 위 최신 녹화는 약16Hz 창 캡처이며 참조별RAM/GPU 추적 및 모든60Hz·부분아머·획득 전 실기 완료를 뜻하지 않는다. WebP 합쳐진 프레임은 실제 캡처시간으로 검증 대응한다.

F1/F3·메모리쓰기 없이 시험 에뮬레이터를 종료했고 [보호47](../work/sprite_style_unification_20261107/protection_checkpoint47.json)의80파일·카드5쌍은 불변이다.

**진행 중/다음 작업**

시부키 기본/포스 차량13 후보 `3e11b7e6…`는 독립검사·508원참조 실행을 통과했으며 마지막 직접 미술검토/동결/통합은 진행 중이다. Ultimate 차량도 새 원화 정합 중이다. 나나 기본/포스 호버는 대기 기준 입력을 준비했고, Ultimate 노바는 새 디테일을 유지하면서215의 원래 올린 팔 자세를 국소 교정한다. 리코·린 일반/블랙/UI·끝점도 전체 범위에 유지하며 현재 추가 확정 재작화 후보는 없다.

**검증 기록 충돌과 복원:** 새87/92 독립검사에서 옛138/139 검사 폴더 이름을 재사용하여 예전 보고서/판독기가 덮인 것을 발견했다. 새 자료를 별도 보존하고 과거 세션 로그로 복원했으며 옛 보고서 `bc5269ec…`, 시각검토 `f6c67b22…`, 비교이미지는 기존 잠금 해시와 동일함을 확인했다. 옛 판독기 자체의 사전 해시는 없어 그 코드의 과거 바이트 동일성까지 주장하지 않는다. 원화/ARC/BIN/동결/사용자 파일은 변경되지 않았다. [복원 근거](../work/sprite_style_unification_20261107/zero_audit/settle138_139_recovery01/restoration.json). 새 검사는 고유한 `nana_base_settle87_92_independent01`로 분리하고31입력을 잠갔다.

시부키 after135 팔과 나나 Ultimate 사다리149/151/153 보정은 이미지 도구 자동 안전검토 거부로 미완료이며 우회하지 않는다. 관련 사다리7참조는 이전 그림 보존. 나나 저체력120..125 실제 발동도 이전 실패로 미검증이다. 전체 미술·전수 실기·최종 사용자 수용 완료를 주장하지 않는다.

'''
prefix=prefix.replace('nana_audit/ultimate_hover_repaint/FROZEN.json','nana_audit/ultimate_hover_repaint/packed_hover_candidate_v1/FROZEN.json')
for name,marker in [('STATUS.md','아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'),('SPRITE_STYLE_UNIFICATION_20261107.md','아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.')]:
 p=ROOT/'docs'/name;old=p.read_text('utf8');assert marker in old
 p.write_text(old.split('\n',1)[0]+'\n\n'+prefix+old[old.index(marker):],'utf8')
print('BR25/RN39 album30 actual hover/selection/shooting protection47 updated; all work remains active')
