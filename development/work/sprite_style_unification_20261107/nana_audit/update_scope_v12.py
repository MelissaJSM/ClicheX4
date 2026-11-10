"""RN18 기본/포스 피격 실기와 Ultimate 새원화/효과후보의 서로다른 단계를 기록."""
from pathlib import Path
import json,hashlib
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rec=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    old=N/'scope_summary_v11/manifest.json';j=json.loads(old.read_text('utf8'));out=N/'scope_summary_v12';out.mkdir(exist_ok=False)
    j['previous_immutable_manifest']=rec(old);j['scope']='기본/포스 피격13 동결후 RN18 실제관측을 연결. Ultimate4몸체×전후8원화와65층 효과후보는 제작중이며 동결/게임완료로 집계하지 않음.'
    summary=ROOT/'work/sprite_style_unification_20261107/runtime/nana_hurt18_summary.json';root92=ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint92.json'
    assert sha(summary)=='a661a9660588aebc766ee733eff1898be4302cf21d04721e1d940d66e0913f5a'
    j['rn18_hurt_runtime']={'summary':rec(summary),'root_review':rec(root92),'base_animation33_34_refs':list(range(106,115)),'fourth_animation35_refs':[233,234,235,236],'actual_capture_windows':480,'root_viewed_panels':24,'unresolved_mismatch_events':0,'scope':'root 실제새부팅 기본/포스 관측. 부분전조합·60Hz전수 실기는 아님. 원본/저장자료 보호28 및 두세션 정상종료.'}
    j['current_candidate']['new_gameplay_verified_here']=False;j['current_candidate']['root_runtime_evidence']=rec(summary)
    u=N/'ultimate_hurt_repaint';j['current_production']={'forms':['ultimate_before','ultimate_after'],'refs':[106,110,233,234],'dependent_effect_refs':[107,108,109,111,112,113,114,235,236],'stage':'eight_authored_sources_four_common_bodies_and_effect_targets','native_prepared_arc':None,
        'sources':[rec(u/'first_v1/generation.json'),rec(u/'extra_v1/generation.json')],'common_body':rec(u/'costume_pair_probe_v4/manifest.json'),'body_layers':rec(u/'body_layers_probe_v1/manifest.json'),'effect_diagnostic':rec(u/'effect_probe_v1/manifest.json'),'aura_candidate':rec(u/'aura_contact_probe_v2/registration.json'),
        'limits':'원화8표시/몸체20층·파생효과까지 새후보이며 패킹/원MIPS/GPU/독립/원시간표/실기는 아직완료아님. 두오라는현재외부확실한66/135px 보존,숨겨진전체효과복구주장없음.'}
    for form in ('ultimate_before','ultimate_after'):
        for r in j['remaining_by_form'][form]:
            if r['ref']in j['current_production']['refs']:r['stage']='common_body_registered_source_candidate'
            elif r['ref']in j['current_production']['dependent_effect_refs']:r['stage']='own_ultimate_effect_source_candidate'
    j['parallel_ownership']={'root':'기본/포스 사다리143..155/183; PL00부모978a·별도root_nana_ladder','overhaul_audio':'Ultimate피격13및후속Ultimate미완료','generation_policy':'한캐릭터/페이지 순차슬롯 공유'}
    j['frozen_reference_count_unchanged']=True
    j['reviewed_now']=[f'ultimate_hurt_repaint/{group}/comparison_{k}.png'for group in('extra_registered_v1','body_layers_probe_v1')for k in(1,2)]+[f'ultimate_hurt_repaint/effect_probe_v1/comparison_{k}.png'for k in(1,2,3)]+['ultimate_hurt_repaint/aura_contact_probe_v2/comparison.png']
    (out/'manifest.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(out/'manifest.json'),'new_art_pairs':j['frozen_full_new_art_reference_form_pairs'],'derived_pairs':j['frozen_derived_effect_reference_form_pairs']}))
if __name__=='__main__':main()
