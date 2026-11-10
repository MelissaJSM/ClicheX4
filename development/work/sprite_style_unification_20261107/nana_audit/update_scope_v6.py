"""이전 상세장부를 보존하고 현재 이동32 준비상태만 작은 manifest로 갱신."""
from pathlib import Path
import json,hashlib,collections
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old=N/'scope_summary_v5/manifest.json';j=json.loads(old.read_text('utf8'));out=N/'scope_summary_v6';assert not out.exists();out.mkdir()
 p=N/'ultimate_run_repaint/packed_run_candidate_v1';asset=p/'PL02_U.ARC';assert sha(asset)=='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
 summary={};remaining={}
 for form,rows in j['frames'].items():
  compact=[]
  for r in rows:
   pending=form.startswith('ultimate_')and 1<=r['ref']<=32
   compact.append({'ref':r['ref'],'group':r['group'],'decision':'prepared_pending_independent_and_final_review'if pending else r['decision'],
    'stage':'native_original_MIPS_RGBA7296_offline258_passed_not_frozen'if pending else r['production_stage']})
  summary[form]={'reference_decisions':dict(collections.Counter(r['decision']for r in compact)),
   'frozen_full_new_art_refs':[r['ref']for r in compact if r['decision']=='repaint_frozen'],
   'prepared_full_new_art_refs':[r['ref']for r in compact if r['decision']=='prepared_pending_independent_and_final_review']}
  remaining[form]=[r for r in compact if r['decision']in('needs_redraw','review_before_decision','reachability_review_required')]
 runtime=ROOT/'work/sprite_style_unification_20261107/runtime/nana_checkpoint12_summary.json'
 proof=[p/'proposal.json',p/'extended_verification.json',N/'ultimate_run_repaint/native_components_native_checks.json',N/'ultimate_run_repaint/native_cycle_v1/verification.json']
 result={'scope':'기존 v5 미술장부에 현재 Ultimate 이동32 준비결과만 반영한 작은 진행 manifest. 완료율이 아니다.',
  'previous_immutable_manifest':{'path':old.relative_to(ROOT).as_posix(),'sha256':sha(old)},
  'summary':summary,'remaining_by_form':remaining,'frozen_full_new_art_reference_form_pairs':280,
  'prepared_pending_reference_form_pairs':64,'frozen_plus_prepared_reference_form_pairs':344,
  'units':'한 참조×한 의상 표시를1로 센다. 고유 원화 수/고유 프레임 수/전체 작업 완료율과 다르다.',
  'current_candidate':{'path':asset.relative_to(ROOT).as_posix(),'sha256':sha(asset),'refs':list(range(1,33)),'forms':['ultimate_before','ultimate_after'],
   'independent_pending':True,'final_root_readback_review_pending':True,'frozen':False,'new_gameplay_verified':False,
   'proofs':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)}for q in proof]},
  'preserved_frozen_sources':j['sources'],'root_v12_dash_runtime':{'path':runtime.relative_to(ROOT).as_posix(),'sha256':sha(runtime),'scope':'이전 동결 대시20의 실기. 현재 이동32 후보 검증으로 재사용하지 않음.'},
  'next_priorities':[{'scope':'기본/포스/Ultimate 특수사격·Rising100..104/231..236','reason':'이전 세밀도 미달 및103/104의 원US 불꽃 위치와 사랑이 발사 연결 정적 후속. Nana 실기 결함 확정은 아님.'},
   {'scope':'피격/저체력106..124 및 의상별 회복','reason':'대기대비 단순한 얼굴·소매·다리 잔여를 실제 재비교 후 소량키부터 재작화.'},
   {'scope':'사다리/등장/귀환/승리/탑승','reason':'부분 기존원화복원은 전체 새 미술 통일과 구분. 기존 상세가 충분한참조는 보존할 수 있음.'}],
  'selection_followup':'향후 Nana 기본 차지/등장/승리 변경 시 X선택16사본을 RN 원래변환으로 별도 동기화. root 감사에서 현재모양동일,19/20 y0·18/22/23 y-1·24 y-2. BR변환무단재사용금지.',
  'reviewed_now':['arm_shading_audit_v2/source_native_comparison.png','arm_source_shading_probe_v1/comparison_2..4.png','common_arm_boundary_probe_v2/comparison_1..2.png','packed_run_candidate_v1/readback_1..4.png'],
  'remaining_classification_origin':'v5 실제 정적 검토 장부를 계승했다. 이번에 남은 전참조를 새로 다시 열람했다고 주장하지 않는다.',
  'all_nana_style_complete':False,'all_four_characters_complete':False,'game_BIN_or_pointer_modified_here':False}
 (out/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'manifest_sha256':sha(out/'manifest.json'),'frozen':280,'prepared':64}))
if __name__=='__main__':main()
