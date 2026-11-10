from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/ultimate_special_finish_repaint'
paths=[D/'common_probe_v2/comparison.png',D/'hand98_local_probe_v1/comparison.png']
paths += [D/f'packed_special_candidate_v1/readback_{i}.png'for i in (1,2)]
paths += [D/f'native_cycle_v1/timeline_{aid}.png'for aid in (95,96,97,104,105)]
p=W/'root_review_checkpoint133.json';assert not p.exists()
j={'reviewer':'root','actually_viewed_files':[{'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'actually_viewed':True}for q in paths],'candidate_sha256':'56a3aeb489229d85bb72205bd14f866b4444ff5daa8e1bc7f91c82e9b3c46fc0','findings':['나나 Ultimate95/96/98/99의 새 머릿결·옷 명암과 손 연결 방향을 수용한다.','98 손목 단절 진단은 새 손 원화 국소등록과 고정 총 위치로 해소됐다.','원표95/96/97/104/105 순서 판에서 새4자세 및 기존연결자세 사이 추가 확정 절단·발 위치 급변은 찾지 못했다.'],'runtime_verified':False,'continuous_animation_actually_watched_by_model':False,'independent_audit_pending':True,'whole_project_complete':False}
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(hashlib.sha256(p.read_bytes()).hexdigest())
