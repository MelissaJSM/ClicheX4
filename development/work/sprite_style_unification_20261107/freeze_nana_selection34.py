from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_selection_sync34_03';ind=W/'zero_audit/nana_selection4_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
assert not(D/'FROZEN.json').exists();assert sha(D/'ST0E_U1.ARC')==sha(W/'nana_selection_sync34_repro01/ST0E_U1.ARC')=='a577566919c4dad695950347151ce3a57af8c3247172b04c1f36c5ec6f7101b5'
assert sha(ind/'report.json')=='7595cdf45855032154afd64a563b530d975176849813f55445c8c4aec9f32963'
assert sha(W/'root_review_checkpoint134.json')=='3502713aa77a5d3b530ab7a2b8420eb672b111b7ed87ced4bb453fec77d974cf'
for p in (D/'report.json',D/'origin_regression.json',ind/'report.json'):assert read(p)['passed']
files=[D/'ST0E_U1.ARC',D/'report.json',D/'origin_regression.json',D/'proposal_plan.json',W/'sync_nana_selection34.py',W/'check_selection_origins34.py',ROOT/'scripts/build_sprite_style_selection_v3.py',W/'root_review_checkpoint134.json',ind/'report.json',ind/'visual_review.json',W/'nana_selection_sync34_repro01/ST0E_U1.ARC',W/'nana_selection_sync34_repro01/report.json']
j={'frozen':True,'resource':'ST0E_U1.ARC','candidate_sha256':sha(D/'ST0E_U1.ARC'),'parent_arc_sha256':read(D/'report.json')['before'],'refs':[18,19,20,21],'files':[bound(p)for p in files],'status':'나나 선택4사본 동기화. 원모드별 원점 보존, 별도재현1·정상BR/RN/잘못된BR좌표회귀·독립80UI/1230기타record/134보호tile·ROOT4판 통과. 실제선택화면별도.','runtime_verified':False,'final_user_accepted':False}
(D/'FROZEN.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(D/'FROZEN.json'))
