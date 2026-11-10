from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
D=W/'nana_audit/rising_repaint/joint_layers_probe_v2'
pages=[D/f'{kind}_{i}.png' for kind in ('comparison','partial') for i in (1,2,3)]+[W/'zero_audit/nana_arrival_endpoint_audit01/arrival_layers_133_137.png']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
 'findings':['나나 라이징 기본/포스 양팔 완성 및 부분층6판을 검토했다. 교정한 다리폭·머리 명암·사랑이/팔 접점이 유지되고 단독부분에 새 확정 고립점은 찾지 못했다.','등장133..137의 현재/의상교환 당시/실제재킷층 비교1판을 검토했다. 재킷이 최근 수정에서 사라진 회귀가 아니라 대기보다 앞섶·소매 식별이 약한 기존 미술 표현으로 구분한다.'],
 'limits':['라이징 최종패킹·독립재추출/실기 검증 전이다.','등장 재킷의 식별 보완은 후속 세부 묘사 작업이며 원래코드 변경 근거로 삼지 않는다.'],'final_user_accepted':False}
p=W/'root_review_checkpoint64.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
