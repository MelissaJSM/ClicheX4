"""v6 장부를 보존하며 이동32 최종동결만 갱신한다. 완료율을 만들지 않는다."""
from pathlib import Path
import json,hashlib
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old=N/'scope_summary_v6/manifest.json';j=json.loads(old.read_text('utf8'));out=N/'scope_summary_v7';assert not out.exists()
 f=N/'ultimate_run_repaint/packed_run_candidate_v1/FROZEN.json';freeze=json.loads(f.read_text('utf8'));assert freeze['frozen']
 for form in ('ultimate_before','ultimate_after'):
  s=j['summary'][form];assert s['prepared_full_new_art_refs']==list(range(1,33))
  s['frozen_full_new_art_refs']=sorted(s['frozen_full_new_art_refs']+s['prepared_full_new_art_refs']);s['prepared_full_new_art_refs']=[]
  pending=s['reference_decisions'].pop('prepared_pending_independent_and_final_review');assert pending==32
  s['reference_decisions']['repaint_frozen']+=pending
 j['scope']='기존 v6 장부에 Ultimate 이동32 최종동결만 반영. 전 미술 완료율이나 고유 원화 수가 아니다.'
 j['previous_immutable_manifest']={'path':old.relative_to(ROOT).as_posix(),'sha256':sha(old)}
 j['frozen_full_new_art_reference_form_pairs']=344;j['prepared_pending_reference_form_pairs']=0
 j['current_candidate'].update(independent_pending=False,final_root_readback_review_pending=False,frozen=True,new_gameplay_verified=False)
 j['current_candidate']['proofs'].append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)})
 j['remaining_classification_origin']='v5 실제 정적 검토를 계승한 v6 장부. 이번에는 이동32 동결만 갱신했으며 남은 전참조 재열람 주장이 아니다.'
 assert all(len(q['frozen_full_new_art_refs'])==86 for q in j['summary'].values())
 out.mkdir();p=out/'manifest.json';p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'manifest_sha256':sha(p),'frozen_reference_form_pairs':344,'each_form_refs':86}))
if __name__=='__main__':main()
