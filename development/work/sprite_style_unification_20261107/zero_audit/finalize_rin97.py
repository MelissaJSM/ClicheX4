"""Freeze the already verified wall follow-up; no art or game writes."""
from pathlib import Path
import hashlib,json,sys
D=Path(__file__).resolve().parent;ROOT=D.parents[2];R=D/'rin_extension'
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
P=R/'prepared_wall_followup_v2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists()
q=json.loads((P/'proposal.json').read_text('utf8'))
plan=json.loads((R/'rin97_components.json').read_text('utf8'))
audit_path=R/'final97_readback_audit.json';audit=json.loads(audit_path.read_text('utf8'))
native_path=R/'rin97_components_native_checks.json';native=json.loads(native_path.read_text('utf8'))
guard_path=R/'rin97_guard_checks.json';guard=json.loads(guard_path.read_text('utf8'))
expected='289370272eb51e377435e3fea0591921f4497fe3774d1f41e1d15d4d76d22ca2'
assert sha(P/'PL01_U.ARC')==q['after_sha256']==audit['candidate_sha256']==expected
assert audit['passed'] and native['passed'] and guard['passed']
assert sha(ROOT/q['source_arc'])==q['source_arc_sha256']=='1a4e16a126b551e5f9d291401a5b9249e66c84aa0252b929b2fd31fa541b143e'
assert plan['source_sha256']==audit['source_bin_sha256'] and plan['resources']['PL01_U.ARC']['before']==audit['source_arc_sha256']
assert sha(ROOT/plan['source_bin'])==plan['source_sha256']
baseline,_=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))
assert hashlib.sha256(baseline['PL01_U.ARC']).hexdigest()==plan['resources']['PL01_U.ARC']['before']
static_result=check_static_body(baseline['PL01_U.ARC'],(P/'PL01_U.ARC').read_bytes(),q['static_body_patch'])
contact={'scope':'정지 이미지에서 눈·장갑·발끝의 위치를 확인했다. 색상 ROI의 무게중심은 물리적 접점이나 실제 게임 충돌점과 같지 않다.',
 'origin':[160,160],'canvas':[384,384],'whole_body_translation_after_generic':[0,0],
 'eye_anchors':{'34':{'before_dark_eye_center':[157,141],'after_cyan':[157,141]},'36':{'before':[156,143],'after':[156,143]},'38':{'before':[150,149],'after':[150,149]},'41':{'before':[156,150],'after':[156,150]}},
 'white_glove_centroids':[{'ref':34,'roi':[141,146,160,158],'before':[148.82,150.91],'after':[148.70,151.63]}, {'ref':36,'roi':[139,134,155,151],'before':[149.52,142.08],'after':[149.51,140.19]}, {'ref':38,'side':'raised_rear','roi':[160,132,175,149],'before':[164.52,142.00],'after':[164.47,141.44]}, {'ref':38,'side':'front','roi':[139,148,150,162],'before':[143.11,151.17],'after':[142.67,151.17]}, {'ref':41,'side':'raised_rear','roi':[163,130,177,150],'before':[168.13,140.94],'after':[168.41,139.86]}, {'ref':41,'side':'front','roi':[138,150,158,166],'before':[148.89,157.63],'after':[148.68,157.75]}],
 'toe_rows':[{'ref':34,'y':176,'before_x':[146,147,148,149,150,151,176,177,178,179],'after_x':[145,146,147,148,149,176,177,178,179,180]}, {'ref':36,'y':182,'before_x':[172,173,174],'after_x':[170,171,172,173,174]}, {'ref':38,'y':189,'before_x':[156,157],'after_x':[156,157]}, {'ref':41,'y':190,'before_x':[173,174,175,176],'after_x':[171,172,173,174,175]}],
 'caveats':['36의 흰 장갑 ROI 무게중심은 약1.9px 위이다. 얼굴·커프가 포함될 수 있어 실제 손 접점이 정확히1.9px 이동했다고 단정하지 않는다.','발끝 최하단 y는 유지하지만 새 신발 외곽의 x폭은 1~2px 다르다. 원래 알파로 새 그림을 강제 자르지 않았다.'],
 'old_head_or_clothes_copied_pixels':0,'runtime_verified':False}
contact_path=R/'wall97_contact_review.json';dump(contact_path,contact)
seen=[]
for form in('normal','black'):
 for n in range(2):
  p=P/f'{form}_readback_{n:02}.png';seen.append({'path':rel(p),'sha256':sha(p),'actually_viewed':True})
visual={'sheets':seen,'scope':'작업 ARC의 일반·레드6표시를 대기와 원래 자세 옆에 놓아 직접 열람했다.','observations':['머리 안쪽 회청색 결, 눈·턱 구분, 커프와 앞치마·치맛단 명암이 새35/39와 이어진다.','38의 접힌 무릎과 41~43의 기울어진 몸은 대기 높이로 늘리지 않았다. 41~43은 같은 그림을 사용한다.','눈의 위치는 원래 기준으로 국소 정합했다. 새 머리를 옛 거친 머리로 덮지 않았고 내부 빈 공간·전경 손의 가림을 따로 처리했다.','목·허리·무릎에서 뚜렷한 끊김은 보이지 않았다. 36의 위로 든 장갑은 원래보다 약간 높게 읽히므로 루트 미술검토와 추후 연속 재생에서 따로 확인한다.'],'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
visual_path=R/'wall97_visual_review.json';dump(visual_path,visual)
audit.update(visual_review_pending=False,visual_review=rel(visual_path),visual_review_sha256=sha(visual_path),contact_review=rel(contact_path),contact_review_sha256=sha(contact_path),root_final_packed_review_pending=True)
dump(audit_path,audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(audit_path),native_report=rel(native_path),guard_report=rel(guard_path),visual_report=rel(visual_path),contact_report=rel(contact_path),ready_for_checkpoint_integration=True,frozen_candidate=True,root_review_pending=True,root_final_packed_review_pending=True,full_art_unification_complete=False)
q['verification']['baseline_static_body_check']=static_result
q['scope']='공중/벽 연결34/36/38/41 새4키와 원래 전체 표시가 같은42/43. 이전91·효과·소리·정적몸체 보존. 정적검사 동결이며 루트 최종 미술검토와 실기는 별도다.'
dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';l=json.loads(lp.read_text('utf8'));assert l['prepared_count']==91
(R/'progress_ledger91_snapshot.json').write_bytes(lp.read_bytes())
l['new_art_prepared_refs']=sorted(set(l['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(l['new_art_prepared_refs'])==97
l['remaining_refs_in_original_audit']=[r for r in l['remaining_refs_in_original_audit']if r not in q['new_art_refs']]
l.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=97,latest_scope=q['scope'],latest_proof='final97_readback_audit.json',latest_native='rin97_components_native_checks.json',next_page=None,next_page_scope='남은 벽37/45/193과 피격135/139·저체력149/152의 서로 다른 원화 및 파생효과를 준비한다.')
dump(lp,l)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'independent_sha256':sha(audit_path),'native_sha256':sha(native_path),'guard_sha256':sha(guard_path),'visual_review_sha256':sha(visual_path),'contact_review_sha256':sha(contact_path),'cumulative_main_refs':97,'incremental_main_refs':6,'new_authored_body_keys':4,'bank0_slack':4226,'bank1_slack':7176,'hidden_global_cleanup':False,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
dump(P/'FROZEN.json',f);print(json.dumps(f))
