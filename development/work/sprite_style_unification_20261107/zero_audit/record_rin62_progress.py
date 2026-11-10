from pathlib import Path
import json,hashlib
D=Path(__file__).parent/'rin_extension';P=D/'prepared_third_saber_v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=json.loads((D/'progress_ledger.json').read_text('utf8'))
old=D/'progress_ledger52_snapshot.json'
if not old.exists():old.write_bytes((D/'progress_ledger.json').read_bytes())
new=[f'b0_{n:03}'for n in range(109,128,2)]
j['new_art_prepared_refs']=sorted(set(j['new_art_prepared_refs'])|set(new));assert len(j['new_art_prepared_refs'])==62
j['remaining_refs_in_original_audit']=[r for r in j['remaining_refs_in_original_audit']if r not in new]
j['current_arc']=str(P/'PL01_U.ARC');j['current_sha256']=sha(P/'PL01_U.ARC');j['prepared_count']=62
j['latest_scope']='새 원화 5키로 3타 몸체10참조를 추가했다. 검기11참조는 공유 raw가 바뀌어도 화면은 동일하다.'
j['latest_proof']='final62_readback_audit.json';j['latest_native']='rin62_components_native_checks.json';j['full_art_unification_complete']=False;j['user_accepted']=False;j['gameplay_runtime_verified']=False
j['full_visual_review']='all_unique_review52/visual_review.json';j['full_visual_review_scope']='52단계436참조/58시트를 실제 열람한 기록이며,62추가분10참조는 normal/black_readback6장으로 따로 확인했다.'
j['next_page']='rear_continuation01/inputs.json';j['next_page_scope']='178/182/186/190 새 원화4키를 정확 동일/반전13참조에 등록할 계획. 현재 입력만 준비했고 생성·패킹되지 않았다.'
(D/'progress_ledger.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
analysis=D/'rear_continuation_analysis/analysis.json';r=json.loads(analysis.read_text('utf8'));r['review_status']='일반00~02/black00~02 및 일반 style_compare를 실제 열람했다. 큰 후두부 흰 면, 단색 등/치마, 뭉뚝한 부츠의 명암을 새174·대기147 수준으로 보완해야 한다.';r['next_authored_keys']=[178,182,186,190];r['exact_alias_expansion_count']=13
analysis.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'count':len(j['new_art_prepared_refs']),'sha':j['current_sha256']}))
