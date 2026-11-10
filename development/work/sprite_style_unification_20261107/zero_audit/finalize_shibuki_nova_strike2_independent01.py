from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';O=D/'shibuki_nova_strike2_independent02';P=H/'prepared_nova_strike_base01'
sha=lambda b:hashlib.sha256(b).hexdigest();tracked={}
def read(p):
 b=p.read_bytes();tracked[p.relative_to(R).as_posix()]=sha(b);return b
def js(p):return json.loads(read(p))
rep=js(O/'report.json');assert rep['passed'];tracked.update(rep['inputs'])
for p,h in rep['inputs'].items():assert sha((R/p).read_bytes())==h,p
for row in rep['readback_sheets']:assert sha(read(R/row['path']))==row['sha256']
post=js(P/'post_lock_evidence.json')
for p,h in post['files'].items():assert sha(read(R/p))==h,p
root=js(W/'root_review_checkpoint152.json');assert root['candidate_sha256']==rep['candidate_sha256']
v=js(P/'verification.json');assert v['rejected_count']==17
native=js(D/'shibuki_nova_strike2_renderer_native02/conclusions.json');assert native['passed']
for p in (D/'verify_shibuki_nova_strike2_independent01.py',D/'verify_shibuki_ultimate_hurt13_independent.py',Path(__file__),R/'scripts/export_x_consistency.py',R/'src/psx_player.py',R/'src/psx_ui_atlas.py',D/'shibuki_nova_strike2_renderer_native02/READER_LOCK.json'):read(p)
visual={'actually_viewed':True,'candidate_sha256':rep['candidate_sha256'],'images':rep['readback_sheets'],'actual_images':5,'observations':['독립 재추출 기본/포스 두 비교판에서 새217의 머릿결·리본·접힌 팔과 허리/부츠 세부가 이어진다. 이전 넓은 단색 면보다 명암과 의상 경계가 분명하다.','독립217/220 부분판의 mask0/1/2/4/8/15를 실제 열람했고 새 팔목·허리·발목의 추가 확정 단절을 찾지 못했다. 나머지16mask×2arm 전수64조합은 픽셀검사 범위로 구분한다.','220 효과·새몸·최종합성 분리판에서 원래 넓은 효과 바깥 형상과 새몸 앞그리기 관계를 확인했다. 새몸 안에 예전 머리의 밝은 점선/옛몸 면이 남아 있는 추가 확정 문제는 찾지 못했다.'],'limitations':['정적5판 의견이며 실제 게임·60Hz·모든 부분 조합의 시각전수 열람은 아니다.','Root152의 원순서4판은 루트의 관찰 근거이며 이 독립 시각5판에 합산하지 않는다.','원효과와 새몸 가림 변화는 신규 제작정책이며 과거 가림을 픽셀 전부 보존한 것은 아니다.'],'new_confirmed_defect':False}
ev={'passed':True,'candidate_sha256':rep['candidate_sha256'],'independent_report_sha256':sha((O/'report.json').read_bytes()),'original_source_reconstruction':'생성3고정셀을 직접 재양자화하고 부츠X+1 국소등록/공통머리손/부분소유/Manhattan1 외곽/원220색상매핑을 직접 재구성해10층과실제ARC exact 확인. 제작함수 미호출.','original_effect_preservation':'원220의24records 및18전체256nibble 타일은 색인매핑 후exact. 원body를그리는7records뒤가아니라 원효과24뒤새body7 순서.218/219 raw·5층·records exact.','storage':'6참조의2공유stream 64전체타일 역순열과30층 records번호 변환만 확인. 표시/부분RGBA 불변.','native_scope':{'directory508':'독립 actual loader→scratchpad→directory→obj+38/+3c→decode/upload 보고9c09ad41에 결속','renderer':'원본 본체/부분renderer+수용PL00wrapper의136조건2회·경계8조건은별도04f4007c/4ca93a07에결속','memory_observer_diagnostic':'6182e769 실패는7파트에도발생하는hook영향 진단이며후보실패로세지않음','GPU_rasterization_or_game':False},'producer_evidence_only':{'reproduction_and_17_rejections_read_not_rerun':True,'original_sequence_13_steps_and_browser_200':'고정post_lock_evidence의3440f6e7/e95d31c7를연결; 독립새브라우저실행아님','root152_static_art_review':'루트8판실제열람기록을해시결속; 내열람5판과분리'},'initial_visual_crop_attempt':'independent01은그림절단방지가드에서중단되어완성보고서없음. 효과왼쪽끝bbox112를포함하는독립02로재작성했으며이전출력덮기없음.','resources_modified':False,'runtime_verified':False}
for name,z in [('visual_review.json',visual),('evidence.json',ev)]:
 p=O/name;assert not p.exists();p.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf8');read(p)
p=O/'READER_LOCK.json';assert not p.exists();p.write_text(json.dumps({'scope':'독립reader·출처·실제열람·별도원실행결속. 후보FROZEN아님','files':tracked},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({n:sha((O/n).read_bytes())for n in('report.json','visual_review.json','evidence.json','READER_LOCK.json')}))
