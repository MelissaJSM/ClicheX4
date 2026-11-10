"""Ultimate 피격13 동결과 다음 등장/승리 읽기를 별도 단계로 기록한다."""
from pathlib import Path
import json,hashlib,copy
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    src=D/'scope_summary_v12/manifest.json';m=json.loads(src.read_text('utf8'));out=D/'scope_summary_v13';out.mkdir(exist_ok=False)
    body=[106,110,233,234];derived=[107,108,109,111,112,113,114,235,236];selected=set(body+derived)
    for form in('ultimate_before','ultimate_after'):
        s=m['summary'][form];remaining=m['remaining_by_form'][form]
        for q in remaining:
            if q['ref']in selected:s['reference_decisions'][q['decision']]-=1
        s['reference_decisions']={k:v for k,v in s['reference_decisions'].items()if v}
        s['reference_decisions']['repaint_frozen']=len(set(s['frozen_full_new_art_refs'])|set(body))
        s['reference_decisions']['derived_effect_frozen']=len(derived)
        s['frozen_full_new_art_refs']=sorted(set(s['frozen_full_new_art_refs'])|set(body));s['frozen_derived_effect_refs']=derived
        s['prepared_full_new_art_refs']=[];s['new_source_registered_not_packed_refs']=[133,135]
        m['remaining_by_form'][form]=[q for q in remaining if q['ref']not in selected]
        for q in m['remaining_by_form'][form]:
            if q['ref']in(133,135):q['stage']='authored_source_fixed_cell_registration_not_packed'
    m['scope']='Ultimate 피격13 동결까지 완료. RN19 통합/실기는 루트 별도 단계. 다음 등장133/135 전후4원화 고정셀 등록중이며 완료 집계 제외.'
    m['previous_immutable_manifest']=rec(src);m['previous_completed_candidate']=m['current_candidate']
    d=D/'ultimate_hurt_repaint';f=d/'packed_hurt_candidate_v1';fr=json.loads((f/'FROZEN.json').read_text('utf8'));assert fr['frozen']
    m['current_candidate']={**rec(f/'PL02_U.ARC'),'refs':sorted(selected),'new_body_keys':body,'derived_effect_refs':derived,'forms':['ultimate_before','ultimate_after'],'frozen':True,'new_gameplay_verified_here':False,'proofs':[rec(f/'FROZEN.json')],'root_runtime_evidence':None}
    m['preserved_frozen_sources']['PL02']=rec(f/'PL02_U.ARC')
    m['frozen_full_new_art_reference_form_pairs']=sum(len(v['frozen_full_new_art_refs'])for v in m['summary'].values())
    m['frozen_derived_effect_reference_form_pairs']=sum(len(v.get('frozen_derived_effect_refs',[]))for v in m['summary'].values())
    m['frozen_new_art_plus_derived_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs']+m['frozen_derived_effect_reference_form_pairs']
    m['prepared_pending_reference_form_pairs']=0;m['frozen_plus_prepared_reference_form_pairs']=m['frozen_full_new_art_reference_form_pairs'];m['frozen_reference_count_unchanged']=False
    c=D/'ultimate_ceremony_repaint'
    m['current_production']={'forms':['ultimate_before','ultimate_after'],'refs':[133,135],'stage':'first_four_authored_and_fixed_registered','native_prepared_arc':None,'sources':[rec(c/'first_v1/generation.json')],'registration':rec(c/'first_registered_v2/registration.json')}
    m['current_production']['limits']='133 전체+1y 눈정합은 접지1px 차이로 진단만 보존, 고정원점 후보 우선.135 감긴눈→열린눈 표현과 공통층/손발/효과는 후속 검토. 아직 새 ARC 없음.'
    m['next_priorities']=['Ultimate 등장133..140의 머릿결/재킷 가독성 및 고유효과 분리;133/135 첫4원화 등록중','기본/포스 사다리는 루트 별도소유. Ultimate204..207 승리·차량/호버·특수 잔여 계속','156..158 및 Ultimate사다리 등 기존세밀한후보는 실제비교 후 보존/재작화 판단;새그림이 없다는 이유로 불량 또는 완료로 단정하지 않음']
    m['all_nana_style_complete']=False;m['all_four_characters_complete']=False
    (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8')
    pre=json.loads((c/'preflight_v1/manifest.json').read_text('utf8'))
    review={'source_sha256':pre['source_sha256'],'actual_viewed_sheets':pre['sheets'],'count':8,'displayed_refs':15,'forms':2,'findings':[
      {'refs':[133,135,136,137],'decision':'needs_redraw','reason':'대기보다 굵은 연속검정 귀/머리외곽·넓은 단색앞머리,재킷 긴소매/커프 표현이 약함.133/135 새4원화는 별도등록중.'},
      {'refs':[138,139],'decision':'continuity_review_then_local_refinement','reason':'앞선133..137보다 명암이 있으나 뒤머리/하체면이 단순하다.독립몸체 차이가 있어 임의복제 금지.'},
      {'refs':[134,140],'decision':'effect_and_body_derivation_audit','reason':'134둥근효과와140흰실루엣은 단색그림 결함으로 분류하지 않고 몸체/효과 출처 조사.'},
      {'refs':[156,157,158],'decision':'preserve_pending_body_effect_audit','reason':'156얼굴·머리·재킷 구획이 남고 새확정절단은 못찾음.157/158은효과구분 우선;새제작 안됨을 품질미달로 동일시하지 않음.'},
      {'refs':[204,205,206,207],'decision':'needs_redraw','reason':'뒤머리 넓은 분홍면 및 소매 검정면이 대기보다 단순,207올린팔의 소매 구획이 특히 약함.원손/권총·접지는 유지.'}],
      'first_inputs_actually_viewed':[rec(c/'first_inputs_v1'/n)for n in('targets.png','style.png')],
      'first_native_comparisons_actually_viewed':[rec(c/'first_registered_v2'/f'comparison_{i}.png')for i in(1,2)],
      'gameplay_verified':False,'native_candidate_created':False,'scope':'8정적 최신재추출판과 첫원화등록2판 실제 열람.15refs×2폼이며 실시간/부분조합/게임미확인.'}
    (c/'preflight_v1/visual_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'summary_sha256':sha(out/'manifest.json'),'new_art_pairs':m['frozen_full_new_art_reference_form_pairs'],'derived_pairs':m['frozen_derived_effect_reference_form_pairs'],'total_pairs':m['frozen_new_art_plus_derived_reference_form_pairs']}))
if __name__=='__main__':main()
