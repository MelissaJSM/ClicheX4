"""기존 잔여 읽기 보고서를 덮지 않고 실제 열람 결론과 입력 잠금 추가."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
O=D/'nana_remaining_after_hover_read01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def save(name,obj):
 p=O/name;assert not p.exists();p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf8');return {'path':rel(p),'sha256':sha(p)}
r=json.loads((O/'report.json').read_text('utf8'))
assert sha(O/'report.json')=='1f3ef6ebb66005fdc25c8bc3dffba48f5806c7b7cdb59d85f0808ff1e810401f'
views=[]
for n in ('base_preparation','fourth_preparation','base_strike_effects','fourth_strike_effects'):
 p=O/f'{n}.png';views.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
v=save('visual_review.json',{'scope':'최신 PL00 잔여 Nova 213..220의 별도 4판 정적 열람. 새 제작/전체 품질 완료 판정 아님.','report_sha256':sha(O/'report.json'),'actually_viewed':views,'observations':['213/214는 같은 웅크린 축을 공유하지만214 얼굴 왼쪽의 분홍 추가 면과 다리층 차이가 있어 현재 그대로 동일 별칭이라고 부를 수 없다. 별도 새 몸체 원화가 반드시 필요하다는 확정은 아니며 효과/손 의미의 출처를 먼저 구분해야 한다.','215/216은 현재 두 의상 모두 같은 그림이다. 원US부터 같은 그림이었다는 뜻은 아니다.','217의 돌진 몸체는 머리/옷 명암 덩어리가 최근 상세화와 달라 후속 세부 검토 대상으로 남긴다.','218/219는 인물이 없는 독립 분홍 에너지이며 새 인물 원화 누락으로 세지 않는다.220은217의 Y+1 몸과 별도 에너지의 합성이다.'],'runtime_or_new_MIPS':False,'new_generation_or_asset_changes':False})
rows=[
 {'forms':'기본/포스','refs':'213/214/215/217','classification':'서로 다른 현재 그림의 원출처/세부 검토','remaining':'214는 추가 손/효과 의미부터 확인. 신규4원화 확정 수 아님'},
 {'forms':'기본/포스','refs':'216','classification':'현재215와5층 동일 별칭','remaining':'215 교체 때 연동. 원US는 다름'},
 {'forms':'기본/포스','refs':'218/219','classification':'별도 에너지 효과','remaining':'현재색/형상·순서 보존 검토. 새 몸 원화로 세지 않음'},
 {'forms':'기본/포스','refs':'220','classification':'217 Y+1 + 별도 효과','remaining':'새217이 바뀌면 몸 연동. 가시 몸799픽셀 현재exact, 추가효과2708픽셀'},
 {'forms':'Ultimate 전후','refs':'148/149/150/151/152/153/155','classification':'도구 거부 또는 연결 보류7','remaining':'부모 보존·미완료. 새몸3/반전/사격 연동을7원화로 세지 않음. 재시도/우회 없음'},
 {'forms':'전폼','refs':'140/208..212','classification':'실루엣/전환/광선 보존 검토','remaining':'Ultimate의 기존 근거를 PL00에 무근거 확대하지 않음. root 최종 보존 판정 별도'},
 {'forms':'기본/포스','refs':'221..230','classification':'새 호버 최종 후보','remaining':'이 보고 최초 시점 동결 전. Audio 별도 최종 감사 완료 메시지 수신, root 동결/통합은 별도'},
 {'forms':'전폼','refs':'기존 preserve_reviewed / UI / HQ / 작은 차량머리','classification':'기존 수용 근거 유지','remaining':'미재작화만으로 품질 미달/신규 원화 필요로 세지 않음'}]
extra=[]
for p in [W/'nana_audit/base_hover_final_independent01/report.json',W/'nana_audit/base_hover_final_independent01/visual_review.json',W/'nana_audit/base_hover_final_independent01/READER_LOCK.json']:
 assert p.is_file();extra.append({'path':rel(p),'sha256':sha(p),'status':'별도 감사자 완료 증거 읽기; 이 스크립트가 해당 검사를 실행한 것은 아님'})
c=save('conclusions.json',{'report_sha256':sha(O/'report.json'),'visual_review':v,'rows':rows,'late_scope27_correction':'기본85/86/87/92는 이미 root FROZEN. 이전 scope27 누락을 미제작으로 세지 않는다.','new_hover_independent_support':extra,'all_nana_complete':False,'counts_are_not_artwork_or_quality_rates':True,'new_native_or_runtime_tests':False})
inputs=dict(r['inputs'])
for p in [Path(__file__),D/'read_nana_remaining_after_hover01.py',O/'report.json',O/'visual_review.json',O/'conclusions.json']:
 inputs[rel(p)]=sha(p)
for row in views+extra:inputs[row['path']]=row['sha256']
for path,h in inputs.items():assert sha(ROOT/path)==h,path
l=save('READER_LOCK.json',{'input_count':len(inputs),'inputs':inputs,'old_reports_or_frozen_files_modified':False})
print(json.dumps({'visual':v,'conclusions':c,'lock':l}))
