from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix='''**2026-11-08 / EXPANSION — 네 캐릭터 모든 의상의 대기 기준 세부 묘사 통일 작업 진행 중. 전체 미완료.** 사용자의 진행도 질문은 중단 지시가 아니다. 리코·시부키·나나·린의 일반/블랙, 기본/포스/Ultimate 전후, 등장·승리·귀환·UI 사본을 범위에 유지한다.

최신 검증 통합 시험본은 [BR23](../out/ver_buki_riko/sprite_style_unification_20261107_v23/shibuki_riko.cue) / [RN36](../out/ver_rin_nana/sprite_style_unification_20261107_v36/rin_nana.cue)다. BIN SHA-256은 BR `cba70c5fee260a7e0d0e7751be9e8583ef2050696a3700add9cf06f6679b0724`, RN `3715c4f50c0adcceeeed435f3e59bdccc51c5bf79b4f7fa8fdb961b88fd1a3ea`. 전251,793섹터·EDC/ECC·재추출·EXE 보존·원MIPS/GPU 검사 통과. 활성 배포 포인터·v1.0.0 출시본·사용자 F1/카드와 원본 미국판 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`는 보존한다.

[전체 모음집 v28](../out/sprite_style_unification_20261107/review_v28/ALL_SPRITES_CURRENT.html)은 두 시험본의28폼·4,510표시를 묶었고 변경2,699(리코491/시부키757/나나811/린640)의 픽셀·4재생루프 검사를 통과했다. 약59.8%는 중복 의상·색상·UI 포함 변경 표시 비율이며 고유 원화나 품질 완료율이 아니다. 이미 세부가 충분해 보존한 자세·순수 효과도 있어 모든 표시를 수정해야 완료되는 분모가 아니다.

**이번에 반영한 작업**

- BR23: 시부키 기본/포스 사격85..92의40층. 새 그림을 줄이지 않고 기존9스트림18참조의 타일 순서를 역변환 가능한 방식으로 재정렬해 공간을 확보했다. 비대상 모션·전체 타일 픽셀·832부분조건·원 디렉터리508참조·재현3/거부15와 [직접 검토135](../work/sprite_style_unification_20261107/root_review_checkpoint135.json) 통과. [동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_standing_fire_base01/FROZEN.json). 선택1..8사본은 이 BIN에서 아직 이전 그림이다.
- RN35: 나나 기본/포스 라이드 체이서162..174, Ultimate특수95/96/98/99, 선택화면18..21 승리/귀환 사본. 차량은4고유자세의새8셀과 원래9개 Y이동 관계를 사용했다. 조립은행5 용량을40B 늘릴 때 은행6의 **미참조 비영 바이트를 포함한40B**를 사용했으며, 은행6의237조립·원실행 로더/렌더러를 검증했다. 단순한0패딩이었다고 하지 않는다. [검토132](../work/sprite_style_unification_20261107/root_review_checkpoint132.json), [133](../work/sprite_style_unification_20261107/root_review_checkpoint133.json), [134](../work/sprite_style_unification_20261107/root_review_checkpoint134.json). RN 선택19/20은 반전Y0이며 BR의Y+1을 적용하지 않는다.
- RN36: 나나 기본/포스 사격85/86 네셀·10층과 Ultimate차량13·65층. 사격에서 정본 사랑이20셀은85에20개,86에19개+새 피부손1셀 가림으로 보인다. 새 머리는 기존 조립기록6개를 재사용했으나 그림은 새 원화다. [사격 동결](../work/sprite_style_unification_20261107/root_nana_shot85/packed_shot01/FROZEN.json), [차량 동결](../work/sprite_style_unification_20261107/nana_audit/ultimate_vehicle_repaint/packed_vehicle_candidate_v1/FROZEN.json), [검토136](../work/sprite_style_unification_20261107/root_review_checkpoint136.json)·[137](../work/sprite_style_unification_20261107/root_review_checkpoint137.json). 비대상7296RGBA·독립 독자·원MIPS/GPU·원표 재생 검사를 통과했다. 실기 발동은 별도다.

**실제 게임 검증:** RN35를 새로 부팅해 선택 확정→손을 든 자세→귀환 윤곽→빛 상승→로딩 전환을128창으로 기록하고3판을 직접 봤다. 확정된 추가 절단/큰 크기 도약은 찾지 못했다. 조립 항목0xa는 RAM 전체 일치지만 그래픽0x10102 전체 일치는 찾지 못했고, 실행 참조별 GPU검증은 하지 않았다. [실제 캡처와 한계](../work/sprite_style_unification_20261107/runtime/rn35_selection_summary.json). 메모리쓰기/F1/F3 없이 종료했고 [보호42](../work/sprite_style_unification_20261107/protection_checkpoint42.json)의80파일·카드5쌍 불변이다.

이전 RN30 등장7의 RAM/GPU 실기, RN28의90/91·138/139 양방향 포스 실기, RN26의88/89·95/96·97/98/99 실기 근거도 보존한다. RN30의 등장126..139는 실제 표시마스크0이고140부터15였다. 따라서 새 등장7의 포스 표시는 정적검증이며 실기 완료로 확대하지 않는다. Animated WebP가 동일창을 합치는 점을 반영하여 캡처번호를 시간으로 대응한다. 옛RN12/RN9의 교정16판은 최신 그림 실기로 계산하지 않는다.

**진행 중/다음 작업:** 나나 기본87/92 연결 자세의 새4셀은 고정 크기로 등록했고, 부분 아머에서 떨어진 베일1셀의 소유층을 바로잡았다. 패킹 이후 독립/원MIPS 검토를 이어간다. 시부키 선택1..8은 후보47e5bd…와 원점 관계를 검토 중이며 범위확장 빌더v4는 아직 시험 전이다. 시부키 Ultimate사격, 나나 Ultimate호버/노바의 손·무기·추진발, 선택사본과 실기 검증을 계속 진행한다. 리코·린의 일반/블랙/UI와 끝점 검토 근거도 범위장부에 유지하며 현재 추가 확정 재작화 후보는 없다.

시부키 after135 팔과 나나 Ultimate 사다리149/151/153 보정은 이미지 도구 자동 안전검토 거부로 미완료이며 우회하지 않는다. 관련 사다리7참조는 이전 그림 보존. 나나 저체력120..125 실제 발동도 이전 실패로 미검증이다. 전체 미술·전수 실기·최종 사용자 수용 완료를 주장하지 않는다.

'''
for name,marker in [('STATUS.md','아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'),('SPRITE_STYLE_UNIFICATION_20261107.md','아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.')]:
 p=ROOT/'docs'/name;old=p.read_text('utf8');assert marker in old;p.write_text(old.split('\n',1)[0]+'\n\n'+prefix+old[old.index(marker):],'utf8')
print('BR23/RN36, verified album28, protection42, continued full scope')
