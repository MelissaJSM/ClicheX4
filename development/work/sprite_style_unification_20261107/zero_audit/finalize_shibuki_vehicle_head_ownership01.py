"""기존 원시읽기와 동료 실제 호출코드 읽기를 별도 최종 근거에 결속한다."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;O=D/'shibuki_vehicle_head_ownership01';N=W/'nana_audit/shibuki_vehicle_head_callers_read01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(R).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def write(name,obj):
 with(O/name).open('x',encoding='utf8')as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
r=read(O/'report.json');assert r['passed']and sha(O/'report.json')=='f54782ea7e2e0cce035c7ecb8a8f1ebb5273b0b3670a9f2f35ebe28d615a9dfa'
files=r['inputs'].copy()
def track(p):files[rel(p)]=sha(p);return{'path':rel(p),'sha256':sha(p)}
for p,h in files.items():assert sha(R/p)==h,p
assert sha(N/'report.json')=='ada86dcc573d0e8e3b98cf1a4b86c3f335ddee685f8622abc39cf828b11ccd34'
assert sha(N/'clarification.json')=='bc0c40b382fea64fb091473307e3d025d05891558ff7c81a17547514cc6ea0c1'
caller={k:track(N/k)for k in('report.json','conclusions.json','clarification.json','READER_LOCK.json')}
viewed=[track(O/'US_current_fourforms.png'),track(W/'shibuki_audit/vehicle_head_accessory_read01/four_forms_existing_head.png')]
write('visual_review.json',{'actually_viewed':True,'images':viewed,'observations':['원US와 현재 네폼 비교1판 및 대기·작은머리·색인 비교1판을 실제 열람했다.','현재 작은머리는13×15에144px이며 폼별 측면 색 차이는 있지만19표시는 같은 그림의 원점변형이다. 원US의 머리와 모양이 다르며 원US의 여러크롭을 복원한 상태는 아니다.','현재 작은Ultimate 머리에 금색은 아래 홍채1셀 중심으로 보이며 대기의 이마고글 표현은 약하다. 내부세부 보완은 이 현재작화 정책을 기준으로 검토할 수 있다.'], 'limits':['새a0629 후보 미술검토는 별도 독립보고이다.','실제 조종석 몸체와의 배치·게임내 좌우반전·도달성은 이두판만으로 증명하지 않는다.'],'new_art_generated':False,'runtime_verified':False})
write('conclusions.json',{'passed':True,'scope':'시부키 원US/현재 PL00·PL02 차량 작은머리 소유와 일반 호출경로 읽기','report':track(O/'report.json'),'visual':track(O/'visual_review.json'),'caller_peer_evidence':caller,'verified':['원US두ARC와현재두ARC 각각20참조×32조합=총2560조합.198은모두투명하며678층은모든참조에서투명이다.','현재네폼은19개13×15/144px 머리가 정규화RGBA exact이다. 원US는base/Ultimate전후5개,Fourth6개 서로다른정규화RGBA크롭이므로19동일은현재Shibuki수용정책으로만표기한다.','현재비어있지않은0/5 레코드는 대상밖 소비자와 공유되지 않는다. 빈678 레코드는 다른동작에서도공유되며 원래전체빈타일을 보호해야한다.','부모PL02의198은196/197과raw를공유한다.19타깃동시새raw로합칠경우198을원래raw에별도로남겨야한다.','mech→normal state18→player_ride→일반dispatcher 본체·부분아머 경로는 동료가원US/BR29에서직접대조했다.198도원표50/51에포함된다.','원US는player+A7 아머비트.현BR29는비Ultimate만그대로사용하며Ultimate작은머리는engine+47=0일때15,비0일때0.217..230강제15정책을184..203에적용하지않는다.','실제머리5는head bit1만영향을주며타비트/arm variant는빈678덕분에표시변화없다.이사실은원함수호출을생략한다는뜻이아니다.'],'current_vs_original_us':{q['form']:{'current19_normalized_exact':q['current19_aliases_exact'],'US_RGBA_crop_groups':list(q['US_normalized_RGBA_groups'].values())}for q in r['forms']},'cautions':['190은선형원표스캔에서관측되지않았지만미도달/삭제가능으로확정하지않았다.','원US크롭복원과현재머리내부고글보완은별개다.','동료최초conclusions 일부한국어 인코딩손상은원파일을보존하고clarification.json으로정정했다. 주소·해시·정상mask본문은 별도로읽었다.'],'producer_functions_called':False,'resources_modified':False,'new_MIPS_execution':False,'runtime_verified':False})
for p in(O/'conclusions.json',D/'read_shibuki_vehicle_heads01.py',Path(__file__)):track(p)
for p,h in files.items():assert sha(R/p)==h,p
write('READER_LOCK.json',{'files':dict(sorted(files.items())),'original_inputs_unchanged':True,'source_or_resource_writes':False})
print(json.dumps({k:sha(O/k)for k in('report.json','visual_review.json','conclusions.json','READER_LOCK.json')}))
