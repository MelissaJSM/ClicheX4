"""승리4·루트 저체력6 동결과 귀환 원화후보를 구분하는 새 스냅샷."""
from pathlib import Path
import json,hashlib,collections
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
def rec(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')

def main():
 old=N/'scope_summary_v15/manifest.json';m=read(old);out=N/'scope_summary_v16';out.mkdir(exist_ok=False)
 history=read(N/'scope_summary_v5/manifest.json');v=N/'ultimate_victory_repaint';vp=v/'packed_victory_candidate_v1';vf=read(vp/'FROZEN.json');assert vf['frozen']
 low=ROOT/'work/sprite_style_unification_20261107/root_nana_lowhp/packed_lowhp01';lf=read(low/'FROZEN.json');assert lf['frozen']
 runtime=ROOT/'work/sprite_style_unification_20261107/runtime/nana_base_lowhp22_summary.json';rt=read(runtime);assert not rt['target_trigger_verified'] and not rt['new_lowhp_actual_frames_observed']
 r=N/'ultimate_return_repaint'
 for form,s in m['summary'].items():
  d={q['ref']:q['decision']for q in history['frames'][form]};d.update({q['ref']:q['decision']for q in m['remaining_by_form'][form]})
  for key,decision in [('frozen_full_new_art_refs','repaint_frozen'),('frozen_derived_effect_refs','derived_effect_frozen'),('frozen_mirrored_refs','mirrored_frozen')]:d.update({n:decision for n in s[key]})
  assert dict(collections.Counter(d.values()))==s['reference_decisions']
  added=lf['refs'] if form in('base','fourth') else vf['refs'];d.update({n:'repaint_frozen'for n in added})
  s['reference_decisions']=dict(collections.Counter(d.values()));s['frozen_full_new_art_refs']=sorted(n for n,v in d.items()if v=='repaint_frozen');s['new_source_registered_not_packed_refs']=[156]if form.startswith('ultimate')else[95,98]
  m['remaining_by_form'][form]=[q for q in m['remaining_by_form'][form]if q['ref']not in added]
  for q in m['remaining_by_form'][form]:
   if form.startswith('ultimate')and q['ref']in(156,157,158):q['stage']='new156_local_costume_candidate_157158_derivation_pending'
   elif form in('base','fourth')and q['ref']in(95,96,98,99):q['stage']='root_new95_98_registration_96_99_exact_xplus1_derived_pending'
 m['scope']='Ultimate 승리4와 루트 기본/포스 저체력6 동결 반영. RN22 저체력 발동 실패는 실기통과로 세지 않음. 귀환156은 새등록후보,157/158파생은 미완료.'
 m['previous_immutable_manifest']=rec(old);m['previous_completed_candidate']=m['current_candidate'];m['current_candidate']={'path':rec(vp/'PL02_U.ARC')['path'],'sha256':vf['asset_sha256'],'refs':vf['refs'],'forms':['ultimate_before','ultimate_after'],'new_body_keys':vf['new_authored_body_keys'],'linked_body_effect_refs':[],'frozen':True,'independent_pending':False,'final_root_readback_review_pending':False,'new_gameplay_verified':False,'proofs':[rec(vp/'FROZEN.json')]}
 m['preserved_frozen_sources']={'PL00':rec(low/'PL00_U.ARC'),'PL02':rec(vp/'PL02_U.ARC')}
 m['root_lowhp6']={'frozen':rec(low/'FROZEN.json'),'refs':lf['refs'],'forms':['base','fourth'],'distinct_body_rule':'새 한몸×2의상과 입1픽셀·접지호흡으로6참조를 전개한 묶음.6개 독립 전신 원화라고 세지 않음.','integration':'RN22 통합. resident asset RAM동일은 별도 증거.','runtime_attempt':rec(runtime),'target_trigger_verified':False,'new_lowhp_actual_frames_observed':[],'runtime_limit':'HP를 낮추다가 사망/재시작되어 저체력 동작 발동 실패. 원MIPS/원표/독립192부분조건 검사는 유효하나 실제저체력 관측은 미완료.'}
 progress={'stage':'new156_body_and_local_costume_registered_candidate','forms':['ultimate_before','ultimate_after'],'new_body_refs':[156],'planned_linked_refs':[157,158],'preserve_energy_refs':[159,160],'parent_frozen':rec(vp/'FROZEN.json'),'proofs':[rec(r/'body_v1/generation.json'),rec(r/'body_registered_v1/registration.json'),rec(r/'costume_edit_v1/generation.json'),rec(r/'costume_pair_probe_v2/manifest.json')],'native_packed':False,'runtime_verified':False,'issues':'최초 원화의 흰 반바지는 미채택. 국소 새 의상40셀과 최초 실제경계1셀로 정합한 v2를 검토 중. 새 머리/다리 유지하며157/158 원빛·파생은 후속.'}
 write(out/'return_progress_snapshot.json',progress);m['current_production']=progress
 write(v/'production_status.json',{'frozen':True,'frozen_file':rec(vp/'FROZEN.json'),'asset_sha256':vf['asset_sha256'],'refs':vf['refs'],'source_pages':2,'distinct_body_keys':4,'costume_displays':8,'shared_record_207_layer5_to_89_preserved':True,'native_cycle_canvas':66,'runtime_verified':False,'next_return':rec(out/'return_progress_snapshot.json')})
 m['reviewed_now']=[rec(vp/f'readback_{i}.png')for i in(1,2)]+[rec(v/f'native_cycle_v1/timeline_{i}.png')for i in(39,40)]+[rec(r/'body_registered_v1/comparison.png'),rec(r/'costume_pair_probe_v2/comparison.png')]
 for name,key in [('full_new_art','frozen_full_new_art_refs'),('derived_effect','frozen_derived_effect_refs'),('mirrored','frozen_mirrored_refs')]:m[f'frozen_{name}_reference_form_pairs']=sum(len(s[key])for s in m['summary'].values())
 m['frozen_new_art_plus_derived_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs']+m['frozen_derived_effect_reference_form_pairs'];m['all_frozen_reference_form_pairs']=m['frozen_new_art_plus_derived_reference_form_pairs']+m['frozen_mirrored_reference_form_pairs'];assert m['all_frozen_reference_form_pairs']==492
 m['frozen_plus_prepared_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs'];m['frozen_reference_count_unchanged']=False
 m['parallel_ownership']={'root':'기본/포스95/98 새원화·96/99 x+1 파생, 통합/실기','overhaul_audio':'Ultimate 귀환156 및157/158연동·나머지미술','generation_policy':'공유 슬롯으로 한 캐릭터 한 페이지씩 순차'}
 m['next_priorities']=['Ultimate 귀환156 양폼 의상/공통층 후보검토 뒤157/158효과파생/원표40/패킹.','Ultimate 사다리·95..99·85..92·차량/hover 및 기본/포스 등장승리귀환 후속.','RN22 저체력 실기 발동은 미완료로 유지. 기존 상세 보존 항목을 자동 재작화 요구로 바꾸지 않음.']
 m['remaining_classification_origin']='이전v15 결정을 상속하고 승리4와 루트저체력6만동결갱신. 모든 나머지모션을 이번에 새로 직접열람했다고 주장하지 않음.'
 write(out/'manifest.json',m);print(json.dumps({'sha256':sha(out/'manifest.json'),'new_reference_forms':m['frozen_full_new_art_reference_form_pairs'],'derived':m['frozen_derived_effect_reference_form_pairs'],'mirrored':m['frozen_mirrored_reference_form_pairs'],'total':m['all_frozen_reference_form_pairs']}))
if __name__=='__main__':main()
