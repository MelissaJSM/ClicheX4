"""Ultimate 라이징7 동결과 RN16 실기관측을 구분해 최신 장부에 연결한다."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
record=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}

def main():
    old=N/'scope_summary_v8/manifest.json';j=read(old);out=N/'scope_summary_v9';assert not out.exists()
    p=N/'rising_repaint/packed_ultimate_candidate_v1';f=read(p/'FROZEN.json');assert f['frozen'];refs=f['refs']
    for form in('ultimate_before','ultimate_after'):
        s=j['summary'][form];assert len(s['frozen_full_new_art_refs'])==86
        for q in j['remaining_by_form'][form]:
            if q['ref']in refs:s['reference_decisions'][q['decision']]-=1;s['reference_decisions']['repaint_frozen']+=1
        s['frozen_full_new_art_refs']=sorted(set(s['frozen_full_new_art_refs'])|set(refs));s['new_source_registered_not_packed_refs']=[]
        j['remaining_by_form'][form]=[q for q in j['remaining_by_form'][form]if q['ref']not in refs]
    j['scope']='v8를 보존하고 Ultimate 라이징7 최종동결 및 기본/포스 RN16 실기 범위를 연결했다. 전폼 미술 완료율이 아니다.'
    j['previous_immutable_manifest']=record(old);j['previous_completed_candidate']=j['current_candidate']
    j['current_candidate']={'path':(p/'PL02_U.ARC').relative_to(ROOT).as_posix(),'sha256':f['asset_sha256'],'refs':refs,'forms':['ultimate_before','ultimate_after'],'frozen':True,'new_gameplay_verified_here':False,'proofs':[record(p/'FROZEN.json')]}
    j['current_production']={'forms':['base','fourth'],'refs':[106,110],'stage':'next_source_inputs_preparing','native_prepared_arc':None,'source_scope':record(N/'hurt_repaint/scope_v1/manifest.json'),'dependent_effect_refs':[107,108,109,111,112,113,114],'limits':'피격몸체/효과CLUT·공유 분리 조사. 새 생성/패킹 완료 아님.'}
    j['preserved_frozen_sources']['PL02']=record(p/'PL02_U.ARC')
    count=sum(len(s['frozen_full_new_art_refs'])for s in j['summary'].values());assert count==372
    j['frozen_full_new_art_reference_form_pairs']=count;j['prepared_pending_reference_form_pairs']=0;j['frozen_plus_prepared_reference_form_pairs']=count
    runtime=ROOT/'work/sprite_style_unification_20261107/runtime/nana_rising16_summary.json'
    j['root_rn16_rising_runtime']=record(runtime);j['root_rn16_rising_runtime']['scope']='루트 포스352캡처/28참조(새7), 기본176캡처/22참조(새4:103/104/231/232) RAM/GPU. 실제20판 육안검토. Ultimate신규7 실기는 아직 아니다.'
    j['root_vehicle_hover_review']=record(ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint72.json')
    j['root_vehicle_hover_review']['scope']='루트 RN16 차량/hover 51refs×4폼 11판.184..203머리전용 보존,162..174 및213..230 후보 구분.217..230 실제mask15예외 유지.'
    j['next_priorities']=[{'scope':'기본/포스 피격106..114·233..236 및저체력120..125','reason':'넓은 단색 머리·검은옷 면을 고유몸체별 개선하고 원효과/깜박임을 분리 보호한다.'},{'scope':'기본/포스 사다리143..155/183 및등장133..140/승리204..207','reason':'새 대기 대비 머리 가닥/소매구획 격차. Ultimate133..137 재킷은 기존표현 약함이지 최근층삭제 아님.'},{'scope':'체이서162..174/호버213..230 및다른특수95..99/85..92','reason':'차량11판에서 큰 단색면 후보 확인. 탑승머리184..203은새결함못찾아보존; 도달/효과분류와무기접점유지.'}]
    j['reviewed_now']=['rising_repaint/packed_ultimate_candidate_v1/readback_1..3.png','rising_repaint/ultimate_native_cycle_v1/timeline_99..103.png','rising_repaint/ultimate_effect_contact_v1/comparison_1..2.png','hurt_repaint/scope_v1/comparison_1..5.png']
    j['remaining_classification_origin']='기존v8 전범위 장부+최종Ultimate7/피격19새추출5판의 실제열람. 다른모션을 새로전수검토했다고 확대하지 않는다.'
    out.mkdir();dst=out/'manifest.json';dst.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(dst),'frozen_form_reference_pairs':count}))
if __name__=='__main__':main()
