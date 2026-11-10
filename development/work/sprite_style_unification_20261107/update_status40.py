from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
album=ROOT/'out/sprite_style_unification_20261107/review_v31';checks=json.loads((album/'browser_checks.json').read_text('utf8'))
assert checks['passed']and len(checks['modified_pixel_checks'])==2796
native=json.loads((ROOT/'work/sprite_style_unification_20261107/staging_br_v26_native_checks.json').read_text('utf8'));assert native['passed']
for filename in ['STATUS.md','SPRITE_STYLE_UNIFICATION_20261107.md']:
 p=ROOT/'docs'/filename;text=p.read_text('utf8')
 old='최신 검증 통합 시험본은 [BR25](../out/ver_buki_riko/sprite_style_unification_20261107_v25/shibuki_riko.cue)'
 assert old in text;text=text.replace(old,'최신 검증 통합 시험본은 [BR26](../out/ver_buki_riko/sprite_style_unification_20261107_v26/shibuki_riko.cue)',1)
 text=text.replace('BIN SHA-256은 BR `21696e9bae002ef6c9f95fed683e7cd531fd6cdfc6c0fdae97529c3b28a09636`','BIN SHA-256은 BR `b99860d4a87e8b152d2476ea65851583eb01d7978f9b97488a8d88ad7b536f27`',1)
 text=text.replace('[전체 모음집 v30](../out/sprite_style_unification_20261107/review_v30/ALL_SPRITES_CURRENT.html)은 BR25/RN39의28폼·4,510표시 중2,757변경(리코491/시부키781/나나845/린640)','[전체 모음집 v31](../out/sprite_style_unification_20261107/review_v31/ALL_SPRITES_CURRENT.html)은 BR26/RN39의28폼·4,510표시 중2,796변경(리코491/시부키820/나나845/린640)',1)
 text=text.replace('**약61.1%는','**약62.0%는',1).replace('2,757픽셀 비교와4재생루프','2,796픽셀 비교와4재생루프',1).replace('review_v30/browser_checks.json','review_v31/browser_checks.json',1)
 old='시부키 기본/포스 차량13 후보 `3e11b7e6…`는 독립검사·508원참조 실행을 통과했으며 마지막 직접 미술검토/동결/통합은 진행 중이다.'
 new='시부키 기본/포스 차량13 `3e11b7e6…`는 독립검사·508원참조 실행과 [직접18판 검토144](../work/sprite_style_unification_20261107/root_review_checkpoint144.json)를 거쳐 [동결](../work/sprite_style_unification_20261107/shibuki_audit/prepared_chaser_base01/FROZEN.json)·BR26 통합을 완료했다. BR26의 실제 차량 손잡이·발판 실기는 아직 미실행이다.'
 assert old in text;text=text.replace(old,new,1)
 text=text.replace('나나 기본/포스 호버는 대기 기준 입력을 준비했고','나나 기본/포스 호버는 새 원화8셀을 생성·고정격자 등록했고 발끝1~3px·눈 위치의 접점 정합을 검토 중이며 아직 BIN 미반영이다. 내장 imagegen 사용 원화/프롬프트는 [작업폴더](../work/sprite_style_unification_20261107/root_nana_hover/)의 art01/02_generated.png 및 art01/02_prompt.txt에 보존했다. 이후',1)
 p.write_text(text,'utf8')
print('BR26/RN39, album31 2796 checks; new hover art remains unintegrated')
