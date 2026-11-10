from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;U=W/'nana_audit/base_nova_repaint';O=D/'nana_base_nova6_independent01';P=U/'packed_nova_candidate_v1'
sha=lambda b:hashlib.sha256(b).hexdigest();tracked={}
def read(p):
 b=p.read_bytes();tracked[p.relative_to(R).as_posix()]=sha(b);return b
def js(p):return json.loads(read(p))
rep=js(O/'report.json');assert rep['passed'];tracked.update(rep['inputs'])
for p,h in rep['inputs'].items():assert sha((R/p).read_bytes())==h,p
for row in rep['readback_sheets']:assert sha(read(R/row['path']))==row['sha256']
root=js(W/'root_review_checkpoint156.json');assert root['candidate_sha256']==rep['candidate_sha256']
for row in root['actually_viewed_files']:assert sha(read(R/row['path']))==row['sha256']
repro=js(P/'reproduction.json');assert repro['passed']and repro['candidate_sha256']==rep['candidate_sha256']and len(repro['rejected_cases'])==9 and all(r['rejected']for r in repro['rejected_cases'])
cycle=js(U/'native_cycle_v1/verification.json');assert cycle['passed']and cycle['candidate_arc_sha256']==rep['candidate_sha256']and cycle['canvas_native_checks']==48
for p in(D/'verify_nana_base_nova6_independent01.py',D/'verify_shibuki_ultimate_hurt13_independent.py',Path(__file__),R/'scripts/export_x_consistency.py',R/'src/psx_player.py',R/'src/psx_ui_atlas.py',D/'nana_base_nova214_relations01/report.json',D/'nana_base_nova214_relations01/conclusions.json'):read(p)
visual={'actually_viewed':True,'candidate_sha256':rep['candidate_sha256'],'images':rep['readback_sheets'],'actual_images':5,'observations':['최종ARC에서 독립 재추출한3비교판을 실제 보았다.213/215의 새머릿결·베레/포스베일·올린손/팔목·기본부츠/포스맨다리와작은신발 세부가 이전 넓은 단색 면보다 명확하다. 추가 확정 절단이나 큰 체격 변화는 찾지 못했다.','214의 얼굴앞/머리위 분홍은 원US 외부효과124셀로 별도 검증한 요소다.새 손이나 새머리 조각으로 재분류하지 않았으며 동일위치 원효과가 새몸 앞을 가리는 방향을 확인했다.','최종준비 부분판 mask1/2/4/8/15 두행을 보았다.큰뒤베일은head5가아닌leg8과함께표시되며 완성포스의머리·치맛단·베일 연결에 추가확정분리를찾지못했다.초기common_v1의큰head5판을최종부분근거로대체하지않았다.','217/220 새접힌팔·머리·베일·부츠/맨다리가원효과와이어진다.217부분판에서는팔목/어깨의추가확정단절을찾지못했으며220외부에너지형상과새몸가림을구분해보았다.'],'new_confirmed_defect':False,'limitations':['정적 최종5판이며 실제 게임·60Hz·모든부분192조합의 시각전수 검토는 아니다.','초기common_v1 등5판의앞선의견은최종소유변경검사와구분한다.','Root156의9판 실제열람은루트근거로분리결속하며이검토5판에합산하지않는다.']}
evidence={'passed':True,'candidate_sha256':rep['candidate_sha256'],'independent_report_sha256':sha((O/'report.json').read_bytes()),'source_reconstruction':'생성2장6고정셀 전체96canvas 면적투표를 직접 재양자화.새공통손/얼굴창·213부츠65셀Y-1·준비하체57/돌진11같은행표본·소유마스크·베일84/58셀head5→leg8을재구성해30목표/최종ARC exact.제작함수미호출.','effects':'원US214외부124셀을독립ARC에서직접얻고부모5층파생재현후새213에합성/아머차폐.216=215.217양폼새몸Manhattan1.220부모몸+1영역799셀의envelope9복원후새몸+1;외부2708효과중새몸이가리는영역은변경이며전체FXraw보존아님.218/219모든raw/층/조립불변.','storage':'508raw502비대상·1110층·1757조립·192대상부분/114GPU·4원공유stream/대상32tile·은행/entry/팔레트/비대상exact.','producer_evidence_only':{'native6_decode_hashes_bound_not_reexecuted':True,'reproduction1_rejections9_read_not_rerun':True,'original_sequence106_browser48_read_not_rerun':True,'producer_full_RGBA7296_not_independent_fullRGBA_execution':True,'root156_art_review_bound':True},'resources_modified':False,'runtime_verified':False,'overall_complete':False}
assert rep['effect220']['removed_oldbody_region_pixels']==799 and rep['effect220']['parent_external_effect_pixels']==2708
for name,z in [('visual_review.json',visual),('evidence.json',evidence)]:
 p=O/name;assert not p.exists();p.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf8');read(p)
p=O/'READER_LOCK.json';assert not p.exists();p.write_text(json.dumps({'scope':'독립reader/출처/기술/최종5판실제열람결속.후보FROZEN아님','files':tracked},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({n:sha((O/n).read_bytes())for n in('report.json','visual_review.json','evidence.json','READER_LOCK.json')}))
