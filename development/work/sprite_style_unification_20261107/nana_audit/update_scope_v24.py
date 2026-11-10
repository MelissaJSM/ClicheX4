"""RN36 차량 통합과 새 호버10 후보 검증을 완료수와 분리한다."""
from pathlib import Path
import json,hashlib
N=Path(__file__).resolve().parent;W=N.parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rec=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 old=N/'scope_summary_v23/manifest.json';m=read(old);out=N/'scope_summary_v24';out.mkdir(exist_ok=False);h=N/'ultimate_hover_repaint';p=h/'packed_hover_candidate_v1';assert sha(p/'PL02_U.ARC')=='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'
 m['previous_immutable_manifest']=rec(old);rn=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v36/rin_nana.bin';assert sha(rn)=='3715c4f50c0adcceeeed435f3e59bdccc51c5bf79b4f7fa8fdb961b88fd1a3ea';m['rn36_integration']={'bin':rec(rn),'scope':'Ultimate차량9432와루트기본85/86 통합. 실제게임 차량관측은 별도.','evidence':'루트완료보고+이파일hash 확인, 자체호버 원MIPS source.'};m['ultimate_vehicle13']['integration']='RN36 통합/원MIPS source확인. 실기미관측.'
 for form in('ultimate_before','ultimate_after'):
  m['summary'][form]['new_source_registered_not_packed_refs']=[]
  for q in m['remaining_by_form'][form]:
   if q['ref']in range(221,231):q['stage']='packed_candidate_e630_independent_pending'
 m['current_production']={'stage':'ultimate_hover10_final_candidate_independent_pending','candidate':rec(p/'PL02_U.ARC'),'input_lock':rec(p/'INPUT_FROZEN.json'),'targets':rec(h/'targets_preview_v3/manifest.json'),'new_body_refs':[221,223,225,227,229],'new_arm_refs':[222,224,226,228,230],'source_cells':10,'actual_visual_mask':15,'layer0':'상체','layer5':'하체','empty_layers':[6,7,8],'source_reconstruction':rec(h/'targets_preview_v3/source_reconstruction.json'),'packed_verification':rec(p/'verification.json'),'reproduction':rec(p/'reproduction.json'),'native':rec(h/'native_components_v1_native_checks.json'),'original_sequence':rec(h/'native_cycle_v1/verification.json'),'original_effect_contacts':rec(h/'packed_contacts_v1/report.json'),'visual':rec(p/'producer_visual_review.json'),'frozen':False,'runtime_verified':False,'counted_as_completed':False,'muzzle_policy':'옛8열창보존 진단안은 미채택. 실제원US/RN36총구표에 정본20과 새팔을 정합. 코드·효과·전신원점 불변.','blocked_ladder_refs_unchanged':[148,149,150,151,152,153,155]}
 m['scope']='RN36 Ultimate차량 통합 확인. 호버10 새5몸체+원발사점5팔 최종후보는 독립대기이며 완료수에 미포함.';m['next_priorities']=['호버10 독립·루트 원순서 검토 후 동결.','노바213..220 실제소유/원효과 관계 조사와 대기 대비 세부 검토.','사다리 보류7은 미완료/무변경 유지. 기본/포스 후속집계는 루트 최종장부와 별도 연결.'];m['remaining_classification_origin']='v23 상속. 현재제작호버10만진행상태갱신, 전체모션 재열람/루트새완료전수집계는 하지 않았다.'
 (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(out/'manifest.json'),'frozen_count_unchanged':m['all_frozen_reference_form_pairs']}))
if __name__=='__main__':main()
