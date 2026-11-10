"""등장10·루트 사다리14 동결을 원화/파생/반전으로 나눠 기록한다."""
from pathlib import Path
import json,hashlib,collections
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
def rec(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 old=N/'scope_summary_v14/manifest.json';m=read(old);out=N/'scope_summary_v15';assert not out.exists();out.mkdir()
 history=read(N/'scope_summary_v5/manifest.json');c=N/'ultimate_ceremony_repaint';p=c/'packed_arrival_candidate_v1';f=read(p/'FROZEN.json');assert f['frozen']
 ladder=ROOT/'work/sprite_style_unification_20261107/root_nana_ladder/packed_ladder07';lf=read(ladder/'FROZEN.json');assert lf['frozen']
 newladder=[143,144,146,149,150,151,153,154,155,183];mirrors=[145,147,148,152]
 for form,summary in m['summary'].items():
  d={q['ref']:q['decision']for q in history['frames'][form]};d.update({q['ref']:q['decision']for q in m['remaining_by_form'][form]})
  d.update({n:'repaint_frozen'for n in summary['frozen_full_new_art_refs']});d.update({n:'derived_effect_frozen'for n in summary['frozen_derived_effect_refs']})
  assert dict(collections.Counter(d.values()))==summary['reference_decisions']
  if form in('base','fourth'):
   added,linked,mirror=newladder,[],mirrors
  else:added,linked,mirror=f['new_authored_body_keys'],f['derived_body_effect_refs'],[]
  d.update({n:'repaint_frozen'for n in added});d.update({n:'derived_effect_frozen'for n in linked});d.update({n:'mirrored_frozen'for n in mirror})
  summary['reference_decisions']=dict(collections.Counter(d.values()));summary['frozen_full_new_art_refs']=sorted(n for n,v in d.items()if v=='repaint_frozen');summary['frozen_derived_effect_refs']=sorted(n for n,v in d.items()if v=='derived_effect_frozen');summary['frozen_mirrored_refs']=sorted(n for n,v in d.items()if v=='mirrored_frozen')
  summary['new_source_registered_not_packed_refs']=[204,205]if form.startswith('ultimate')else[]
  changed=set(added+linked+mirror);m['remaining_by_form'][form]=[q for q in m['remaining_by_form'][form]if q['ref']not in changed]
  for q in m['remaining_by_form'][form]:
   if form.startswith('ultimate')and q['ref']in(204,205):q['stage']='new_source_fixed_registration_candidate_not_packed'
 m['previous_immutable_manifest']=rec(old);m['scope']='Ultimate 등장10과 루트 기본/포스 사다리14의 동결 반영. 새원화/효과연동/반전 참조를 분리하고 전체 완료율은 산출하지 않음.'
 m['previous_completed_candidate']=m['current_candidate'];m['current_candidate']={'path':rec(p/'PL02_U.ARC')['path'],'sha256':f['asset_sha256'],'refs':f['refs'],'forms':['ultimate_before','ultimate_after'],'new_body_keys':f['new_authored_body_keys'],'linked_body_effect_refs':f['derived_body_effect_refs'],'frozen':True,'independent_pending':False,'final_root_readback_review_pending':False,'new_gameplay_verified':False,'proofs':[rec(p/'FROZEN.json')]}
 m['preserved_frozen_sources']={'PL00':rec(ladder/'PL00_U.ARC'),'PL02':rec(p/'PL02_U.ARC')}
 m['root_ladder14']={'frozen':rec(ladder/'FROZEN.json'),'new_body_keys':[143,144,146,149,151,153,154,183],'new_firing_arm_keys':[150,155],'mirrored_refs':mirrors,'forms':['base','fourth'],'integration':'루트 RN20 통합 보고. 이 장부 갱신은 실기를 새로 수행하지 않음.','runtime_verified_here':False}
 snapshot=out/'ceremony_progress_snapshot.json';snapshot.write_bytes((c/'production_status.json').read_bytes())
 m['current_production']={'forms':['ultimate_before','ultimate_after'],'refs':[204,205,206,207],'registered_refs':[204,205],'stage':'first_two_keys_fixed_native_registration','progress':[rec(N/'ultimate_victory_repaint/a_v1/generation.json'),rec(N/'ultimate_victory_repaint/a_registered_v1/registration.json')],'native_prepared_arc':None,'gesture_policy':'204 가슴 손과205 빈손 경례 유지,206 뺨옆 권총/207 머리위 권총 후속. 원화 생성 수를 완료수에 넣지 않음.'}
 m['reviewed_now']=[rec(p/f'readback_{i}.png')for i in range(1,6)]+[rec(c/f'native_cycle_v1/timeline_{i}.png')for i in(2,95,96)]+[rec(N/f'ultimate_victory_repaint/a_registered_v1/comparison_{i}.png')for i in(1,2)]
 m['frozen_full_new_art_reference_form_pairs']=sum(len(s['frozen_full_new_art_refs'])for s in m['summary'].values());m['frozen_derived_effect_reference_form_pairs']=sum(len(s['frozen_derived_effect_refs'])for s in m['summary'].values());m['frozen_mirrored_reference_form_pairs']=sum(len(s['frozen_mirrored_refs'])for s in m['summary'].values())
 m['frozen_new_art_plus_derived_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs']+m['frozen_derived_effect_reference_form_pairs'];m['all_frozen_reference_form_pairs']=m['frozen_new_art_plus_derived_reference_form_pairs']+m['frozen_mirrored_reference_form_pairs'];assert m['all_frozen_reference_form_pairs']==472
 m['frozen_plus_prepared_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs'];m['frozen_reference_count_unchanged']=False
 m['units']='한 참조×한 의상 표시 항목. full_new_art는 새 전신/새팔로 구성한 참조이며 고유 생성원화 수가 아니다. 파생효과/idle연동 및 반전을 별도로 집계하며 전체 미술 완료율로 환산하지 않는다.'
 m['parallel_ownership']={'root':'기본/포스 저체력120..125,사다리14 동결·통합/실기','overhaul_audio':'Ultimate 승리204..207 및 남은 미술 범위','generation_policy':'한 캐릭터 한 페이지씩 공유 슬롯 순차 사용'}
 m['next_priorities']=['Ultimate 승리204..207 양의상 원화/손·사랑이/공통층/원순서39.','156..158의 기존 상세·원화/파생효과는 보존 검토. 자동 완성 또는 결함으로 분류하지 않음.','Ultimate 사다리·95..99·85..92·차량/hover와 기본/포스 등장승리귀환,root 저체력 후보를 계속 추적.']
 m['remaining_classification_origin']='이전v14의 각 참조 결정을 상속하고 이번 등장10·루트 사다리14만 변경. 다른 전모션을 이번에 재열람했다고 주장하지 않음.'
 (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(out/'manifest.json'),'full_new_art':m['frozen_full_new_art_reference_form_pairs'],'derived':m['frozen_derived_effect_reference_form_pairs'],'mirrored':m['frozen_mirrored_reference_form_pairs'],'all_frozen':m['all_frozen_reference_form_pairs']}))
if __name__=='__main__':main()
