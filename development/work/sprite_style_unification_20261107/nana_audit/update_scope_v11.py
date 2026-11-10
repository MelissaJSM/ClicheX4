"""기본/포스 피격 동결과 Ultimate 피격 첫 원화 상태를 구분해 장부를 갱신한다."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rec=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    old=N/'scope_summary_v10/manifest.json';j=json.loads(old.read_text('utf8'));out=N/'scope_summary_v11';out.mkdir(exist_ok=False)
    j['previous_immutable_manifest']=rec(old);j['scope']='기본/포스 피격 새몸체4와 효과파생9 동결, Ultimate 피격 첫2몸체×전후4 원화 고정등록. RN18 실기는 아직 연결하지 않음. 전체 완료율 아님.'
    body=[106,110,233,234];derived=[107,108,109,111,112,113,114,235,236];allrefs=sorted(body+derived)
    for form in ('base','fourth'):
        summary=j['summary'][form];summary['frozen_full_new_art_refs']=sorted(set(summary['frozen_full_new_art_refs']+body));summary['frozen_derived_effect_refs']=derived
        decisions=summary['reference_decisions'];decisions['needs_redraw']-=13;decisions['repaint_frozen']+=4;decisions['derived_effect_frozen']=9
        j['remaining_by_form'][form]=[q for q in j['remaining_by_form'][form]if q['ref']not in allrefs]
    for form in ('ultimate_before','ultimate_after'):
        for q in j['remaining_by_form'][form]:
            if q['ref']in allrefs:
                if q['decision']!='needs_redraw':
                    j['summary'][form]['reference_decisions'][q['decision']]-=1;j['summary'][form]['reference_decisions']['needs_redraw']+=1
                q.update({'group':'hurt','decision':'needs_redraw','stage':'source_fixed_registration'if q['ref']in(106,110)else'derived_effect_pending'if q['ref']in derived else'source_pending'})
    j['frozen_full_new_art_reference_form_pairs']=sum(len(q['frozen_full_new_art_refs'])for q in j['summary'].values())
    j['frozen_derived_effect_reference_form_pairs']=18
    j['frozen_new_art_plus_derived_reference_form_pairs']=j['frozen_full_new_art_reference_form_pairs']+18
    j['frozen_plus_prepared_reference_form_pairs']=j['frozen_full_new_art_reference_form_pairs']
    j['units']='한참조×한의상 표시 항목 수. 새몸체 원화와 파생효과를 분리 집계한다. 고유 원화 수·전체 품질완료율과 다르다.'
    p=N/'hurt_repaint/packed_hurt_candidate_v1';freeze=json.loads((p/'FROZEN.json').read_text('utf8'));assert freeze['frozen']
    j['preserved_frozen_sources']['PL00']=rec(p/'PL00_U.ARC')
    j['previous_completed_candidate']=j['current_candidate'];j['current_candidate']={**rec(p/'PL00_U.ARC'),'refs':allrefs,'new_body_keys':body,'derived_effect_refs':derived,'forms':['base','fourth'],'frozen':True,'new_gameplay_verified_here':False,'proofs':[rec(p/'FROZEN.json')]}
    u=N/'ultimate_hurt_repaint';j['current_production']={'forms':['ultimate_before','ultimate_after'],'refs':[106,110],'next_source_refs':[233,234],'dependent_effect_refs':derived,'stage':'first_four_sources_fixed_registered','native_prepared_arc':None,'generation':rec(u/'first_v1/generation.json'),'registration':rec(u/'first_registered_v1/registration.json'),'limits':'새원화4표시만 고정96셀 등록. 기존 공유효과·의상 공통부·손발 및 팔레트15 의미 정합 전. 새게임 미반영.'}
    j['reviewed_now']=[f'ultimate_hurt_repaint/scope_review_v1/comparison_{k}.png'for k in(1,2)]+[f'ultimate_hurt_repaint/first_registered_v1/comparison_{k}.png'for k in(1,2)]
    j['next_priorities'][0]={'scope':'Ultimate 피격106..114·233..236 및 기본/포스 저체력120..125','reason':'Ultimate106/110 뒤머리 단색띠,233/234 큰 분홍면/소매 구획을 대기와 실제 확대 재비교. 저체력Ultimate는 기존 상세 보존 검토와 구분.'}
    j['frozen_reference_count_unchanged']=False
    j['count_correction']='이전233..236의 low_hp 그룹 명칭은 hurt로 정정. 원몸통아머 접촉피격 표35에 해당하며 낮은체력 동작이 아니다.'
    (out/'manifest.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'sha256':sha(out/'manifest.json'),'new_art_pairs':j['frozen_full_new_art_reference_form_pairs'],'derived_pairs':18}))
if __name__=='__main__':main()
