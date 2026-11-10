from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
status='''# 프로젝트 상태

**현재 작업은 네 캐릭터 전체의 세부 묘사 통일이며 계속 진행 중이다.** 최신 통합 시험본은 BR v15 / RN v17이다. 사용자는 한도 해제 후 계속 작업을 지시했으며 추가 결정으로 막힌 항목은 없다. 중간 검증을 전체 완료나 사용자 최종수용으로 취급하지 않는다. 활성 배포 포인터는 기존 재감사본 그대로 보존한다.

시부키 기본/포스 이동·사격32를 [BR v15 시험 CUE](../out/ver_buki_riko/sprite_style_unification_20261107_v15/shibuki_riko.cue)에 통합했다. BIN `dfd1b9d09e8fad846aebfd51a89aecc46bff98bc6281619bb21abf1c8dbf27fc`, PL00 `381d83fa…`, 변경318섹터다. 전섹터/EDC·ECC/재추출/EXE 보존·원MIPS/GPU 검사 통과. 새 부팅 기본288창·포스287창에서 새1..32 전부 각각 RAM/GPU 일치 표본을 확보했고, 추가 포스 차지샷192창까지 총36판을 직접 검토했다. 추가 확정 분리·축소·윤곽 손실은 찾지 못했다. **비동기 미확정 사건 기본3/포스1은 별도로 남겼으며 전체60Hz/부분아머 전조합 실기 완료는 아니다.** [실기 근거와 제한](../work/sprite_style_unification_20261107/runtime/shibuki_run15_summary.json), [직접 검토82](../work/sprite_style_unification_20261107/root_review_checkpoint82.json).

시부키 새 그림의 세부를 줄이지 않고 저장하기 위해 고정186,228B 그래픽 항목 안의 원디코더 미소비 후미344/328B를 재사용했다. 내부은행0만672B 증가, 외부 항목/LBA/EXE/음향/팔레트 불변이며 은행12/13은 절대위치·전체바이트도 보존한다. [508참조 실제 원로더/디렉터리/객체/해독·업로드 검사](../work/sprite_style_unification_20261107/zero_audit/shibuki_run32_directory_native01/report.json), [독립 보존검사](../work/sprite_style_unification_20261107/zero_audit/shibuki_run32_independent01/report.json), [동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_base_run01/FROZEN.json)을 연결했다. 현재 승인된 가역 재작화·재삽입 범위의 구현 판단이며 새 사용자 승인 문구를 만들어 기록하지 않는다.

RN v17은 나나 Ultimate 라이징7 통합본 그대로다([CUE](../out/ver_rin_nana/sprite_style_unification_20261107_v17/rin_nana.cue)). BIN `13da8bfc9cb6968028300ff362975826c1d6f08f3a009b623fa26fe529e5b124`, 전섹터/원MIPS/GPU 검사와 후폼 새 부팅351창·12판 검토 및 새7참조 RAM/GPU 일치를 마쳤다. 재킷/부분 전조합 실기는 별도다. [검증 근거](../work/sprite_style_unification_20261107/runtime/nana_ultimate_rising17_summary.json).

[현재 단독 모음집 v18](../out/sprite_style_unification_20261107/review_v18/ALL_SPRITES_CURRENT.html)은 BR15/RN17의4,510표시·28폼을 제공하며2,217변경표시 픽셀과4재생루프 검사를 통과했다. **중복 의상·색상·UI 참조가 있으므로 이 수를 품질 완료율로 환산하지 않는다.** [전체 범위 장부](../work/sprite_style_unification_20261107/zero_audit/full_scope_matrix02/COVERAGE.html)는 대상별 근거와 미완료 후보를 구분한다. 보호27에서 원본/출시본/포인터/F1 등80파일·시험카드5쌍이 동일하며 별도 포스 카드 사본도 다시 검증했다. 모든 시험 ePSXe는 종료했다.

다음 제작은 나나 기본/포스 피격의 새 하체·오라 정합, 시부키 Ultimate 사다리의 손발 접점·공통층이다. 초기 미술은 [77](../work/sprite_style_unification_20261107/root_review_checkpoint77.json), [78](../work/sprite_style_unification_20261107/root_review_checkpoint78.json), [79](../work/sprite_style_unification_20261107/root_review_checkpoint79.json)에서 직접 검토했으나 아직 새 BIN 미포함이다. 뒤통수 안경 반복은 국소 교정했고151 낮은 팔과235/236 피격 오라의 접점은 후속 교정 중이다. 리코·린 및 두X의 차량/등장·승리·귀환/UI까지 전체 범위를 유지한다.

'''
p=ROOT/'docs/STATUS.md';old=p.read_text('utf8');marker='아래 RN v16 및 이전 문단은 당시의 상세 이력이다.';assert marker in old;p.write_text(status+old[old.index(marker):],'utf8')
p=ROOT/'docs/SPRITE_STYLE_UNIFICATION_20261107.md';old=p.read_text('utf8');marker='아래는 RN v16 및 이전 시점의 이력이다.';assert marker in old
head=status.replace('# 프로젝트 상태','# 대기 기준 스프라이트 세부 묘사 통일',1)
p.write_text(head+old[old.index(marker):],'utf8')
print('Updated STATUS and sprite style report: BR15/RN17, still in progress')
