"""완료한 독립 읽기와 실제 열람을 새 증거에 결속한다. 제작/자원 변경 없음."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
H=W/'shibuki_audit';O=D/'shibuki_ultimate_hover10_independent01'
PEER=W/'nana_audit/shibuki_ultimate_hover_body_source_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(R).as_posix()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(name,data):
 with (O/name).open('x',encoding='utf8')as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
report=read(O/'report.json');assert report['passed']and sha(O/'report.json')=='ddfcaa28f2871a663275d5990e6f26685bf8eff7cc02484c0135cd87549f0b3f'
inputs=dict(report['inputs'])
def track(p):inputs[rel(p)]=sha(p);return {'path':rel(p),'sha256':sha(p)}
for p,h in inputs.items():assert sha(R/p)==h,p
peer=read(PEER/'report.json');assert peer['passed']and peer['candidate_sha256']==report['candidate_sha256']
assert sha(PEER/'report.json')=='3e7127eb3f7b04d4e87a167e1a1f53f5482fb033a30427df4eacb9e321986342'
assert sha(PEER/'visual_review.json')=='d29005f25a94cc9e5e5cbb29b08010f927440b6235aef3f8f767ab51c19c2616'
for row in read(PEER/'READER_LOCK.json')['files']:
 p=R/row['path'];assert sha(p)==row['sha256'],p;track(p)
for p,h in peer['source_files'].items():assert sha(R/p)==h,p;inputs[p]=h
for n in(221,223,225,227,229):
 for pb in(0,5,6,7,8):
  pp=PEER/f'reconstructed/{n}_bank{pb}_indices.png';tp=H/f'hover_ultimate_targets01/{n}_bank{pb}_indices.png'
  assert np.array_equal(np.array(Image.open(pp)),np.array(Image.open(tp)));track(pp);track(tp)
producer={}
for key,path in {
 'verification':'prepared_hover_ultimate01/verification.json',
 'original_MIPS10':'hover_ultimate_components_native_checks.json',
 'static_contacts':'hover_ultimate_final_contacts01/report.json',
 'original_sequence':'hover_ultimate_sequence01/report.json',
 'browser':'hover_ultimate_sequence01/browser_verification.json',
 'post_lock':'prepared_hover_ultimate01/post_lock_evidence.json',
}.items():producer[key]=track(H/path)
v=read(H/'prepared_hover_ultimate01/verification.json')
assert v['total_identical_builds']==3 and len(v['reproduction_sha256'])==2 and all(x==report['candidate_sha256']for x in v['reproduction_sha256'])
assert v['rejected_count']==18 and len(v['rejected_inputs'])==18 and all(x['rejected']for x in v['rejected_inputs'])
post=read(H/'prepared_hover_ultimate01/post_lock_evidence.json')
for p,h in post['evidence'].items():assert sha(R/p)==h,p;inputs[p]=h
browser=read(H/'hover_ultimate_sequence01/browser_verification.json');assert browser['passed']and browser['calls']==1500 and browser['canvas_checks']==3000
for name in('verify_shibuki_ultimate_hover10_independent01.py','verify_shibuki_ultimate_hurt13_independent.py','finalize_shibuki_ultimate_hover10_independent01.py'):track(D/name)
for name in('scripts/export_x_consistency.py','scripts/discover_inputs.py','scripts/prepare_riko_ui.py','src/psx_player.py','src/psx_static_effect.py','src/psx_ui_atlas.py'):track(R/name)
body_evidence={name:track(PEER/name)for name in('report.json','visual_review.json','READER_LOCK.json')}
shot_art=[H/'hover_ultimate_shot_inputs01/page01/generated_v1.png',H/'hover_ultimate_shot_inputs01/page02/generated_v1.png',H/'hover222_cleanup_inputs01/generated_v1.png']
viewed=[]
for row in report['readback_sheets']:
 assert sha(R/row['path'])==row['sha256'];viewed.append({**row,'actually_viewed':True});track(R/row['path'])
assert len(viewed)==11
visual={
 'candidate_sha256':report['candidate_sha256'],'actually_viewed':True,
 'directly_viewed_final_boards':viewed,'directly_viewed_generated_shot_sources':[track(p)for p in shot_art],
 'body_source_review_by_peer':body_evidence['visual_review.json'],
 'observations':[
  '새 221/229의 두 손 위 자세와 222/230 한 팔 사격 전환이 분명하며, 재추출 5판에서 추가로 확정할 팔/목·발목 절단이나 전신 크기 급변을 찾지 못했다.',
  '222/224의 긴 전완과 총열 사이 어두운 손목은 밝은 바탕에서도 이어진다. 226/228은 굽힌 팔/손을 정본 총 아래로 배치한 형태로 읽히며 총 자체가 별도 떠 있는 확정 결함은 찾지 못했다.',
  '원위치 15제트의 5개 비교판에서 신발과 불꽃의 큰 추가 분리는 찾지 못했다. 229/230 첫 위상12의 두 불꽃 사이 빈 공간은 그대로 보이며 모든 불꽃 면이 매 위상에 발과 붙는다는 주장은 하지 않는다.',
  '원 첫 탄환을 원발생점에 합성한 밝은 판은 총 앞쪽의 점유 관계를 확인하는 정적 진단이다. 중립색 효과이며 게임의 실제 CLUT/블렌딩/움직임 재현은 아니다.',
  '초기 사격 생성 page01의 222 여분 팔은 최종 채택한 그림이 아니다. 별도 cleanup 생성의 두 팔 형태와 최종 국소 마스크 적용을 직접 구분해 보았다.'
 ],
 'limits':['직접 열람은 최종 재추출·제트·총구 11판과 사격 생성원본 3파일이다. 동료가 본 비사격 원화4파일/재구성5판은 별도 관찰로 결속한다.','원게임 실기/60Hz/실제 반투명 CLUT 및 프레임 순서 동영상 열람을 수행하지 않았다.','221 원손 대비 남은1px 높이 차이를 원외곽 exact 복원으로 확대하지 않는다.'],
 'art_or_resource_changed':False,'runtime_verified':False
}
write('visual_review.json',visual)
conclusions={
 'passed':True,'candidate_sha256':report['candidate_sha256'],'parent_sha256':report['parent_sha256'],
 'technical_report':track(O/'report.json'),'visual_review':track(O/'visual_review.json'),'peer_body_source':body_evidence,
 'combined_source_scope':'비사격5+221국소2 =7셀은 별도 독립 reader가 직접 재양자화하고25층을 재구성했다. 사격5+222국소1 =6셀은 본 reader가 직접 재양자화/의미마스크/정본총을 재구성했다. 합13고정셀은 원화13장이나 독립포즈13개를 뜻하지 않는다.',
 'peer_reconstructed25_to_final_targets_checked_here':True,'checks':report['counts'],
 'accepted_storage_and_policy':['상체0/하체5, 빈6/7/8을 유지. 실제 Ultimate 호버는 mask15이고 다른부분조합은 회귀 진단이다.','5개 몸/사격 쌍의 하체5와 공유stream을 유지. 원15jet/6전체타일/30기록 및 첫탄환7의 전체타일/조립은 부모·기존 원US 읽기 근거와 일치한다.','수용34 정본60불투명+11투명 창은 원총구5좌표로 평행 등록했다. 각 옛호버의 총 몸통 픽셀 전체가 그대로라는 뜻은 아니다.','50목표층·320부분·160총구조건·97GPU파트와 502비대상raw/1090층/1741조립을 독립 대조했다. 은행·entry 경계, 팔레트와 음향은 불변이다.'],
 'producer_evidence_checked_without_execution':producer,
 'producer_evidence_scope':'기존 원MIPS10의 실제 디코드 raw해시를 본 reader가 후보와 결속했다. 3회동일빌드/18입력거부 및1500호출/3000canvas 기록은 읽기·해시 결속이며 본 감사에서 제작/재현/브라우저/MIPS를 새 실행한 것이 아니다.',
 'original_source_report_preserved':True,'producer_functions_imported_or_called':False,'source_or_ARC_modified':False,'new_MIPS_execution':False,'runtime_verified':False,
 'remaining':['Root 최종 미술기록과 제작자 근거의 동결 결속은 담당자 단계다.','BIN 통합/실제 새부팅 호버·사격 및 방향/부분상태 실기는 별도다.']
}
write('conclusions.json',conclusions)
track(O/'conclusions.json');track(PEER/'READER_LOCK.json')
for p,h in inputs.items():assert sha(R/p)==h,p
write('READER_LOCK.json',{'files':dict(sorted(inputs.items())),'candidate_sha256':report['candidate_sha256'],'producer_input_lock_unchanged':report['inputs'][rel(H/'prepared_hover_ultimate01/INPUT_LOCK.json')],'no_source_or_resource_writes':True})
print(json.dumps({name:sha(O/name)for name in('report.json','visual_review.json','conclusions.json','READER_LOCK.json')}))
