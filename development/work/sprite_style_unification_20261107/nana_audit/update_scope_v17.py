"""귀환3·루트특수4 동결과138/139 새 등록후보를 분리한 스냅샷."""
from pathlib import Path
import json,hashlib,collections
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
def rec(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 old=N/'scope_summary_v16/manifest.json';m=read(old);out=N/'scope_summary_v17';out.mkdir(exist_ok=False)
 history=read(N/'scope_summary_v5/manifest.json');r=N/'ultimate_return_repaint';rp=r/'packed_return_candidate_v1';rf=read(rp/'FROZEN.json');assert rf['frozen']
 sp=N.parent/'root_nana_special/packed_special02';sf=read(sp/'FROZEN.json');assert sf['frozen']
 b=N/'base_settle_repaint'
 for form,s in m['summary'].items():
  d={q['ref']:q['decision']for q in history['frames'][form]};d.update({q['ref']:q['decision']for q in m['remaining_by_form'][form]})
  for key,decision in [('frozen_full_new_art_refs','repaint_frozen'),('frozen_derived_effect_refs','derived_effect_frozen'),('frozen_mirrored_refs','mirrored_frozen')]:d.update({n:decision for n in s[key]})
  assert dict(collections.Counter(d.values()))==s['reference_decisions']
  if form in('base','fourth'):
   added=sf['refs'];d.update({n:'repaint_frozen'for n in added});s['new_source_registered_not_packed_refs']=[138]
  else:
   added=rf['refs'];d[156]='repaint_frozen';d.update({n:'derived_effect_frozen'for n in(157,158)});s['new_source_registered_not_packed_refs']=[]
  s['reference_decisions']=dict(collections.Counter(d.values()))
  for key,decision in [('frozen_full_new_art_refs','repaint_frozen'),('frozen_derived_effect_refs','derived_effect_frozen'),('frozen_mirrored_refs','mirrored_frozen')]:s[key]=sorted(n for n,v in d.items()if v==decision)
  m['remaining_by_form'][form]=[q for q in m['remaining_by_form'][form]if q['ref']not in added]
  for q in m['remaining_by_form'][form]:
   if form in('base','fourth')and q['ref']in(138,139):q['stage']='new138_source_registered_139_yminus1_pending_common_layers'
   elif form in('base','fourth')and q['ref']in(88,89,97):q['stage']='root_standing_art_registration_pending'
 m['scope']='Ultimate 귀환3 및 루트 기본/포스 특수4 동결 반영.138/139는 새 원화 등록후보이며 전체 미술완료가 아니다.'
 m['previous_immutable_manifest']=rec(old);m['previous_completed_candidate']=m['current_candidate'];m['current_candidate']={'path':rec(rp/'PL02_U.ARC')['path'],'sha256':rf['asset_sha256'],'refs':rf['refs'],'forms':['ultimate_before','ultimate_after'],'new_body_keys':[156],'linked_body_effect_refs':[157,158],'frozen':True,'independent_pending':False,'final_root_readback_review_pending':False,'new_gameplay_verified':False,'proofs':[rec(rp/'FROZEN.json')]}
 m['preserved_frozen_sources']={'PL00':rec(sp/'PL00_U.ARC'),'PL02':rec(rp/'PL02_U.ARC')}
 m['root_special4']={'frozen':rec(sp/'FROZEN.json'),'refs':sf['refs'],'forms':['base','fourth'],'new_body_keys':[95,98],'translated_refs':{'96':{'source':95,'translation':[1,0]},'99':{'source':98,'translation':[1,0]}},'integration':'RN24 통합은 루트 보고.실기 미완료.','new_gameplay_verified':False}
 progress={'stage':'new138_body_fixed_registration_candidate','forms':['base','fourth'],'new_body_refs':[138],'planned_linked_refs':[139],'relation':'모든5층에서139=138 y−1을부모직접대조.새원화는138 한자세×2의상.','proofs':[rec(b/'body_v1/generation.json'),rec(b/'body_registered_v1/registration.json')],'native_packed':False,'runtime_verified':False,'final_packing_parent':'루트89/97 후속 PL00 동결 후 합류.현재 원화용 부모509는 게임최신본으로 오해하지 않음.'}
 m['current_production']=progress;write(out/'settle_progress_snapshot.json',progress)
 write(r/'production_status.json',{'frozen':True,'frozen_file':rec(rp/'FROZEN.json'),'asset_sha256':rf['asset_sha256'],'refs':rf['refs'],'source_pages':2,'distinct_body_keys':1,'costume_displays':2,'derived_body_effect_refs':[157,158],'native_cycle_canvas':66,'runtime_verified':False,'next_priority':rec(out/'settle_progress_snapshot.json')})
 m['reviewed_now']=[rec(rp/f'readback_{i}.png')for i in(1,2,3)]+[rec(r/f'native_cycle_v1/timeline_{i}.png')for i in(39,40)]+[rec(b/'body_registered_v1/comparison.png')]
 for name,key in [('full_new_art','frozen_full_new_art_refs'),('derived_effect','frozen_derived_effect_refs'),('mirrored','frozen_mirrored_refs')]:m[f'frozen_{name}_reference_form_pairs']=sum(len(s[key])for s in m['summary'].values())
 m['frozen_new_art_plus_derived_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs']+m['frozen_derived_effect_reference_form_pairs'];m['all_frozen_reference_form_pairs']=m['frozen_new_art_plus_derived_reference_form_pairs']+m['frozen_mirrored_reference_form_pairs'];assert m['all_frozen_reference_form_pairs']==506
 m['frozen_plus_prepared_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs'];m['frozen_reference_count_unchanged']=False
 m['count_limit']='참조×폼 표시 수이며 고유 원화 수/생성 횟수/품질 완료율이 아니다.특수96/99는95/98 이동파생이고 귀환157/158은156 효과파생이다.'
 m['parallel_ownership']={'root':'기본/포스89/97 및88공유,통합/실기','overhaul_audio':'기본/포스138139 우선,이후Ultimate사다리·잔여','generation_policy':'한 캐릭터 한 페이지씩 공유 슬롯 순차'}
 m['next_priorities']=['기본/포스138 새머리·권총·공통부 정합과139 y−1 전개 후 최신PL00에패킹.','Ultimate 사다리·95..99·85..92·차량/hover 및 기본/포스 등장승리귀환 후속.','RN22 저체력 실기 발동 미완료 유지.귀환실기는RN25통합 뒤루트 담당.']
 m['remaining_classification_origin']='이전v16 결정을 상속하고귀환3/루트특수4만동결갱신.나머지전체모션을새로직접열람했다고주장하지않음.'
 write(out/'manifest.json',m);print(json.dumps({'sha256':sha(out/'manifest.json'),'new_reference_forms':m['frozen_full_new_art_reference_form_pairs'],'derived':m['frozen_derived_effect_reference_form_pairs'],'mirrored':m['frozen_mirrored_reference_form_pairs'],'total':m['all_frozen_reference_form_pairs']}))
if __name__=='__main__':main()
