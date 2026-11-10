"""RN19 후폼피격 대표 실기와 현재 등장 미완료 후보를 연결한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    src=D/'scope_summary_v13/manifest.json';m=json.loads(src.read_text('utf8'));out=D/'scope_summary_v14';out.mkdir(exist_ok=False);c=D/'ultimate_ceremony_repaint';runtime=ROOT/'work/sprite_style_unification_20261107/runtime/nana_ultimate_hurt19_summary.json';r=json.loads(runtime.read_text('utf8'))
    m['previous_immutable_manifest']=rec(src);m['scope']='Ultimate 피격13은RN19통합/획득후233..236 대표실기근거 연결. 새등장5몸체×2의상은등록후보이며최종무기/공통층/효과·패킹미완료.완료수증가없음.'
    m['current_candidate']['root_runtime_evidence']=rec(runtime);m['current_candidate']['root_runtime_scope']={'forms':['ultimate_after'],'refs':r['verified_new_references'],'actual_captures':r['actual_captures'],'root_viewed_boards':r['root_viewed_boards'],'before_and_other_hurt_refs_unverified':True}
    snapshot=out/'ceremony_progress_snapshot.json';snapshot.write_bytes((c/'production_status.json').read_bytes())
    m['current_production']={'forms':['ultimate_before','ultimate_after'],'refs':[133,135,136,137,138],'linked_refs':[130,131,134,139,141],'stage':'source_registration_and_weapon_semantics','native_prepared_arc':None,'progress':rec(snapshot),'limits':'138초기낮춘팔안은미채택.위로든권총팔국소원화98029555를의미영역등록중.기존동결자원불변.','source_pages':[rec(c/q/'generation.json')for q in('first_v1','second_v1','raised138_v1')]}
    for form in('ultimate_before','ultimate_after'):
        m['summary'][form]['new_source_registered_not_packed_refs']=[133,135,136,137,138]
        for q in m['remaining_by_form'][form]:
            if q['ref'] in(133,135,136,137,138):q['stage']='new_art_registered_not_packed_weapon_contacts_pending'
            if q['ref'] in(130,131,134,139,141):q['stage']='linked_body_silhouette_correction_planned'
    m['next_priorities']=['Ultimate 등장133..139의손/사랑이·공통층과130/131/134/141 연동.138교정은원위권총자세 유지.','기본/포스사다리는루트별도소유.다음Ultimate204..207승리와남은전체범위추적.','156..158은현재상세와파생효과확인으로보존검토.미재작화를불량또는완료로자동분류하지않음.']
    m['frozen_reference_count_unchanged']=True;m['all_nana_style_complete']=False;m['all_four_characters_complete']=False
    (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'path':str(out/'manifest.json'),'sha256':sha(out/'manifest.json'),'frozen_pairs':m['frozen_new_art_plus_derived_reference_form_pairs']}))
if __name__=='__main__':main()
