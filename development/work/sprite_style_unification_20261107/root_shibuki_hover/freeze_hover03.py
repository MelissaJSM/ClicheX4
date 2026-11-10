from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];P=D/'packed_hover_candidate03';H=W/'shibuki_audit';Z=W/'zero_audit/shibuki_base_hover10_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def entry(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
want='8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397';assert sha(P/'PL00_U.ARC')==want
assert sha(Z/'READER_LOCK.json')=='59ea0eecace581d3c1551773b346ed356d39a4c7d1ab88bd70bb070e10009a9f'
assert read(Z/'report.json')['passed']and read(D/'native_components03_native_checks.json')['passed']and read(D/'native_cycle01/verification.json')['passed']
repro=read(P/'reproduction_checks.json');assert repro['passed']and repro['total_identical_builds']==3 and len(repro['rejected'])==10
parent=H/'prepared_vehicle_head_base01/FROZEN.json';assert read(parent)['frozen']
lock=D/'hover_input_lock03.json';assert sha(lock)=='f2ff91ce1df30fa39adfae38111cb9afc62623b87056c818b410d293af0db561'
for name,digest in read(lock)['files'].items():assert sha(ROOT/name)==digest,name
paths=[lock,parent,D/'native_components03_native_checks.json',D/'native_cycle01/manifest.json',D/'native_cycle01/verification.json',W/'root_review_checkpoint161.json',W/'root_review_checkpoint162.json',H/'root_hover_visual01/visual_review.json']+[Z/n for n in('report.json','visual_review.json','conclusions.json','READER_LOCK.json')]
report={'passed':True,'candidate_sha256':want,'parent_arc_sha256':'4ceab054c4fa9170a0e785fb00baa01f05afaceb4d2dfc2dcc4e80eab30ee36f','input_files':256,'total_identical_builds':3,'rejected_inputs':10,'evidence':[entry(p)for p in paths],'native_and_independent_passed':True,'root_final_art_reviewed':True,'all_bank_boundaries_preserved':True,'pixel_reduction':False,'runtime_verified':False,'full_style_unification_complete':False,'limits':['조종석 작은머리·기본/포스 호버 실제 게임은 후속이다.','기존16참조는 모든타일 역순열이 같은 저장 전용 변경이며 새 원화 개수로 세지 않는다.','223 신발 국소 등록의 겹침8픽셀,228 총의 얼굴 사각형7셀 겹침은 별도 기록된 한계다.']}
f=P/'final_verification.json';assert not f.exists();f.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
proposal={'project':'ver_buki_riko','files':{'PL00_U.ARC':{'path':(P/'PL00_U.ARC').relative_to(ROOT).as_posix(),'after':want}},'parent':entry(H/'prepared_vehicle_head_base01/PL00_U.ARC'),'selected_refs':list(range(221,231)),'storage_only_refs':read(P/'verification.json')['storage_only_refs'],'runtime_verified':False}
(P/'proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n','utf8')
frozen={'frozen':True,'candidate_sha256':want,'parent_arc_sha256':report['parent_arc_sha256'],'files':{p.name:sha(p)for p in sorted(P.iterdir())if p.is_file()},'source_scripts':{p.relative_to(ROOT).as_posix():sha(p)for p in(D/'pack_hover03.py',D/'verify_hover03.py',D/'freeze_hover03.py')},'native_and_independent_passed':True,'root_final_art_reviewed':True,'gameplay_verified':False,'user_accepted':False,'full_style_unification_complete':False}
(P/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(P/'FROZEN.json'))
