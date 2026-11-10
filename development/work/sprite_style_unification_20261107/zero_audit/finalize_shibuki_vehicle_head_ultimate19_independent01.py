"""실제 재추출6판과 별도 원화·caller 근거를 최종 독립 잠금에 결속한다."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';P=H/'prepared_vehicle_head_ultimate01';O=D/'shibuki_vehicle_head_ultimate19_independent01';S=W/'nana_audit/shibuki_vehicle_head_source_independent01';C=W/'nana_audit/shibuki_vehicle_head_callers_read01';U=D/'shibuki_vehicle_head_ownership01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(R).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def write(name,obj):
 with(O/name).open('x',encoding='utf8')as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
r=read(O/'report.json');assert r['passed']and sha(O/'report.json')=='5b4cd8d554b07d0f33e1f798669a3f35d5b71145292656923e13e7da5f4380d8'
files=r['inputs'].copy()
def track(p):files[rel(p)]=sha(p);return{'path':rel(p),'sha256':sha(p)}
for p,h in files.items():assert sha(R/p)==h,p
assert sha(S/'report.json')=='9913e172d0169950b5c5add7e9436e65269f5c44345e50b0d508f19e15e53672'
source=read(S/'report.json');assert source['passed']and source['candidate_sha256']==r['candidate_sha256']and source['exact_owned_layers']==38
for p,h in source['inputs'].items():assert sha(R/p)==h,p
meta=read(H/'vehicle_head_ultimate_targets01/manifest.json')
for row in source['targets']:
 for pb,proof in row['layers'].items():assert proof['indexed_sha256']==meta['targets'][str(row['ref'])][pb]
source_evidence={k:track(S/k)for k in('report.json','visual_review.json','READER_LOCK.json','reader.py')}
caller_evidence={k:track(C/k)for k in('report.json','conclusions.json','clarification.json','READER_LOCK.json')}
ownership_evidence={k:track(U/k)for k in('report.json','visual_review.json','conclusions.json','READER_LOCK.json')}
viewed=[]
for q in r['readback_sheets']:assert sha(R/q['path'])==q['sha256'];viewed.append(track(R/q['path']))
assert len(viewed)==6
visual={'actually_viewed':True,'observer':'/root/hud_checkpoint','boards':viewed,'board_count':6,'observations':['実候補ARCから独立再抽出した前後19参照4板と184/196部分2板を実際に閲覧した。','새머리는 부모와 같은13×15 범위 안에서 이마의 금색가로선과 중앙 머릿결 음영이 더 분명하다. 아래 홍채와 이마장식은 분리돼 보인다.','before의 측면파랑과 after의 보라머리는 같은 눈·귀 위치를 유지한다.19원점에서 새로운 명백한 얼굴·귀 절단이나 크기 급변을 찾지 못했다.','184/196 부분16마스크판에서 head 비트1에만 측면색이 바뀌고 그밖 비트에 새 조각이 나타나지 않는다. 기존빈198은 수치로32조합 공백을 확인했다.','귀 사이 추가[-5,-35]/제거[-6,-36]는 같은 픽셀수의 새로운 계단윤곽이다. 외곽전체동일 또는 원US복원으로 판단하지 않는다.'],'source_peer_actual_views':source_evidence['visual_review.json'],'limits':['재추출4판은 각참조부모/후보를 같은crop으로 비교한 정적판이다. 실제조종석 위치관계는 시험하지 않았다.','608부분을 수치검사했지만 개별608판을 전부 열람했다고 주장하지 않는다. 부분판은184/196의16마스크다.','이감사는Ultimate 작은머리만 포함한다. 기본/포스 작은머리 세부보완 여부와 전체캐릭터 완료는 별도다.'],'new_art_generated':False,'source_or_resource_modified':False,'new_MIPS_execution':False,'runtime_verified':False}
visual['observations'][0]='실제 후보ARC에서 독립 재추출한 전후19참조4판과184/196부분2판을 실제 열람했다.'
write('visual_review.json',visual)
v=read(P/'verification.json');assert v['total_identical_builds']==3 and v['rejected_count']==11 and all(x['rejected']for x in v['rejected_inputs'])and all(h==r['candidate_sha256']for h in v['reproduction_sha256'])
sequence=read(P/'original_sequence_read.json');assert sequence['candidate_sha256']==r['candidate_sha256']and sequence['all_pointer_step_bytes_exact']and sequence['table_count']==26 and sequence['step_count']==92
write('conclusions.json',{'passed':True,'scope':'고정 a0629 Shibuki Ultimate 차량머리19의 출처·자원·미술 독립검사 마감','candidate_sha256':r['candidate_sha256'],'parent_sha256':r['parent_sha256'],'report':track(O/'report.json'),'visual':track(O/'visual_review.json'),'direct_source_peer':source_evidence,'original_ownership':ownership_evidence,'caller_peer':caller_evidence,'checks':r['counts'],'source_chain':['별도독립자가 생성1254²→전체64 NEAREST/alpha128/실제15색을 직접재양자화했다.','실제RGB HSV의금색10표본중5셀변경,부모측면9중새보라8만before overlay4로직접재구성했다.','19부모원점평행등록38층은 source보고rawarray해시와목표manifest를다시대조했고,우리ARC reader가95층 전체와비대상을대조했다.'],'storage_protection':['19새raw는하나의5타일stream이며0/2/3전체는빈칸,body1/overlay4만사용한다.','198은새19stream에서분리되어부모raw/5층/조립/32빈표시를보존한다.','선택빈678의57기록은record_offset포함exact이며해당은행전체bytes도exact.다른동작과공유하는빈기록을새머리로오염시키지않았다.','경계/팔레트/음향/다른entry와비대상493raw/1045층/1753의미조립은exact.타깃38새소유층의기록만허용변경이다.'],'original_vs_policy':['현재19동일머리는기존Shibuki수용정책.원US5/6개서로다른RGBA크롭복원은아니다.','작은머리의실제Ultimate선택은engine+47=0이면15,비0이면0이며호버217..230강제15와별개다.원US는player+A7이었다.','원표26/92스텝보존은읽기근거이며실제차량26동작재현으로세지않는다.198도원표50/51에포함되어빈프레임보호가필요하다.190은선형표미관측만으로삭제하지않았다.'],'existing_author_evidence':{'native19':r['native_author_report_bound'],'reproduction':{'evidence':track(P/'verification.json'),'identical_builds':3,'rejections':11,'independently_rerun':False},'original_tables':track(P/'original_sequence_read.json'),'post_lock':track(P/'post_lock_evidence.json')},'limits':['생성원화 직접재구성은Audio독립실행이고최종ARC·부분·시각6판은HUD독립실행으로구분한다.','기존원MIPS19 디코드hash는후보와결속했지만새독립MIPS/실기/실제조종석은미실행이다.','루트의최종미술수용및통합/실기는별도단계이며이독립보고가그단계를대체하지않는다.'],'producer_functions_imported_or_called':False,'source_or_resource_modified':False,'new_MIPS_execution':False,'runtime_verified':False})
for p in(O/'conclusions.json',D/'verify_shibuki_vehicle_head_ultimate19_independent01.py',Path(__file__)):track(p)
for p,h in files.items():assert sha(R/p)==h,p
write('READER_LOCK.json',{'files':dict(sorted(files.items())),'producer_locked_inputs':188,'source_inputs_unchanged':True,'source_or_resource_writes':False})
print(json.dumps({k:sha(O/k)for k in('report.json','visual_review.json','conclusions.json','READER_LOCK.json')}))
