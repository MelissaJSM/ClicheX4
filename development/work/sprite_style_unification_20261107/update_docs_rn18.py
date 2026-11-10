from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for filename in ('STATUS.md','SPRITE_STYLE_UNIFICATION_20261107.md'):
 p=ROOT/'docs'/filename;old=p.read_text('utf8')
 old=old.replace('최신 통합 시험본은 BR v15 / RN v17이다.','최신 통합 시험본은 BR v15 / RN v18이다.',1)
 start=old.index('RN v17은 나나 Ultimate 라이징7 통합본 그대로다(')
 end=old.index('아래 RN v16 및 이전 문단은 당시의 상세 이력이다.' if filename=='STATUS.md' else '아래는 RN v16 및 이전 시점의 이력이다.')
 text='''RN v18에 나나 기본/포스 피격13참조(새 몸체4·효과 파생9)를 통합했다([CUE](../out/ver_rin_nana/sprite_style_unification_20261107_v18/rin_nana.cue)). BIN `0f40463b883e00a7e3acf268fd45052b905d0454440d8c5436ce24fe80f58c95`, PL00 `978a9fc1…`, 누적296변경섹터·전251,793섹터 비교/EDC·ECC/재추출/원MIPS·GPU 검사 통과. 기존 Ultimate 라이징7과 린은 보존했다. 피격13의 독립 공유층 검사·원순서 재생과 [최종 원화검토85](../work/sprite_style_unification_20261107/root_review_checkpoint85.json), [순서검토86](../work/sprite_style_unification_20261107/root_review_checkpoint86.json)를 연결한다.

새 부팅 기본형2회 기록320창·포스160창에서 기본106..114와 포스233..236 모두 실제 RAM/GPU 일치 표본을 얻었으며24판을 직접 열람했다. 추가 확정 몸체 분리·크기 변화·피격 효과 잘림은 찾지 못했고 비동기 미확정 사건은0이다. **모든 방향/모든 부분 아머/전체60Hz/모든 피해원까지 실기 완료를 뜻하지 않는다.** 첫 잘못된 긴 입력은 실행 전에 거부되었으며 짧은 제한을 지킨 계획으로 다시 실행했다. [실기·실패 기록·제한](../work/sprite_style_unification_20261107/runtime/nana_hurt18_summary.json), [직접 검토92](../work/sprite_style_unification_20261107/root_review_checkpoint92.json).

[현재 단독 모음집 v19](../out/sprite_style_unification_20261107/review_v19/ALL_SPRITES_CURRENT.html)은 BR15/RN18의4,510표시·28폼을 제공하며2,256변경표시 픽셀과4재생루프 검사를 통과했다. **중복 의상·색상·UI 참조가 있으므로 이 수를 품질 완료율로 환산하지 않는다.** [전체 범위 장부](../work/sprite_style_unification_20261107/zero_audit/full_scope_matrix03/COVERAGE.html)는 대상별 근거와 미완료 후보를 구분하며 RN18 최신 실기는 위 기록에서 보충한다. 보호28에서 원본/출시본/포인터/F1 등80파일·시험카드5쌍이 동일하고 별도 포스 카드 사본도 재검증했다. 두 시험 세션은 종료했다.

다음 제작은 나나 Ultimate 피격의 손발·공통층/효과와 시부키 Ultimate 사다리의 사격·접점/공통층이다. 새 피격 초기8표시를 [88](../work/sprite_style_unification_20261107/root_review_checkpoint88.json)·[90](../work/sprite_style_unification_20261107/root_review_checkpoint90.json), 사다리 전후12참조와 사격 후보를 [89](../work/sprite_style_unification_20261107/root_review_checkpoint89.json)·[91](../work/sprite_style_unification_20261107/root_review_checkpoint91.json)에서 직접 보았지만 아직 통합 BIN에는 포함되지 않았다. 남은 저체력·차량·등장·승리·귀환 등은 계속 장부에 남아 있다. 리코·린과 UI 사본까지 네 캐릭터 전체 범위를 유지한다.

'''
 p.write_text(old[:start]+text+old[end:],'utf8')
print('Updated BR15/RN18 evidence and remaining work; not final completion')
