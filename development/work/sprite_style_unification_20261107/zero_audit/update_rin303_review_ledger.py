"""Attach new read-only reviews to the mutable current ledger only."""
from pathlib import Path
import hashlib
import json
D=Path(__file__).parent
R=D/'rin_extension'
ledger=json.loads((R/'progress_ledger.json').read_text('utf8'))
assert ledger['prepared_count']==303
assert ledger['current_sha256']=='1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
inventory=json.loads((R/'all_unique_review303/inventory.json').read_text('utf8'))
assert all(p['actual_view_image'] for p in inventory['pages']) and len(inventory['pages'])==58
assert all(r['provisional_groups'] for r in inventory['references'].values())
ledger['full_visual_review']='all_unique_review303/visual_review.json'
ledger['full_visual_review_scope']='최신303의436 단독 표시를 동일 색인 형태319그룹으로 묶어 일반29·레드29 총58판을 실제 열람했다. 추가 확정 재작화 대상은 찾지 못했으나 전수 실기 완료는 아니다.'
ledger['latest_targeted_visual_review']='burst303_review_v2/visual_review.json'
ledger['current_selection_copy_check']='validation_scope303/selection_current.json'
ledger['current_runtime_scope']='validation_scope303/runtime_scope.json'
ledger['next_page_scope']='새303 통합본의 양방향 낙봉파·지상 질풍아와 미관측 사다리/탑승/등장/레드 실기 범위 확인. 추가 확정 미술 문제가 생기면 별도 후속 경로로 수정한다.'
ledger['classification_check']={'standalone_body_or_head':313,'standalone_effect_or_blank':123,'history_dependent_partial':8,'separate_static_body_effects':2,'unclassified_standalone':0,'blank_body_misclassified':0,'is_completion_percentage':False}
(R/'progress_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n','utf8')
(R/'progress_ledger303_review_snapshot.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n','utf8')
print(hashlib.sha256((R/'progress_ledger303_review_snapshot.json').read_bytes()).hexdigest())
