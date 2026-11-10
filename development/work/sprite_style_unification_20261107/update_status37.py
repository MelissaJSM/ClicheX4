from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix='''**2026-11-08 / EXPANSION — 네 캐릭터 모든 의상의 대기 기준 세부 묘사 통일 작업 진행 중. 전체 미완료.** 진행도 질문은 중단 지시가 아니다. 리코·시부키·나나·린의 일반/블랙, 기본/포스/Ultimate 전후, 등장·승리·귀환·UI 사본을 범위에 유지한다.

최신 검증 통합 시험본은 [BR24](../out/ver_buki_riko/sprite_style_unification_20261107_v24/shibuki_riko.cue) / [RN37](../out/ver_rin_nana/sprite_style_unification_20261107_v37/rin_nana.cue)다. BIN SHA-256은 BR `45b5e019396f37aaa623e2c23bd4b91ceff344826ef95b6496c41e3d55b91644`, RN `8a7ee9c47d170c8869f5415e18dc23e920157e28e9d49d7762a7acebc416a01e`. 전251,793섹터·EDC/ECC·재추출·EXE 보존·원MIPS/GPU 검사 통과. 활성 배포 포인터·v1.0.0 출시본·사용자 F1/카드와 원본 미국판 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`는 보존한다.

마지막 검증된 [전체 모음집 v28](../out/sprite_style_unification_20261107/review_v28/ALL_SPRITES_CURRENT.html)은 BR23/RN36의28폼·4,510표시 중2,699변경(리코491/시부키757/나나811/린640)을 수록했다. 약59.8%는 중복 의상·색상·UI 포함 변경 표시 비율이며 고유 원화나 품질 완료율이 아니다. 현재 BR24/RN37 모음집 v29를 생성·검사 중이다. [범위장부10](../work/sprite_style_unification_20261107/zero_audit/full_scope_matrix10/COVERAGE.html)은 현재144분류칸·292근거와 앨범 시점 차이를 구분한다.

**최근 반영한 작업과 근거**

- 시부키 기본/포스 사격85..92의40층을 새로 정리했다. 타일 순서를 역변환 가능한 방식으로 재정렬해 공간을 확보했고, 비대상832부분조건·원 디렉터리·실행 검사를 통과했다. BR24에서는 선택화면1..8도 새 사격 그림으로 동기화했다. 실제 측정한 Y차(-1/0/0/0/0/-1/-2/0)를 보존했다. [기본 사격 동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_standing_fire_base01/FROZEN.json), [선택 사본 동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_selection_standing01/FROZEN.json), [직접 검토139](../work/sprite_style_unification_20261107/root_review_checkpoint139.json).
- 나나 기본/포스 사격85/86, 이어지는87/92의 새8셀·20층을 반영했다. 머리 조립기록은 기존 기록을 재사용하되 그림은 새 원화이며, 부분 아머에서 떨어지던 베일1셀의 소유층도 수정했다. 508원참조·비대상층·7,296RGBA·64부분조건과 원MIPS/GPU·원순서 재생 검사 통과. [85/86 동결](../work/sprite_style_unification_20261107/root_nana_shot85/packed_shot01/FROZEN.json), [87/92 동결](../work/sprite_style_unification_20261107/root_nana_shot87/packed_settle01/FROZEN.json), [직접 검토137](../work/sprite_style_unification_20261107/root_review_checkpoint137.json)·[138](../work/sprite_style_unification_20261107/root_review_checkpoint138.json).
- RN35/36의 나나 기본/포스·Ultimate 라이드 체이서13참조, Ultimate특수95/96/98/99, 선택화면18..21 승리/귀환도 유지한다. 차량 기본형 패킹은 은행6의 미참조 비영 바이트 포함40B를 사용했으며237조립과 원로더/렌더러를 별도 검증했다. 이를 단순0패딩으로 표현하지 않는다. RN 선택19/20은 반전Y0이며 BR의Y+1을 적용하지 않는다.

**실제 게임 검증**

- BR24 새 부팅 선택 화면의 자동 사격·복귀를240캡처로 기록하고 시간 대응27창/3판과 흐름판을 직접 열람했다. 추가 확정 잘림/큰 크기 도약을 찾지 못했다. [캡처와 한계](../work/sprite_style_unification_20261107/runtime/br24_selection_summary.json).
- RN37 새 부팅과 복사 카드 DATA3로 포스아머 상태를 불러와 일반 사격·차지샷·대기 복귀를 양방향224캡처로 기록했다. 시간 대응7판과 첫화면·흐름판을 직접 열람했고 추가 확정 팔 분리/크기 도약을 찾지 못했다. [캡처와 한계](../work/sprite_style_unification_20261107/runtime/rn37_shot_summary.json). 약16Hz 창 캡처로 모든60Hz프레임/효과가림을 본 것은 아니며, 이번 녹화에서 실행 참조별 RAM/GPU를 기록하지 않았다. 기본형·부분아머는 정적검사와 구분한다.
- RN35 선택 확정·승리·귀환, RN30 등장7, RN28 반동/복귀, RN26 특수기 실기 근거도 보존한다. RN30 등장126..139의 실제 마스크는0,140부터15였으므로 포스 등장 실기 완료로 확대하지 않는다. WebP 합쳐진 프레임은 캡처시간으로 검증 대응한다.

F1/F3·메모리쓰기 없이 시험 에뮬레이터를 종료했고 [보호44](../work/sprite_style_unification_20261107/protection_checkpoint44.json)의80파일·카드5쌍은 불변이다.

**진행 중/다음 작업**

시부키 Ultimate85..92 후보 `1f271aea…`는 root가 재독출6판과 원순서4판을 직접 확인했다([검토140](../work/sprite_style_unification_20261107/root_review_checkpoint140.json)). 독립검사·동결 후 통합한다. 나나 Ultimate호버10은 원래 탄환 발생점과 기존 권총끝의 차이를 발견해 새 팔과 정본 사랑이를 국소 정합 중이다. 코드/탄환/전신·추진발을 임의 변경하지 않는다. 이후 양쪽 차량·호버·노바 등 잔여를 계속 검토한다.

나나 선택화면1..8은 원점이 모두 무반전X0/Y0임을 확인했다. 첫 동기화는 원타일44개 중 공유5개를 제외한39개의 독점 공간이 부족해 쓰기 전에 거부됐다. 세부를 삭제해 맞추지 않으며, 미참조 공간과 원코드 사용 관계를 조사 중이다. 아직 이 UI8은 RN37에 미반영이다. 리코·린 일반/블랙/UI·끝점 검토도 범위에 유지하며 현재 추가 확정 재작화 후보는 없다.

**검증 기록 충돌과 복원:** 새87/92 독립검사에서 옛138/139 검사 폴더 이름을 재사용하여 예전 보고서/판독기가 덮인 것을 발견했다. 새 자료를 별도 보존하고 과거 세션 로그로 복원했으며 옛 보고서 `bc5269ec…`, 시각검토 `f6c67b22…`, 비교이미지는 기존 잠금 해시와 동일함을 확인했다. 옛 판독기 자체의 사전 해시는 없어 그 코드의 과거 바이트 동일성까지 주장하지 않는다. 원화/ARC/BIN/동결/사용자 파일은 변경되지 않았다. [복원 근거](../work/sprite_style_unification_20261107/zero_audit/settle138_139_recovery01/restoration.json). 새 검사는 고유한 `nana_base_settle87_92_independent01`로 분리하고31입력을 잠갔다.

시부키 after135 팔과 나나 Ultimate 사다리149/151/153 보정은 이미지 도구 자동 안전검토 거부로 미완료이며 우회하지 않는다. 관련 사다리7참조는 이전 그림 보존. 나나 저체력120..125 실제 발동도 이전 실패로 미검증이다. 전체 미술·전수 실기·최종 사용자 수용 완료를 주장하지 않는다.

'''
for name,marker in [('STATUS.md','아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.'),('SPRITE_STYLE_UNIFICATION_20261107.md','아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.')]:
 p=ROOT/'docs'/name;old=p.read_text('utf8');assert marker in old;p.write_text(old.split('\n',1)[0]+'\n\n'+prefix+old[old.index(marker):],'utf8')
print('BR24/RN37, actual RN37 shooting, protection44, pending UI allocation and independent Ultimate')
