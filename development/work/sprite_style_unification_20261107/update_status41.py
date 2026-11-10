from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2];W=ROOT/'work/sprite_style_unification_20261107'
c=json.loads((ROOT/'out/sprite_style_unification_20261107/review_v32/browser_checks.json').read_text('utf8'));assert c['passed']and len(c['modified_pixel_checks'])==2832
for n in ('br_v27','rn_v40'):assert json.loads((W/f'staging_{n}_native_checks.json').read_text('utf8'))['passed']
assert (W/'runtime/rn40_nova_summary.json').exists()
for name in ('STATUS.md','SPRITE_STYLE_UNIFICATION_20261107.md'):
 p=ROOT/'docs'/name;t=p.read_text('utf8');marker='아래 BR15/RN18 및 이전 내용은 당시의 상세 이력이다.' if name=='STATUS.md'else'아래 기록은 BR15/RN18 당시와 그 이전의 이력이다.'
 head,tail=t.split(marker,1)
 for old,new in [('BR26','BR27'),('RN39의28폼','RN40의28폼'),('[RN39](../out/ver_rin_nana/sprite_style_unification_20261107_v39','[RN40](../out/ver_rin_nana/sprite_style_unification_20261107_v40'),('ver_buki_riko/sprite_style_unification_20261107_v26','ver_buki_riko/sprite_style_unification_20261107_v27'),('b99860d4a87e8b152d2476ea65851583eb01d7978f9b97488a8d88ad7b536f27','73c2b28eb59739234351b59d9f18de6a1a9429bcf9d8e71327f3206dcb6d2cbb'),('8eb84afaa7c201dfcaee8e5cbf4c2fef152d423b10b501e8238362f9b5cca5b2','fdcebed25fb3ffde641d9a6fc5f56180e74f2d3367057eea2f70c5123ac613b9'),('모음집 v31','모음집 v32'),('review_v31/','review_v32/'),('2,796','2,832'),('시부키820/나나845','시부키846/나나855'),('약62.0%','약62.8%'),('보호47','보호48'),('protection_checkpoint47.json','protection_checkpoint48.json')]:head=head.replace(old,new)
 # Preserve historical runtime version numbers and describe new build changes separately.
 start=head.index('시부키 기본/포스 차량13 `')
 end=head.index('\n\n**검증 기록 충돌',start)
 head=head[:start]+'''시부키 기본/포스 차량13과 Ultimate 차량13을 BR27에 통합했다. 새그림의 독립검사와 직접 비교판18+18 검토를 마쳤으며 [검토144](../work/sprite_style_unification_20261107/root_review_checkpoint144.json)·[145](../work/sprite_style_unification_20261107/root_review_checkpoint145.json)에 근거를 보존했다. 실제 차량 손잡이·발판 실기는 아직 미실행이다.

나나 Ultimate 노바8을 RN40에 통합했고 [직접검토146](../work/sprite_style_unification_20261107/root_review_checkpoint146.json) 및 [실제 양방향 노바112캡처·6판](../work/sprite_style_unification_20261107/runtime/rn40_nova_summary.json)을 확인했다. 관찰한 준비·돌진·복귀에 추가 확정 절단/크기 도약은 없었다. 점멸이 몸을 가리는 구간과 모든60Hz·참조별 실기 추적은 미검증이다.

나나 기본/포스 호버는 새원화12셀의 몸10표시를 정합하고, 얼굴·손·다리를 공유한 파츠 조합10판을 직접 검토했다. 새 사격팔8표시 후보를 받아 합류 중이며 마지막230 사격팔·50층 패킹·실기는 남았다. 아직 BIN에는 반영하지 않았다. [원화/프롬프트/조합](../work/sprite_style_unification_20261107/root_nana_hover/). 시부키 노바 준비4도 새 의상·부분조합·패킹 검토 중이다. 리코·린 일반/블랙/UI·끝점도 전체 범위에 유지하며 현재 추가 확정 재작화 후보는 없다.''' +head[end:]
 p.write_text(head+marker+tail,'utf8')
print('BR27/RN40; album32 verified2832; runtime Nova112; protection48; full task unfinished')
