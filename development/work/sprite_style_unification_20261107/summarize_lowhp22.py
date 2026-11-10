from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
e=read(R/'nana_base_lowhp22_approach_watch/evidence.json');trace=read(R/'nana_base_lowhp22_lower.json')
frames=e['verified_bank_frames'];observed=[q['frame']if isinstance(q,dict)else q[-1] for q in frames]
session=ROOT/e['session'];shots=['20261107T171710522899Z.png','20261107T171818972510Z.png','20261107T171852906225Z.png','20261107T171928287572Z.png','20261107T171959786511Z.png','20261107T172201936761Z.png']
p=R/'nana_base_lowhp22_summary.json';assert not p.exists()
r={'disc':e['disc'],'disc_sha256':e['disc_sha256'],'session':e['session'],'target_refs':list(range(120,126)),'target_trigger_verified':False,'new_lowhp_actual_frames_observed':[],'resident_assets':e['resident_assets'],'observer_verified_frames':frames,'root_actually_viewed_screenshots':[bound(session/q)for q in shots],'evidence':[bound(R/'nana_base_lowhp22_approach_watch/evidence.json'),bound(R/'nana_base_lowhp22_lower.json'),bound(R/'lower_hp_rn22.py'),bound(W/'protection_checkpoint34.json')],'hp_trace':[{'seconds':q['seconds'],'hp':q['hp'],'frame':q['frame'],'engine':q['engine']}for q in trace['events']if'hp'in q],'findings':['新規低HPの実機発動は未確認'], 'limits':['체력43→40→37→34→31→28 뒤128 상태와 사망·재등장이 발생했다. 사망 원인은 확정하지 않는다.','보조 스크립트가128을 사망 상태로 중단하지 못해23초 제한까지 계속했다. 아래에 증거를 잠그며 후속 버전은128/최대체력초과/생명전환/체력증가 시 즉시 중단하도록 고친다.','160개 실제 창 캡처 모두를 눈으로 검토한 것은 아니다. 여섯 개 직접 열람 화면과 관측된33개 참조의 RAM/GPU 검증만 주장한다.','120..125 원MIPS·원순서 시뮬레이션·192부분파츠 검증은 별도 근거이며 실제 발동 성공으로 대체하지 않는다.'],'original_save_keys_sent':False,'process_memory_written':False,'session_closed':True,'final_user_accepted':False}
r['findings']=['새 PL00 리소스가 RAM에 정확히 로드됐고 관측된 기본형33개 참조의 디코드/GPU 검사는 통과했다. 새 저체력120..125는 관측하지 못했다.']
assert not set(observed)&set(range(120,126))
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
