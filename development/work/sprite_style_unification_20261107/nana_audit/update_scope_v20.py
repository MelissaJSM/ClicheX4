"""Ultimate 특수3와 루트 기본/포스 등장7의 동결을 잔여 장부에 반영한다."""
from pathlib import Path
import json,hashlib,collections
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rec=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 old=N/'scope_summary_v19/manifest.json';m=read(old);history=read(N/'scope_summary_v5/manifest.json');out=N/'scope_summary_v20';assert not out.exists()or not any(out.iterdir());out.mkdir(exist_ok=True)
 p=N/'ultimate_standing_repaint/packed_standing_candidate_v1';f=read(p/'FROZEN.json');rp=N.parent/'root_nana_arrival/packed_arrival01';rf=read(rp/'FROZEN.json');assert f['frozen']and rf['frozen'];assert sha(p/'PL02_U.ARC')==f['asset_sha256']and sha(rp/'PL00_U.ARC')==rf['candidate_sha256']
 for form,s in m['summary'].items():
  d={q['ref']:q['decision']for q in history['frames'][form]};d.update({q['ref']:q['decision']for q in m['remaining_by_form'][form]})
  for key,decision in[('frozen_full_new_art_refs','repaint_frozen'),('frozen_derived_effect_refs','derived_effect_frozen'),('frozen_mirrored_refs','mirrored_frozen')]:d.update({n:decision for n in s[key]})
  if form in('ultimate_before','ultimate_after'):
   for q in read(N/'ultimate_special_review01/visual_review.json')['findings']:
    if q['status']=='preserve_reviewed':
     d.update({n:q['status']for n in q['refs']})
     for r in m['remaining_by_form'][form]:
      if r['ref']in q['refs']:r.update({'decision':'preserve_reviewed','stage':'reviewed_existing_detail_preserved','evidence':rec(N/'ultimate_special_review01/visual_review.json')})
  assert dict(collections.Counter(d.values()))==s['reference_decisions']
  bodies=(133,135,136,137)if form in('base','fourth')else(89,97);effects=(130,131,134)if form in('base','fourth')else(88,)
  d.update({n:'repaint_frozen'for n in bodies});d.update({n:'derived_effect_frozen'for n in effects});m['remaining_by_form'][form]=[q for q in m['remaining_by_form'][form]if q['ref']not in(*bodies,*effects)]
  if form in('ultimate_before','ultimate_after'):
   s['new_source_registered_not_packed_refs']=[90,91]
   for q in m['remaining_by_form'][form]:
    if q['ref']in(90,91):q['stage']='new_source_common_layers_candidate_not_packed'
  s['reference_decisions']=dict(collections.Counter(d.values()))
  for key,decision in[('frozen_full_new_art_refs','repaint_frozen'),('frozen_derived_effect_refs','derived_effect_frozen'),('frozen_mirrored_refs','mirrored_frozen')]:s[key]=sorted(n for n,v in d.items()if v==decision)
 m['scope']='Ultimate 특수88/89/97 동결과 루트 기본/포스 등장7 동결. 다음90/91 등록후보·사다리 보류7을 구분.';m['previous_immutable_manifest']=rec(old);m['previous_completed_candidate']=m['current_candidate']
 m['current_candidate']={'path':rec(p/'PL02_U.ARC')['path'],'sha256':f['asset_sha256'],'refs':[88,89,97],'forms':['ultimate_before','ultimate_after'],'new_body_keys':[89,97],'derived_effect_refs':[88],'frozen':True,'independent_pending':False,'final_root_readback_review_pending':False,'new_gameplay_verified':False,'integration':'RN31 예정, 이 장부 작성에서 통합 완료를 주장하지 않음','proofs':[rec(p/'FROZEN.json')]}
 m['preserved_frozen_sources']={'PL00':rec(rp/'PL00_U.ARC'),'PL02':rec(p/'PL02_U.ARC')};m['root_arrival7']={'frozen':rec(rp/'FROZEN.json'),'new_body_keys':[133,135,136,137],'derived_effect_refs':[130,131,134],'forms':['base','fourth'],'integration':'RN30 루트 보고','runtime_verified':False,'scope':'새몸체8셀+원에너지/구체파생3참조×2폼. 이번장부에서 그림/실기 새전수열람은 하지 않음.'}
 m['root_standing3']['derived_ref88']='새89 몸체 X−1,Y불변과 원효과83texel';m['prior_text_correction']=rec(N/'scope_summary_v19/clarification.json')
 progress={'stage':'ultimate_recoil_common_candidate_not_packed','forms':['ultimate_before','ultimate_after'],'new_body_refs':[90,91],'source':rec(N/'ultimate_recoil_repaint/a_v1/generated.png'),'registration':rec(N/'ultimate_recoil_repaint/first_registered_v1/registration.json'),'common':rec(N/'ultimate_recoil_repaint/common_probe_v2/manifest.json'),'native_packed':False,'runtime_verified':False};m['current_production']=progress;write(out/'recoil_progress_snapshot.json',progress)
 m['ultimate_standing3']={'frozen':rec(p/'FROZEN.json'),'refs':[88,89,97],'new_body_keys':[89,97],'derived_effect_refs':[88],'actual_body_source_cells':4,'effect_policy':f['effect_policy'],'runtime_verified':False}
 for name,key in[('full_new_art','frozen_full_new_art_refs'),('derived_effect','frozen_derived_effect_refs'),('mirrored','frozen_mirrored_refs')]:m[f'frozen_{name}_reference_form_pairs']=sum(len(s[key])for s in m['summary'].values())
 m['frozen_new_art_plus_derived_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs']+m['frozen_derived_effect_reference_form_pairs'];m['all_frozen_reference_form_pairs']=m['frozen_new_art_plus_derived_reference_form_pairs']+m['frozen_mirrored_reference_form_pairs'];m['frozen_plus_prepared_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs'];m['frozen_reference_count_unchanged']=False
 m['count_limit']=f"{m['all_frozen_reference_form_pairs']}는 {m['frozen_full_new_art_reference_form_pairs']}새아트참조×폼 + {m['frozen_derived_effect_reference_form_pairs']}효과파생 + {m['frozen_mirrored_reference_form_pairs']}반전표시의 합계다. 고유원화 수·생성횟수·전체완료율이 아니다."
 m['reviewed_now']=[rec(p/'producer_visual_review.json'),rec(N.parent/'root_review_checkpoint128.json')]
 m['parallel_ownership']={'root':'기본/포스 승리귀환·통합/실기','overhaul_audio':'Ultimate90/91·95/96·98/99 및차량 등 잔여','generation_policy':'한페이지씩 공유슬롯 순차'}
 m['next_priorities']=['Ultimate90/91 새원화4의 맨팔/소매경계와 정본91총·공통층을 검토하고 별도패킹.','Ultimate95/98 독립원화와96/99의 새공통X+1관계,원총구/효과검토.','사다리149/151/153 도구거부와연결148/150/152/155 미완료유지. 재요청/우회안함.','기본/포스 승리귀환 및 전폼차량/hover 잔여 유지. 저체력 실기 발동실패 유지.'];m['remaining_classification_origin']='v19를 상속하고 확인된 두 동결묶음만 최신화했다. 전체모션 새전수열람 아님.'
 write(out/'manifest.json',m);print(json.dumps({'sha256':sha(out/'manifest.json'),'new_art':m['frozen_full_new_art_reference_form_pairs'],'derived':m['frozen_derived_effect_reference_form_pairs'],'mirrored':m['frozen_mirrored_reference_form_pairs'],'total':m['all_frozen_reference_form_pairs']}))
if __name__=='__main__':main()
