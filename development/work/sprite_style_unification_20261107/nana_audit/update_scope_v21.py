"""Ultimate90/91 동결과95/98의 미채택 정합 후보를 구분해 기록한다."""
from pathlib import Path
import json,hashlib,collections
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rec=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 old=N/'scope_summary_v20/manifest.json';m=read(old);out=N/'scope_summary_v21';out.mkdir(exist_ok=False);p=N/'ultimate_recoil_repaint/packed_recoil_candidate_v1';f=read(p/'FROZEN.json');assert f['frozen'] and sha(p/'PL02_U.ARC')==f['asset_sha256']
 for form in('ultimate_before','ultimate_after'):
  s=m['summary'][form];remaining={q['ref']:q for q in m['remaining_by_form'][form]}
  for n in(90,91):
   prev=remaining[n]['decision'];s['reference_decisions'][prev]-=1;s['reference_decisions']['repaint_frozen']+=1;s['frozen_full_new_art_refs'].append(n)
  s['reference_decisions']={k:v for k,v in s['reference_decisions'].items()if v};s['frozen_full_new_art_refs']=sorted(s['frozen_full_new_art_refs']);s['new_source_registered_not_packed_refs']=[95,98]
  m['remaining_by_form'][form]=[q for q in m['remaining_by_form'][form]if q['ref']not in(90,91)]
  for q in m['remaining_by_form'][form]:
   if q['ref']in(95,98):q['stage']='new_geometry_candidate_not_accepted'
 m['scope']='Ultimate90/91 동결.95/98 첫원화 크기이탈 미채택 및 국소원화 정합진단을 분리한다.';m['previous_immutable_manifest']=rec(old);m['previous_completed_candidate']=m['current_candidate']
 m['current_candidate']={'path':rec(p/'PL02_U.ARC')['path'],'sha256':f['asset_sha256'],'refs':[90,91],'forms':['ultimate_before','ultimate_after'],'new_body_keys':[90,91],'derived_effect_refs':[],'frozen':True,'independent_pending':False,'final_root_readback_review_pending':False,'new_gameplay_verified':False,'integration':'RN33 루트 예정, 이 시점 통합 완료 주장 없음','proofs':[rec(p/'FROZEN.json')]};m['preserved_frozen_sources']['PL02']=rec(p/'PL02_U.ARC')
 m['ultimate_standing3']['integration']='RN31 루트 보고: BIN acc363099f0cef3fd3c5804199761127c6e8db07177e5d22f4579216121edc53. 새 실기 관측은 별도.'
 m['ultimate_recoil2']={'frozen':rec(p/'FROZEN.json'),'refs':[90,91],'source_cells':4,'weapon_policy':f['weapon_policy'],'runtime_verified':False}
 q=N/'ultimate_special_finish_repaint';m['current_production']={'stage':'ultimate95_98_geometry_candidate_not_accepted','new_body_refs':[95,98],'future_derived_refs':[96,99],'source':rec(q/'a_v1/generated.png'),'first_registration':rec(q/'first_registered_v1/registration.json'),'first_rejected_floor_delta':{'95':8,'98':5},'new_local_source':rec(q/'geometry_v1/generated.png'),'local_registration':rec(q/'geometry_registered_v1/registration.json'),'position_probe':rec(q/'geometry_position_probe_v1/manifest.json'),'limits':'新원화 상세는 확보했으나 손발·몸길이 최종 정합 미완료. 전체축소/옛몸덮기 없음.','native_packed':False,'runtime_verified':False}
 for name,key in[('full_new_art','frozen_full_new_art_refs'),('derived_effect','frozen_derived_effect_refs'),('mirrored','frozen_mirrored_refs')]:m[f'frozen_{name}_reference_form_pairs']=sum(len(s[key])for s in m['summary'].values())
 m['frozen_new_art_plus_derived_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs']+m['frozen_derived_effect_reference_form_pairs'];m['all_frozen_reference_form_pairs']=m['frozen_new_art_plus_derived_reference_form_pairs']+m['frozen_mirrored_reference_form_pairs'];m['frozen_plus_prepared_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs'];m['frozen_reference_count_unchanged']=False
 m['count_limit']=f"{m['all_frozen_reference_form_pairs']}는 {m['frozen_full_new_art_reference_form_pairs']}새아트참조×폼 + {m['frozen_derived_effect_reference_form_pairs']}효과파생 + {m['frozen_mirrored_reference_form_pairs']}반전표시의 합계다. 고유원화 수·생성횟수·전체완료율이 아니다."
 m['reviewed_now']=[rec(p/'producer_visual_review.json'),rec(N.parent/'root_review_checkpoint130.json')];m['next_priorities']=['Ultimate95/98 새몸체 원점·손발·권총 정합,96/99 X+1 파생 정책 검증.','사다리 보류148/149/150/151/152/153/155 미완료 유지. 도구거부 재요청/우회 안함.','전폼 차량/hover 잔여와 루트 기본/포스 승리귀환 후속 확인. 저체력 실기 발동실패 유지.'];m['remaining_classification_origin']='v20 상속 후 확인된90/91 동결만 추가. 루트 최신 승리 후보는 다음 확정 장부에서 합류하며 전체모션 새전수열람 아님.'
 (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(out/'manifest.json'),'total':m['all_frozen_reference_form_pairs'],'new_art':m['frozen_full_new_art_reference_form_pairs']}))
if __name__=='__main__':main()
