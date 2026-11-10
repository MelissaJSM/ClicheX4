"""사다리 허용7·루트반동2 동결 및 제한된 실기를 최신 장부로 연결한다."""
from pathlib import Path
import json,hashlib,collections
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rec=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 old=N/'scope_summary_v18/manifest.json';m=read(old);out=N/'scope_summary_v19';out.mkdir(exist_ok=False);history=read(N/'scope_summary_v5/manifest.json')
 l=N/'ultimate_ladder_repaint';p=l/'packed_first7_diagnostic_v1';f=read(p/'FROZEN.json');rp=N.parent/'root_nana_recoil/packed_recoil03';rf=read(rp/'FROZEN.json');assert f['frozen']and rf['frozen']
 held=[148,149,150,151,152,153,155];review=read(N/'ultimate_special_review01/visual_review.json')
 for form,s in m['summary'].items():
  d={q['ref']:q['decision']for q in history['frames'][form]};d.update({q['ref']:q['decision']for q in m['remaining_by_form'][form]})
  for key,decision in [('frozen_full_new_art_refs','repaint_frozen'),('frozen_derived_effect_refs','derived_effect_frozen'),('frozen_mirrored_refs','mirrored_frozen')]:d.update({n:decision for n in s[key]})
  assert dict(collections.Counter(d.values()))==s['reference_decisions']
  if form in('base','fourth'):
   d.update({n:'repaint_frozen'for n in(90,91)});m['remaining_by_form'][form]=[q for q in m['remaining_by_form'][form]if q['ref']not in(90,91)];s['new_source_registered_not_packed_refs']=[]
   for q in m['remaining_by_form'][form]:
    if q['ref']in(133,135,136,137):q['stage']='root_new_art_registered_not_frozen'
  else:
   d.update({n:'repaint_frozen'for n in(143,144,146,154,183)});d.update({n:'mirrored_frozen'for n in(145,147)})
   for q in review['findings']:
    for n in q['refs']:d[n]=q['status']
   remain={q['ref']:q for q in m['remaining_by_form'][form]if q['ref']not in f['refs']}
   for n in(88,89,90,91,95,96,97,98,99):
    remain[n]={'ref':n,'decision':'needs_redraw','stage':'new_source_registered_not_packed'if n in(89,97)else'reviewed_special_details_pending','evidence':rec(N/'ultimate_special_review01/visual_review.json')}
   for n in held:
    remain[n]['stage']='held_unmodified_tool_refusal_no_retry_or_bypass'if n in(149,151,153)else'linked_to_held_body_unmodified'
   m['remaining_by_form'][form]=sorted(remain.values(),key=lambda q:q['ref']);s['new_source_registered_not_packed_refs']=[89,97];s['unaccepted_held_source_refs']=[149,151,153]
  s['reference_decisions']=dict(collections.Counter(d.values()))
  for key,decision in [('frozen_full_new_art_refs','repaint_frozen'),('frozen_derived_effect_refs','derived_effect_frozen'),('frozen_mirrored_refs','mirrored_frozen')]:s[key]=sorted(n for n,v in d.items()if v==decision)
 m['scope']='Ultimate 허용 사다리7과 루트 기본/포스반동2 동결. 사다리 보류7 불변과 다음 Ultimate특수 등록을 분리.';m['previous_immutable_manifest']=rec(old);m['previous_completed_candidate']=m['current_candidate']
 m['current_candidate']={'path':rec(p/'PL02_U.ARC')['path'],'sha256':f['asset_sha256'],'refs':f['refs'],'forms':['ultimate_before','ultimate_after'],'new_body_keys':f['new_authored_body_keys'],'mirrored_refs':[145,147],'frozen':True,'independent_pending':False,'final_root_readback_review_pending':False,'new_gameplay_verified':False,'proofs':[rec(p/'FROZEN.json')]}
 m['preserved_frozen_sources']={'PL00':rec(rp/'PL00_U.ARC'),'PL02':rec(p/'PL02_U.ARC')}
 m['root_recoil2']={'frozen':rec(rp/'FROZEN.json'),'refs':[90,91],'forms':['base','fourth'],'new_body_form_pairs':4,'integration':'RN28','runtime':rec(N.parent/'runtime/nana_fourth_latest28_summary.json'),'runtime_limit':'Root 포스 양방향90/91,138/139 실제463창/8판 검토. 기본/부분폼 전수 실기 아님. 이 장부 작성에서 새 게임 실행하지 않음.'}
 m['root_settle138139_runtime']=rec(N.parent/'runtime/nana_fourth_latest28_summary.json')
 progress={'stage':'ultimate_standing_sources_registered_not_packed','forms':['ultimate_before','ultimate_after'],'new_body_refs':[89,97],'source':rec(N/'ultimate_standing_repaint/a_v1/generated.png'),'registration':rec(N/'ultimate_standing_repaint/first_registered_v1/registration.json'),'native_packed':False,'runtime_verified':False}
 m['current_production']=progress;write(out/'standing_progress_snapshot.json',progress)
 m['ultimate_ladder_first7']={'frozen':rec(p/'FROZEN.json'),'new_body_keys':[143,144,146,154,183],'mirrored_refs':[145,147],'remaining_unmodified_refs':held,'blocked_correction':f['blocked_correction'],'all_ladder_complete':False,'runtime_verified':False}
 m['reviewed_now']=[rec(N/'ultimate_special_review01/visual_review.json')]+[rec(p/f'readback_{i}.png')for i in(1,2,3)]
 for name,key in [('full_new_art','frozen_full_new_art_refs'),('derived_effect','frozen_derived_effect_refs'),('mirrored','frozen_mirrored_refs')]:m[f'frozen_{name}_reference_form_pairs']=sum(len(s[key])for s in m['summary'].values())
 m['frozen_new_art_plus_derived_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs']+m['frozen_derived_effect_reference_form_pairs'];m['all_frozen_reference_form_pairs']=m['frozen_new_art_plus_derived_reference_form_pairs']+m['frozen_mirrored_reference_form_pairs'];assert m['all_frozen_reference_form_pairs']==534
 m['frozen_plus_prepared_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs'];m['frozen_reference_count_unchanged']=False
 m['count_limit']='534는470새아트참조×폼+52효과파생+12반전표시 합계다. 고유원화 수·생성횟수·전체완료율이 아니다. 사다리5몸체×2+2반전×2이며 보류7은 제외.'
 m['parallel_ownership']={'root':'기본/포스등장,통합/실기','overhaul_audio':'Ultimate특수/차량 등 나머지미완료','generation_policy':'한페이지씩공유슬롯순차'}
 m['next_priorities']=['Ultimate89/97 새4몸체 손/정본총/눈/발·전후의상 공통층 정합.','Ultimate88 효과와95→96/98→99 후폼 차이의 역사관계 읽기 후 나머지특수 제작.','사다리149/151/153 도구거부와 연결148/150/152/155 미완료 유지. 재요청/우회하지 않음.','기본/포스 등장·승리귀환 및 전폼차량/hover 잔여 유지. 저체력 실기 발동실패도 유지.']
 m['remaining_classification_origin']='v18를 상속하며 이번 동결2묶음과 실제 열람한Ultimate특수4판만 갱신. 전체모션을 새 전수열람했다고 주장하지 않는다.'
 write(out/'manifest.json',m);print(json.dumps({'sha256':sha(out/'manifest.json'),'full_new_art_reference_forms':m['frozen_full_new_art_reference_form_pairs'],'derived':m['frozen_derived_effect_reference_form_pairs'],'mirrored':m['frozen_mirrored_reference_form_pairs'],'total':m['all_frozen_reference_form_pairs']}))
if __name__=='__main__':main()
