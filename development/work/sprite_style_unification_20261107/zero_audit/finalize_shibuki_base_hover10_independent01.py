"""호버 최종 후보의 실제 열람과 후속 증거를 기존 보고서 변경 없이 결속한다."""
from pathlib import Path
import sys, json, hashlib
R=Path(__file__).resolve().parents[3]; D=Path(__file__).parent; W=D.parent
S=W/'root_shibuki_hover'; O=D/'shibuki_base_hover10_independent01'
sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import raw
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(R).as_posix()
read=lambda p:json.loads(p.read_text('utf8'))
def write(name,obj):
    with (O/name).open('x',encoding='utf8') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
r=read(O/'report.json'); assert sha(O/'report.json')=='638dc4ff63ac9584dac2256a36e2948e4a1aff0ff5752b4fca6ff6b155247ef3'
files=r['inputs'].copy()
def track(p):
    h=sha(p); files[rel(p)]=h; return {'path':rel(p),'sha256':h}
for p,h in files.items():assert sha(R/p)==h,p
arc=Archive((R/r['candidate']).read_bytes()); candidate=r['candidate_sha256']
ilp=S/'hover_input_lock03.json'; il=read(ilp)
assert sha(ilp)=='f2ff91ce1df30fa39adfae38111cb9afc62623b87056c818b410d293af0db561'
assert il['candidate_sha256']==candidate and il['parent_sha256']==r['parent_sha256'] and len(il['files'])==256
for p,h in il['files'].items():assert sha(R/p)==h,p; track(R/p)
input_lock=track(ilp)
repro_p=S/'packed_hover_candidate03/reproduction_checks.json'; repro=read(repro_p)
assert repro['passed'] and repro['candidate_sha256']==candidate and repro['input_lock_sha256']==input_lock['sha256']
assert repro['total_identical_builds']==3 and len(repro['rejected'])==10 and all(h==candidate for h in repro['reproductions'])
native_p=S/'native_components03_native_checks.json'; native=read(native_p)
assert sha(native_p)=='922932cf65443879310c7098b2edbe2ae91ee0c724052b9d7dafdb849b0c7527' and native['passed']
nr=native['resources']['PL00_U.ARC']; assert nr['candidate_sha256']==candidate
native_refs=[]
for bank in nr['banks']:
    assert bank['bank']==0
    for q in bank['native_decoder_checks']:
        z=raw(arc,0,q['frame']); assert hashlib.sha256(z).hexdigest()==q['decoded_sha256']
        assert len(z)==q['bytes']==q['tiles']*128 and q['buffer_outside_and_unused_tail_preserved']
        native_refs.append(q['frame'])
expected=set(range(221,231))|{39,40,41,42,43,44,49,50,59,60,61,62,65,66,79,80}|(set(range(184,204))-{198})
assert set(native_refs)==expected and len(native_refs)==45 and nr['GPU_part_edge_checks']==506
plan_p=R/Path(native['plan']); plan=read(plan_p); assert plan['resources']['PL00_U.ARC']['after']==candidate
cycle_p=S/'native_cycle01/verification.json'; cycle=read(cycle_p)
assert cycle['passed'] and cycle['candidate_arc_sha256']==candidate and cycle['canvas_native_checks']==84 and len(cycle['play_pause_checks'])==12
cm_p=S/'native_cycle01/manifest.json'; cm=read(cm_p); assert cm['candidate_arc_sha256']==candidate and cm['native_table_bytes_exact'] and len(cm['tables'])==12
root_p=W/'root_review_checkpoint162.json'; root=read(root_p)
assert sha(root_p)=='28c6d8a4601d2f837c1b5fc3235c2cd7e918413480c27b3fdaa6c76c56db5c53' and root['candidate_sha256']==candidate
evidence={'input_lock':input_lock,'reproduction':track(repro_p),'original_MIPS_producer_report':track(native_p),'native_plan':track(plan_p),'offline_cycle':track(cycle_p),'original_tables':track(cm_p),'root_visual':track(root_p)}
parent_source=W/'nana_audit/shibuki_vehicle_head_base19_independent01'
for fn,h in [('report.json','e45ec10c709aa2d9eb49d78d5a3cbd65cc883843fd4ce1dac069eccee6dce9f9'),('visual_review.json','ff7d9ba6a7bd84fe2719eb4fbc062ed6e06ddceddaf3dc845d462a3f8f194fad'),('READER_LOCK.json','ee3e130e01eefb38fe01cc818184d1ad4c987c5cff174b0aa314778fb6ce9fad')]:
    p=parent_source/fn; assert sha(p)==h; evidence['parent_smallhead_'+fn]=track(p)
plock=read(parent_source/'READER_LOCK.json')
for p,h in plock['inputs'].items():assert sha(R/p)==h,p
boards=[]
for q in r['readback_sheets']:
    p=R/q['path']; assert sha(p)==q['sha256']; boards.append(track(p))
write('visual_review.json',{
    'actually_viewed':True,'boards':boards,'count':5,'candidate_sha256':candidate,
    'observations':[
        '221/222, 223/224, 225/226, 227/228, 229/230의 자체 재추출 비교 5판을 실제 열람했다. 각 판은 부모·새 입력50층·최종 ARC·부분 mask11/arm2를 같은 원점과 최근접 5배율로 보여 준다.',
        '221/229의 높은 두 팔, 222/230의 남은 반대 높은 팔과 사격팔이 구분된다. 추가로 남은 세 번째 팔이나 새 확정 어깨·손목·발목 절단은 찾지 못했다.',
        '222/224 긴 소매 아래 그늘과 피부 손목이 총 뒤쪽으로 이어지며, 226/228 접힌 팔도 총이 따로 뜨거나 총열이 두 개로 보이지 않는다.',
        '224 손목과 230 칼라의 세 셀은 앞서 확인한 shot02 피부 소유 수정 상태를 유지한다. 기본 빨강/흰 의상은 그대로이고 포스에서만 실제 donor 피부로 복구됐다.',
        '228은 고정 총구 창 안의 얼굴 창 7셀 가림을 기존 source 감사에서 구분했다. 얼굴 전체 무변경이라고 확대하지 않으며, 이번 재추출에서 해당 총과 새 얼굴/머리의 위치는 입력과 동일하다.',
        '부분 mask11/arm2에서도 공통 얼굴·하체와 선택 의상 경계가 이어진다. 223 가슴앞 작은 손은 작게 읽히지만 이번 판에서 새 분리 결함은 확인하지 못했다.'
    ],
    'limits':[
        '이번 5판에는 실제 게임 배경·제트·탄환이 합성되지 않는다. 이전 제트 접점 정적 감사와 최종 원15제트/7탄환 보존 계산을 별도 연결한다.',
        '160개의 다리 획득 부분조합 연결성 검사는 기계 검사이며 모든 조합을 직접 열람한 것으로 세지 않는다.',
        'Root162의 5판 열람은 별도 관찰자 근거다. 이 기록의 직접 열람 수에 더하지 않는다.',
        '새 원화 생성·편집, 새 MIPS 실행, 실제 플레이·물리·타이밍 검증은 수행하지 않았다.'
    ],'source_or_resource_modified':False,'runtime_verified':False})
write('conclusions.json',{
    'passed':True,'scope':'Shibuki 기본/포스 호버221..230의 최종 ARC 50층과 저장용16참조 독립 검수',
    'candidate_sha256':candidate,'parent_sha256':r['parent_sha256'],'report':track(O/'report.json'),'visual':track(O/'visual_review.json'),
    'counts':r['counts'],'source_evidence_reused':r['source_evidence_reused'],'post_report_evidence':evidence,
    'input_files_checked':256,'producer_native_decoded_hashes_rechecked':45,
    'findings':[
        '50층을 body04/shot02 원본 색인과 직접 대조했고 36d4에서 작은머리4cea로 바뀐 부모의 원 호버50층·팔레트가 같음을 확인했다.',
        '변경 raw26은 새 호버10과 저장만 바꾼16이다. 저장16의 모든512개 전체16×16 타일을 역순열로 대조했으며, 조립80개는 타일번호 외 flags/x/y/순서가 동일하다.',
        '1090개의 비미술 대상층 및 나머지1657개 조립 참조의 의미 기록이 같다. 물리 record_offset까지 모두 같다는 주장은 하지 않는다.',
        '832부분 중 호버320은 새 목표와 같고 저장512는 부모와 같다. 실제 진입에 대응하는 다리8..15와 두 팔 타입의160조합은 모두 하나의 연결성분이다.',
        '사격5×32조합에서60불투명+11투명 고정 총구 창이 정확히 유지된다. 원15제트/7탄환의 실제 world 그림·소비 전체타일·조립을 보존했다.',
        '부모 작은머리184..203은198을 포함해 raw·5층·의미 조립·640부분RGBA가 모두 같다. 부모4cea 자체 source/ARC 독립 보고는 Audio의 새 고유 감사에 별도로 결속했다.',
        '엔트리/그래픽·조립 은행 경계·길이·팔레트·음향·다른 엔트리를 보존했다. 원본·후보·제작 입력은 변경하지 않았다.'
    ],
    'original_MIPS_scope':'제작자 원MIPS report922932cf의45 decoded 해시를 이번 ARC에서 직접 재대조했다. 36d4 통합 부모 대비 작은머리19가 포함되어 GPU506이며, 이번4cea 대비 변경26의 정적 GPU411과 범위가 다르다. 독립 새 MIPS/전체 로더 실행으로 세지 않는다.',
    'source_scope':'기존 body03/shot01/shot02 증거의 잠금과 입력을 재확인하여 재사용했다. 이번 단계는 생성원화 재제작이나 모든 source의 새 재양자화가 아니다.',
    'pending':'실제 게임 통합·호버 물리/입력/동적 탄환과 제트·매 프레임 GPU 관측은 별도이다.',
    'producer_functions_imported_or_called':False,'source_or_resource_modified':False,'new_MIPS_execution':False,'runtime_verified':False})
for p in (O/'conclusions.json',Path(__file__),D/'verify_shibuki_base_hover10_independent01.py'):track(p)
for p,h in files.items():assert sha(R/p)==h,p
write('READER_LOCK.json',{'files':dict(sorted(files.items())),'candidate_sha256':candidate,'previous_reports_preserved':True,'source_or_resource_writes':False})
print(json.dumps({k:sha(O/k)for k in ('report.json','visual_review.json','conclusions.json','READER_LOCK.json')}))
