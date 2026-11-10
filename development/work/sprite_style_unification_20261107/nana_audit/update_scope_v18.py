"""기본/포스standing3·138139 동결과 Ultimate사다리 제작 상태를 구분한다."""
from pathlib import Path
import json,hashlib,collections
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
def rec(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 old=N/'scope_summary_v17/manifest.json';m=read(old);out=N/'scope_summary_v18';out.mkdir(exist_ok=False);history=read(N/'scope_summary_v5/manifest.json');b=N/'base_settle_repaint';bp=b/'packed_settle_candidate_v1';bf=read(bp/'FROZEN.json');sp=N.parent/'root_nana_standing/packed_standing03';sf=read(sp/'FROZEN.json');assert bf['frozen']and sf['frozen'];l=N/'ultimate_ladder_repaint'
 for form,s in m['summary'].items():
  d={q['ref']:q['decision']for q in history['frames'][form]};d.update({q['ref']:q['decision']for q in m['remaining_by_form'][form]})
  for key,decision in [('frozen_full_new_art_refs','repaint_frozen'),('frozen_derived_effect_refs','derived_effect_frozen'),('frozen_mirrored_refs','mirrored_frozen')]:d.update({n:decision for n in s[key]})
  assert dict(collections.Counter(d.values()))==s['reference_decisions']
  if form in('base','fourth'):
   d.update({n:'repaint_frozen'for n in(89,97,138,139)});d[88]='derived_effect_frozen';m['remaining_by_form'][form]=[q for q in m['remaining_by_form'][form]if q['ref']not in(88,89,97,138,139)];s['new_source_registered_not_packed_refs']=[]
   for q in m['remaining_by_form'][form]:
    if q['ref']in(90,91):q['stage']='root_new_art_registered_pending_final_settle_parent'
  else:
   s['new_source_registered_not_packed_refs']=[143,144,146,149,151,153]
   for q in m['remaining_by_form'][form]:
    if q['ref']in(143,144,146,149,151,153):q['stage']='new_body_sources_registered_costume_contacts_common_layers_pending'
  s['reference_decisions']=dict(collections.Counter(d.values()))
  for key,decision in [('frozen_full_new_art_refs','repaint_frozen'),('frozen_derived_effect_refs','derived_effect_frozen'),('frozen_mirrored_refs','mirrored_frozen')]:s[key]=sorted(n for n,v in d.items()if v==decision)
 m['scope']='기본/포스standing3 및138139 동결 갱신. Ultimate사다리 새6고유몸체×전후 원화는 등록후보이며 완료수에 넣지 않는다.';m['previous_immutable_manifest']=rec(old);m['previous_completed_candidate']=m['current_candidate']
 m['current_candidate']={'path':rec(bp/'PL00_U.ARC')['path'],'sha256':bf['asset_sha256'],'refs':[138,139],'forms':['base','fourth'],'new_body_keys':[138],'translated_refs':{'139':{'source':138,'translation':[0,-1]}},'frozen':True,'independent_pending':False,'final_root_readback_review_pending':False,'new_gameplay_verified':False,'proofs':[rec(bp/'FROZEN.json')]}
 m['preserved_frozen_sources']={'PL00':rec(bp/'PL00_U.ARC'),'PL02':rec(N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC')}
 m['root_standing3']={'frozen':rec(sp/'FROZEN.json'),'refs':[88,89,97],'forms':['base','fourth'],'new_body_keys':[89,97],'derived_ref88':'새89 몸체 y−1과 기존효과83texel. 독립 새전신으로 세지 않는다.','integration':'루트 RN26 통합 보고. 실기관측은 루트 별도증거와 연결한다.','new_gameplay_verified_here':False}
 progress={'stage':'ultimate_ladder_sources_registered_not_packed','forms':['ultimate_before','ultimate_after'],'new_body_refs':[143,144,146,149,151,153],'remaining_body_refs':[154,183],'firing_arm_refs':[150,155],'mirrored_refs_pending':[145,147,148,152],'proofs':[rec(l/'a_registered_v1/registration.json'),rec(l/'a_arm_registered_v1/manifest.json'),rec(l/'b_registered_v1/registration.json')],'unaccepted':['첫페이지 후폼 높은팔 분홍소매는 새 국소팔로 수정했으나 공통부·원접점 검증은 미완료.','후속149/151/153 후폼 하의가 흰반바지로 생성돼 의상색/경계 국소교정 전 미채택.'],'native_packed':False,'runtime_verified':False}
 m['current_production']=progress;write(out/'ladder_progress_snapshot.json',progress)
 m['reviewed_now']=[rec(bp/'readback.png')]+[rec(b/f'native_cycle_v1/timeline_{i}.png')for i in(2,95,96)]+[rec(l/f'b_registered_v1/comparison_{i}.png')for i in(149,151,153)]
 for name,key in [('full_new_art','frozen_full_new_art_refs'),('derived_effect','frozen_derived_effect_refs'),('mirrored','frozen_mirrored_refs')]:m[f'frozen_{name}_reference_form_pairs']=sum(len(s[key])for s in m['summary'].values())
 m['frozen_new_art_plus_derived_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs']+m['frozen_derived_effect_reference_form_pairs'];m['all_frozen_reference_form_pairs']=m['frozen_new_art_plus_derived_reference_form_pairs']+m['frozen_mirrored_reference_form_pairs'];assert m['all_frozen_reference_form_pairs']==516
 m['frozen_plus_prepared_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs'];m['frozen_reference_count_unchanged']=False
 m['count_limit']='참조×폼 표시 수이며 고유원화/생성횟수/전체완료율이 아니다.138 한자세×2와139 y−1×2를 분리 기록.88은89+효과이며 Ultimate사다리12등록표시는 동결수에서 제외.'
 m['parallel_ownership']={'root':'기본/포스90/91 후속,통합/실기','overhaul_audio':'Ultimate사다리 및 나머지 미완료','generation_policy':'공유슬롯 한페이지씩 순차'}
 m['next_priorities']=['Ultimate사다리149/151/153 후폼 하의 국소교정, 남은154/183·150/155와 공통층/손발 검증.','기본/포스 등장133..137/승리귀환 및 Ultimate95..99/85..92/차량·hover 잔여 유지.','RN22 저체력 실기 발동실패와 새138139실기미완료 구분 유지.']
 m['remaining_classification_origin']='기존v17판단을 상속하고 동결standing3·138139만 갱신. 나머지 전체모션을 새로 전수열람했다는 뜻이 아니다.'
 write(out/'manifest.json',m);print(json.dumps({'sha256':sha(out/'manifest.json'),'full_new_art_reference_forms':m['frozen_full_new_art_reference_form_pairs'],'derived':m['frozen_derived_effect_reference_form_pairs'],'mirrored':m['frozen_mirrored_reference_form_pairs'],'total':m['all_frozen_reference_form_pairs']}))
if __name__=='__main__':main()
