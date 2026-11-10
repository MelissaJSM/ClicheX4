"""라이징7 동결 및 현재 Ultimate 원화 진행을 새 장부에 추가한다."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent
ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
record=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}

def main():
    old=N/'scope_summary_v7/manifest.json'
    j=read(old);out=N/'scope_summary_v8';assert not out.exists()
    p=N/'rising_repaint/packed_base_candidate_v1'
    f=read(p/'FROZEN.json');assert f['frozen']
    refs=f['refs'];new_source=[100,101,103,104]
    for form in('base','fourth'):
        s=j['summary'][form]
        assert len(s['frozen_full_new_art_refs'])==86
        s['frozen_full_new_art_refs']=sorted(s['frozen_full_new_art_refs']+refs)
        s['reference_decisions']['needs_redraw']-=7
        s['reference_decisions']['repaint_frozen']+=7
        j['remaining_by_form'][form]=[q for q in j['remaining_by_form'][form]if q['ref']not in refs]
    for form in('ultimate_before','ultimate_after'):
        j['summary'][form]['new_source_registered_not_packed_refs']=new_source
        for q in j['remaining_by_form'][form]:
            if q['ref']in new_source:q['stage']='new_source_registered_contacts_and_common_layers_pending'
            elif q['ref']in refs:q['stage']='new_costume_source_pending'
    j['scope']='v7를 보존하고 기본/포스 라이징7 최종동결과 Ultimate 라이징 원화 진행을 추가했다. 새 미술 완료율이 아니다.'
    j['previous_immutable_manifest']=record(old)
    j['previous_completed_candidate']=j.pop('current_candidate')
    j['current_candidate']={'path':(p/'PL00_U.ARC').relative_to(ROOT).as_posix(),'sha256':f['asset_sha256'],
        'refs':refs,'forms':['base','fourth'],'frozen':True,'new_gameplay_verified_here':False,
        'proofs':[record(p/'FROZEN.json')]}
    j['current_production']={'forms':['ultimate_before','ultimate_after'],'refs':refs,
        'registered_source_refs':new_source,'native_prepared_arc':None,
        'registered_source_proofs':[record(N/'rising_repaint/ultimate_air_registered_v1/registration.json'),
                                    record(N/'rising_repaint/ultimate_charge_registered_v3/registration.json')]}
    j['preserved_frozen_sources']['PL00']=record(p/'PL00_U.ARC')
    j['preserved_frozen_sources']['PL02']=record(N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC')
    j['frozen_full_new_art_reference_form_pairs']=358
    j['prepared_pending_reference_form_pairs']=0
    j['frozen_plus_prepared_reference_form_pairs']=358
    runtime=ROOT/'work/sprite_style_unification_20261107/runtime/nana_ultimate_run14_summary.json'
    j['root_v14_run_runtime']=record(runtime)
    j['root_v14_run_runtime']['scope']='루트 실제287창/새1..32 업로드·16시각판. 새라이징 게임검증을 뜻하지 않는다.'
    j['next_priorities']=[
        {'scope':'Ultimate 라이징100..104/231/232','reason':'현재 전후 의상 원화 등록 중. 실제 초기불꽃과 사랑이 위치·공통층·원순서를 함께 검증한다.'},
        {'scope':'등장133..140/승리204..207/귀환 및 기본·포스 사다리143..155/183','reason':'최근 실제 열람에서 머리/의상 세부 감소 확인. Ultimate133..137 재킷층은 기존과 동일하게 존재하나 재킷 가독성 개선이 필요하다.'},
        {'scope':'기본·포스 피격106..114/233..236·저체력120..125 및 모든폼 차량162..174/184..203','reason':'새 원화 미진행과 실제 품질 미달을 구분해 대기와 비교하고 필요한 고유형태를 제작한다.'},
        {'scope':'특수95..99/85..92/208..230 및 선택 사본','reason':'효과전용/실제도달/기존 상세보존 분류를 유지한다. 새 제작이 없다는 이유만으로 불량으로 확정하지 않는다.'}]
    audit=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_arrival_endpoint_audit01/report.json'
    j['arrival_layer_audit']=record(audit)
    j['arrival_layer_audit']['conclusion']='현재133..137의5층과before표시는11/05이력exact. 최근레이어삭제/정적마스크오인이 아닌 기존재킷미술 가독성 한계.'
    j['reviewed_now']=['rising_repaint/packed_base_candidate_v1/readback_1..3.png',
        'rising_repaint/native_cycle_v1/timeline_99..103.png',
        'rising_repaint/ultimate_air_registered_v1/comparison_1..2.png',
        'rising_repaint/ultimate_charge_registered_v3/comparison_1..2.png']
    j['remaining_classification_origin']='v5 실제열람 분류를 계승한v7+라이징7동결. 다른 미진행 전참조를 새로 전수열람했다고 주장하지 않는다.'
    assert sum(len(s['frozen_full_new_art_refs'])for s in j['summary'].values())==358
    out.mkdir();dst=out/'manifest.json';dst.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'sha256':sha(dst),'frozen_reference_form_pairs':358}))

if __name__=='__main__':main()
