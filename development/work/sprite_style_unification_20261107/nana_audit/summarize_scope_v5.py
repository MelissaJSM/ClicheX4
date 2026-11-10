"""동결 v4를 보존한 채 최신 게임 적용/실기와 미패킹 원화를 분리 기록."""
from pathlib import Path
import sys,json,collections
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path[:0]=[str(ROOT),str(D/'native_restore')]
from preview_restore import digest,write,need

def main():
 out=D/'scope_summary_v5';out.mkdir(exist_ok=False);old=D/'scope_summary_v4/manifest.json';m=json.loads(old.read_text('utf8'))
 frozen=D/'ultimate_dash_repaint/packed_dash_candidate_v1/FROZEN.json';need(json.loads(frozen.read_text('utf8'))['asset_sha256']=='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0','Freeze')
 before=json.loads((D/'ultimate_run_repaint/body_review_v2/manifest.json').read_text('utf8'));paths={q['ref']:q for q in before['frames']};summary={}
 for form,items in m['frames'].items():
  for q in items:
   n=q['ref']
   if form.startswith('ultimate')and n in(*range(67,85),93,94):q.update(production_stage='full_new_art_frozen_root_art_reviewed_integrated_v12',evidence='ultimate_dash_repaint/packed_dash_candidate_v1/FROZEN.json',runtime_scope='v12 후폼 실제 새20 전부 관측. 전폼 실기 확인으로 확대하지 않음.')
   if form=='ultimate_before'and n in range(1,33,2):q.update(production_stage='all16_before_bodies_registered_original_timeline_checked_not_packed',candidate_evidence=paths[n])
   if form=='ultimate_after'and n in(1,7,15,25):q.update(production_stage='after_costume_generated_fixed_cell_donor_not_joint_not_packed',candidate_evidence='ultimate_run_repaint/after_a_registered_v1/registration.json')
  summary[form]={'decision_reference_counts':dict(collections.Counter(q['decision']for q in items)),'stage_reference_counts':dict(collections.Counter(q['production_stage']for q in items))}
 m.update(summary=summary,full_style_complete=False,gameplay_by_this_agent=False,update_scope='기본/포스 각86 및 Ultimate 각54 새 전신 참조 동결 수는 v4와 같다. Ultimate 대시20은 루트 최종 미술 검토·v12 통합·후폼 실제 관측 완료. 이동 재킷16은 새 원화 등록과 원시간표 오프라인 검사를 완료했지만 후폼16/사격16쌍/패킹이 남아 기존 동결 수에 포함하지 않는다.',previous_immutable_manifest={'path':old.relative_to(ROOT).as_posix(),'sha256':digest(old)})
 m['current_work']={'ultimate_run32':{'before_registered_refs':list(range(1,33,2)),'after_generated_refs':[1,7,15,25],'after_joint_refs':[],'firing_new_refs':[],'native_packed':False,'body_preview':{'path':(D/'ultimate_run_repaint/body_review_v2/verification.json').relative_to(ROOT).as_posix(),'sha256':digest(D/'ultimate_run_repaint/body_review_v2/verification.json')},'next':['후폼 나머지12 원화','후폼16 의상 의미영역 합성','이동사격16 새팔 전후 생성·정합','공유32타일/원총구/부분파츠/원시간표 재추출 검사']},'required_followup':'모든 폼 Rising103/104의 원US 오른손·원불꽃에 사랑이 권총/총구 연결 교정. 단순주먹으로 무기를 대체하지 않는다.'}
 runtime=ROOT/'work/sprite_style_unification_20261107/runtime/nana_checkpoint12_summary.json'
 m['root_runtime_evidence']={'path':runtime.relative_to(ROOT).as_posix(),'exists':runtime.exists(),'sha256':digest(runtime)if runtime.exists()else None,'scope':'루트 새부팅 후폼 대시 실기. 최초72 GPU샘플 원인은 확정하지 않으며 재시도72 모두일치·타실패의 직전/목표행혼합을 별도 사후 감사.'}
 m['remaining_by_form']={f:[{'ref':q['ref'],'decision':q['decision'],'stage':q['production_stage']}for q in items if q['decision']in('needs_redraw','review_before_decision','reachability_review_required')]for f,items in m['frames'].items()}
 m['coverage_limits']='이 장부 갱신에서 이전948표시를 다시 모두 열람하지 않았다. 현재 frozen 실물 키 목록은 v4와 동일하므로 그대로 상속한다. 새로운 원화/정적수치/오프라인/게임실기/사용자 최종수용은 서로 다른 단계다. 선택·저장·부분아머 및 특수·탑승·승리·귀환 등 원래 전체 범위 유지.'
 write(out/'manifest.json',m);print(json.dumps({'path':str(out/'manifest.json'),'sha256':digest(out/'manifest.json'),'full_style_complete':False}))
if __name__=='__main__':main()
