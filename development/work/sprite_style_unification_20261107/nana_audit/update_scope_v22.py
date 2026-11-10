"""특수4와 루트 승리·귀환·차량의 동결을 장부에 합류한다."""
from pathlib import Path
import json,hashlib
N=Path(__file__).resolve().parent;W=N.parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rec=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 old=N/'scope_summary_v21/manifest.json';m=read(old);out=N/'scope_summary_v22';out.mkdir(exist_ok=False)
 def promote(forms,refs,decision,listkey):
  for form in forms:
   s=m['summary'][form];remaining={q['ref']:q for q in m['remaining_by_form'][form]}
   for n in refs:
    assert n in remaining and n not in s[listkey],(form,n);prev=remaining[n]['decision'];s['reference_decisions'][prev]-=1;s['reference_decisions'][decision]=s['reference_decisions'].get(decision,0)+1;s[listkey].append(n)
   s['reference_decisions']={k:v for k,v in s['reference_decisions'].items()if v};s[listkey]=sorted(s[listkey]);m['remaining_by_form'][form]=[q for q in m['remaining_by_form'][form]if q['ref']not in refs]
 def frozen(folder,name):
  fp=folder/'FROZEN.json';q=read(fp);asset=folder/name;assert q['frozen']and sha(asset)==q.get('asset_sha256',q.get('candidate_sha256'));return q,{'frozen':rec(fp),'asset':rec(asset),'refs':q['refs'],'new_gameplay_verified':False}
 p=N/'ultimate_special_finish_repaint/packed_special_candidate_v1';f,proof=frozen(p,'PL02_U.ARC');promote(('ultimate_before','ultimate_after'),[95,96,98,99],'repaint_frozen','frozen_full_new_art_refs')
 for key,folder,refs,effect in [('root_victory4','root_nana_victory/packed_victory02',[204,205,206,207],[]),('root_return3','root_nana_return/packed_return03',[156],[157,158]),('root_vehicle13','root_nana_vehicle/packed_vehicle03',list(range(162,175)),[])]:
  q,r=frozen(W/folder,'PL00_U.ARC');promote(('base','fourth'),refs,'repaint_frozen','frozen_full_new_art_refs')
  if effect:promote(('base','fourth'),effect,'derived_effect_frozen','frozen_derived_effect_refs')
  r['integration']='RN32 승리/RN34 귀환은 루트 통합 보고. 차량은 RN35 계획이며 이 시점 실제완료를 주장하지 않는다.';r['unique_source_body_keys']=[162,166,170,174]if key=='root_vehicle13'else refs;r['translated_reference_note']='차량13에는 고유4자세와9상하이동참조가 포함된다. 새원화26장이라는 뜻이 아니다.'if key=='root_vehicle13'else'';m[key]=r
 m['preserved_frozen_sources']['PL00']=m['root_vehicle13']['asset'];m['preserved_frozen_sources']['PL02']=rec(p/'PL02_U.ARC')
 m['previous_immutable_manifest']=rec(old);m['previous_completed_candidate']=m['current_candidate'];m['current_candidate']={'path':rec(p/'PL02_U.ARC')['path'],'sha256':f['asset_sha256'],'refs':f['refs'],'forms':f['forms'],'new_body_keys':[95,98],'translated_refs':[96,99],'derived_effect_refs':[],'frozen':True,'independent_pending':False,'final_root_readback_review_pending':False,'new_gameplay_verified':False,'integration':'RN35 루트 예정, 이 시점 통합완료 주장 없음','proofs':[rec(p/'FROZEN.json')]};m['ultimate_special4']={**proof,'source_authored_body_keys':[95,98],'translated_refs':[96,99],'weapon_policy':f['weapon_policy'],'translation_policy':f['translation_policy']}
 m['ultimate_recoil2']['integration']='RN33 및RN34 PL02 ce616 통합/원MIPS는 루트 보고. 신규 실기 관측은 별도.'
 v=N/'ultimate_vehicle_repaint';m['current_production']={'stage':'ultimate_vehicle_first_eight_source_cells_registered','new_body_refs':[162,166,170,174],'forms':['ultimate_before','ultimate_after'],'sources':[rec(v/f'{page}_v1/generated.png')for page in('a','b')],'registrations':[rec(v/f'{page}_registered_v1/manifest.json')for page in('a','b')],'first4_bbox_and_eye_exact':True,'second4_floor_delta':1,'old_after_alias_exact':False,'relation_reading':rec(v/'existing_v1/report.json'),'limits':'고정8셀만 등록. 의상/공통손·170/174 발높이와9파생의 원관계 후속 검토. 생성완료를 자원/미술/실기완료로 세지 않는다.','native_packed':False,'runtime_verified':False}
 for form in('ultimate_before','ultimate_after'):
  m['summary'][form]['new_source_registered_not_packed_refs']=[162,166,170,174]
  for q in m['remaining_by_form'][form]:
   if q['ref']in range(162,175):q['stage']='source_registered_joint_costume_pending'if q['ref']in(162,166,170,174)else'historical_alias_relation_pending'
 for name,key in[('full_new_art','frozen_full_new_art_refs'),('derived_effect','frozen_derived_effect_refs'),('mirrored','frozen_mirrored_refs')]:m[f'frozen_{name}_reference_form_pairs']=sum(len(s[key])for s in m['summary'].values())
 m['frozen_new_art_plus_derived_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs']+m['frozen_derived_effect_reference_form_pairs'];m['all_frozen_reference_form_pairs']=m['frozen_new_art_plus_derived_reference_form_pairs']+m['frozen_mirrored_reference_form_pairs'];m['frozen_plus_prepared_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs'];m['frozen_reference_count_unchanged']=False
 m['scope']='Ultimate특수4 및 루트 기본/포스 승리4·귀환3·차량13의 동결을 합류. 다음얼티밋차량8원화는 미완료로 분리.';m['count_limit']=f"{m['all_frozen_reference_form_pairs']}는 {m['frozen_full_new_art_reference_form_pairs']}새아트참조×폼 + {m['frozen_derived_effect_reference_form_pairs']}효과파생 + {m['frozen_mirrored_reference_form_pairs']}반전표시의 합계다. 새아트참조에는 X+1/상하흔들림 파생도 포함되므로 고유원화 수·생성횟수·전체완료율이 아니다."
 m['reviewed_now']=[rec(p/'producer_visual_review.json'),rec(W/'root_review_checkpoint133.json')];m['next_priorities']=['Ultimate 탑승162/166/170/174 원화 손발·의상 공통층,원9파생관계 검증.','Root 기본/포스85/86 신규원화는 별도 진행이며 기존장부의review_before_decision을 완료로 바꾸지 않는다.','사다리 보류7은 미완료·무변경 유지. hover/Nova/기타분류 잔여는 계속 추적.'];m['remaining_classification_origin']='v21 상속 후 실제FROZEN을 확인한 범위만 추가. 이번 전체모션 전수재열람은 하지 않았다.'
 (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(out/'manifest.json'),'total':m['all_frozen_reference_form_pairs'],'new_art_refs':m['frozen_full_new_art_reference_form_pairs'],'effect_refs':m['frozen_derived_effect_reference_form_pairs']}))
if __name__=='__main__':main()
